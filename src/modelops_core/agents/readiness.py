"""Readiness agentic loop for pilot/demo/release trust gates."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from modelops_core.approval.risk_service import compute_proposal_risk
from modelops_core.config import load_repo_config, resolve_generated_path, resolve_model_path
from modelops_core.gaps.gap_detection import detect_model_gaps
from modelops_core.issue_draft.draft_service import DraftResult, write_draft
from modelops_core.notifications.event_service import emit_notification_event
from modelops_core.notifications.preview_service import preview_notifications
from modelops_core.patching.patch_model import PatchOperation
from modelops_core.patching.patch_proposal_service import build_patch_proposal, write_patch_proposal
from modelops_core.patching.patch_validator import validate_patch_proposal
from modelops_core.reports.index_freshness import check_index_freshness
from modelops_core.reports.ownership_report import generate_ownership_report
from modelops_core.reports.scorecard_service import generate_scorecard
from modelops_core.repository import parse_file, scan_repository
from modelops_core.validation import validate_objects


@dataclass
class ReadinessInput:
    """Input to the ReadinessAgent."""

    repo_root: Path
    profile: str = "pilot"  # demo, pilot, release


@dataclass
class ReadinessBlocker:
    """A single readiness gate failure."""

    gate: str
    severity: str  # high, medium, low
    message: str
    object_id: str | None
    issue_id: str | None = None


@dataclass
class ReadinessResult:
    """Result of running the ReadinessAgent."""

    ready: bool
    profile: str
    gate_count: int
    failed_gates: list[str]
    blockers: list[ReadinessBlocker]
    issues_created: list[str]
    proposal_created: str | None
    draft_issue_path: Path | None
    notification_event_ids: list[str]


class ReadinessAgent:
    """Agent that checks repository readiness and creates review artifacts."""

    _GATES: tuple[str, ...] = (
        "validation_errors",
        "stale_index",
        "scorecard_zero_coverage_pass",
        "scorecard_untitled_repository",
        "missing_validation_coverage",
        "unresolved_high_severity_gaps",
        "invalid_open_proposal",
        "high_risk_unapproved_proposal",
        "active_object_missing_owner",
    )

    # Profile thresholds: coverage is a percentage; max_high_severity_gaps is a count.
    _PROFILE_THRESHOLDS: dict[str, dict[str, float | int]] = {
        "demo": {
            "min_validation_rule_coverage": 0.0,
            "max_high_severity_gaps": 5,
            "max_critical_gaps": 1,
        },
        "pilot": {
            "min_validation_rule_coverage": 40.0,
            "max_high_severity_gaps": 2,
            "max_critical_gaps": 0,
        },
        "release": {
            "min_validation_rule_coverage": 70.0,
            "max_high_severity_gaps": 0,
            "max_critical_gaps": 0,
        },
    }

    def __init__(self, dry_run: bool = False) -> None:
        self.dry_run = dry_run

    def run(self, input_data: ReadinessInput) -> ReadinessResult:
        """Run all readiness gates and emit artifacts for blockers."""
        repo_root = input_data.repo_root.resolve()
        profile = input_data.profile
        model_path = resolve_model_path(repo_root)
        generated_path = resolve_generated_path(repo_root)
        db_path = generated_path / "modelops.db"

        blockers: list[ReadinessBlocker] = []

        # Gate 1: validation errors
        blockers.extend(self._check_validation(model_path))

        # Gate 2: stale index
        blockers.extend(self._check_index_freshness(repo_root))

        # Gate 3-6: scorecard trust issues and coverage gaps
        if db_path.exists():
            blockers.extend(self._check_scorecard(db_path, repo_root))
            blockers.extend(self._check_ownership(db_path))
            blockers.extend(self._check_validation_coverage(db_path, profile))
            blockers.extend(self._check_unresolved_high_severity_gaps(db_path, profile))

        # Gate 7-8: open proposal state
        blockers.extend(self._check_open_proposals(model_path))

        # Deduplicate by (gate, object_id)
        seen: set[tuple[str, str | None]] = set()
        unique_blockers: list[ReadinessBlocker] = []
        for b in blockers:
            key = (b.gate, b.object_id)
            if key in seen:
                continue
            seen.add(key)
            unique_blockers.append(b)
        blockers = unique_blockers

        failed_gates = sorted({b.gate for b in blockers})
        ready = len(failed_gates) == 0

        issues_created: list[str] = []
        proposal_created: str | None = None
        draft_issue_path: Path | None = None
        notification_event_ids: list[str] = []

        if not self.dry_run and blockers:
            issues_created = self._write_issues(blockers, model_path)
            for idx, blocker in enumerate(blockers):
                if blocker.issue_id:
                    blocker.issue_id = issues_created[idx]

            # Build a PatchProposal for deterministic fixes (currently none in blockers,
            # but the structure is here for future gate-specific fixes).
            proposal_ops = self._build_proposal_ops(blockers)
            if proposal_ops:
                proposal_id = self._next_proposal_id(model_path)
                proposal = build_patch_proposal(
                    proposal_id=proposal_id,
                    operations=proposal_ops,
                    affected_objects=[b.object_id for b in blockers if b.object_id],
                    source_evidence="Readiness agent gate run",
                    created_by="system",
                )
                validation_results = validate_patch_proposal(proposal, repo_model_path=model_path)
                proposal["validation_status"] = (
                    "valid"
                    if not any(v.severity == "ERROR" for v in validation_results)
                    else "invalid"
                )
                proposal["validation_results"] = [v.model_dump() for v in validation_results]
                write_patch_proposal(proposal, model_path)
                proposal_created = proposal_id

            draft_issue_path = self._write_draft_issue(blockers, repo_root, generated_path)
            notification_event_ids = self._emit_notifications(
                repo_root, model_path, blockers, proposal_created
            )

        return ReadinessResult(
            ready=ready,
            profile=profile,
            gate_count=len(self._GATES),
            failed_gates=failed_gates,
            blockers=blockers,
            issues_created=issues_created,
            proposal_created=proposal_created,
            draft_issue_path=draft_issue_path,
            notification_event_ids=notification_event_ids,
        )

    def _check_validation(self, model_path: Path) -> list[ReadinessBlocker]:
        """Check for validation errors and high-volume warnings."""
        files = scan_repository(model_path)
        parsed_objects = [parse_file(f) for f in files]
        summary = validate_objects(parsed_objects)

        blockers: list[ReadinessBlocker] = []
        for result in summary.results:
            if result.severity == "ERROR":
                blockers.append(
                    ReadinessBlocker(
                        gate="validation_errors",
                        severity="high",
                        message=f"{result.code}: {result.message}",
                        object_id=result.object_id,
                    )
                )

        # Flag methodology noise: many warnings of the same code
        warning_counts: dict[str, int] = {}
        for result in summary.results:
            if result.severity == "WARNING":
                warning_counts[result.code] = warning_counts.get(result.code, 0) + 1
        for code, count in warning_counts.items():
            if count > 20:
                blockers.append(
                    ReadinessBlocker(
                        gate="validation_warnings_high_volume",
                        severity="low",
                        message=f"{count} warnings with code {code} — consider bulk cleanup.",
                        object_id=None,
                    )
                )

        return blockers

    def _check_index_freshness(self, repo_root: Path) -> list[ReadinessBlocker]:
        """Check whether the generated index is stale."""
        try:
            freshness = check_index_freshness(repo_root)
            if not freshness.fresh:
                return [
                    ReadinessBlocker(
                        gate="stale_index",
                        severity="medium",
                        message=f"Generated index is stale: {freshness.reason}",
                        object_id=None,
                    )
                ]
        except Exception as exc:
            return [
                ReadinessBlocker(
                    gate="stale_index",
                    severity="medium",
                    message=f"Could not determine index freshness: {exc}",
                    object_id=None,
                )
            ]
        return []

    def _check_scorecard(self, db_path: Path, repo_root: Path) -> list[ReadinessBlocker]:
        """Check scorecard for trust-breaking metric logic."""
        blockers: list[ReadinessBlocker] = []
        report = generate_scorecard(db_path, repo_root)

        # Zero-coverage metrics marked as pass
        # Only coverage-style metrics where 0.0 means "nothing covered".
        _COVERAGE_METRICS = {
            "evidence_coverage",
            "sap_table_coverage",
            "ownership_coverage",
            "validation_rule_coverage",
            "lov_coverage",
            "mapping_logic_coverage",
            "dataset_profile_coverage",
            "traceability_coverage",
            "model_completeness",
        }
        for metric in report.metrics:
            if metric.name in _COVERAGE_METRICS and metric.value == 0.0 and metric.status == "pass":
                blockers.append(
                    ReadinessBlocker(
                        gate="scorecard_zero_coverage_pass",
                        severity="high",
                        message=(
                            f"Scorecard metric '{metric.name}' is 0.0 "
                            f"but marked as pass. {metric.explanation}"
                        ),
                        object_id=None,
                    )
                )

        # Repository name fallback
        config = load_repo_config(repo_root)
        config_name = config.name if config else None
        if config_name and report.repo_name == "Untitled Repository":
            blockers.append(
                ReadinessBlocker(
                    gate="scorecard_untitled_repository",
                    severity="medium",
                    message=(
                        f"Scorecard shows 'Untitled Repository' despite config name "
                        f"'{config_name}'."
                    ),
                    object_id=None,
                )
            )

        return blockers

    def _check_ownership(self, db_path: Path) -> list[ReadinessBlocker]:
        """Check for active objects missing owners."""
        report = generate_ownership_report(db_path, Path())
        return [
            ReadinessBlocker(
                gate="active_object_missing_owner",
                severity="medium",
                message=f"Active {orphan.object_type} '{orphan.object_id}' has no owner.",
                object_id=orphan.object_id,
            )
            for orphan in report.orphaned_objects
        ]

    def _check_validation_coverage(self, db_path: Path, profile: str) -> list[ReadinessBlocker]:
        """Check that validation-rule coverage meets the profile threshold."""
        thresholds = self._PROFILE_THRESHOLDS.get(profile, self._PROFILE_THRESHOLDS["pilot"])
        min_coverage = thresholds.get("min_validation_rule_coverage", 40.0)

        report = generate_scorecard(db_path, db_path.parent.parent)
        for metric in report.metrics:
            if metric.name == "validation_rule_coverage":
                if metric.value < min_coverage:
                    return [
                        ReadinessBlocker(
                            gate="missing_validation_coverage",
                            severity="medium",
                            message=(
                                f"Validation rule coverage is {metric.value}%, "
                                f"below {profile} threshold of {min_coverage}%. "
                                f"{metric.explanation}"
                            ),
                            object_id=None,
                        )
                    ]
                return []
        return []

    def _check_unresolved_high_severity_gaps(
        self, db_path: Path, profile: str
    ) -> list[ReadinessBlocker]:
        """Check for unresolved high-severity model gaps beyond profile tolerance."""
        thresholds = self._PROFILE_THRESHOLDS.get(profile, self._PROFILE_THRESHOLDS["pilot"])
        max_high = int(thresholds.get("max_high_severity_gaps", 2))
        max_critical = int(thresholds.get("max_critical_gaps", 0))

        gaps = detect_model_gaps(db_path)
        high = [g for g in gaps if g.severity == "high"]
        critical = [g for g in gaps if g.severity == "critical"]

        blockers: list[ReadinessBlocker] = []
        if len(critical) > max_critical:
            sample = ", ".join(sorted({g.column_name for g in critical[:3]})) or "model"
            blockers.append(
                ReadinessBlocker(
                    gate="unresolved_high_severity_gaps",
                    severity="high",
                    message=(
                        f"{len(critical)} critical model gap(s) exceed {profile} threshold "
                        f"of {max_critical}; sample: {sample}."
                    ),
                    object_id=None,
                )
            )
        if len(high) > max_high:
            sample = ", ".join(sorted({g.column_name for g in high[:3]})) or "model"
            blockers.append(
                ReadinessBlocker(
                    gate="unresolved_high_severity_gaps",
                    severity="high",
                    message=(
                        f"{len(high)} high-severity model gap(s) exceed {profile} threshold "
                        f"of {max_high}; sample: {sample}."
                    ),
                    object_id=None,
                )
            )
        return blockers

    def _check_open_proposals(self, model_path: Path) -> list[ReadinessBlocker]:
        """Check open PatchProposals for invalid or high-risk state."""
        blockers: list[ReadinessBlocker] = []
        proposals_dir = model_path / "patch-proposals"
        if not proposals_dir.exists():
            return blockers

        for proposal_path in proposals_dir.glob("*.md"):
            parsed = parse_file(proposal_path)
            fm = parsed.frontmatter or {}
            if fm.get("status") != "pending_review":
                continue

            proposal_id = str(fm.get("id", proposal_path.stem))
            operations = fm.get("operations", []) or []
            validation_status = fm.get("validation_status")

            if validation_status == "invalid":
                blockers.append(
                    ReadinessBlocker(
                        gate="invalid_open_proposal",
                        severity="high",
                        message=f"Open proposal {proposal_id} is invalid.",
                        object_id=proposal_id,
                    )
                )

            risk = compute_proposal_risk(operations, model_path)
            if risk.risk_level == "high":
                blockers.append(
                    ReadinessBlocker(
                        gate="high_risk_unapproved_proposal",
                        severity="high",
                        message=(
                            f"Open proposal {proposal_id} is high-risk: "
                            f"{', '.join(risk.risk_reasons)}"
                        ),
                        object_id=proposal_id,
                    )
                )

        return blockers

    def _build_proposal_ops(self, blockers: list[ReadinessBlocker]) -> list[PatchOperation]:
        """Build deterministic patch operations for blockers that can be auto-fixed."""
        # Currently no model-level fixes are safe to apply automatically.
        # This hook is for future gates like "missing description" with a generated value.
        return []

    def _write_issues(self, blockers: list[ReadinessBlocker], model_path: Path) -> list[str]:
        """Write Issue canonical files for readiness blockers."""
        issues_dir = model_path / "issues"
        if not self.dry_run:
            issues_dir.mkdir(parents=True, exist_ok=True)

        issue_ids: list[str] = []
        timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")

        for idx, blocker in enumerate(blockers, start=1):
            issue_id = f"ISS-READINESS-{timestamp}-{idx:03d}"
            issue_ids.append(issue_id)
            if self.dry_run:
                continue

            frontmatter: dict[str, Any] = {
                "id": issue_id,
                "type": "Issue",
                "status": "open",
                "name": f"Readiness blocker: {blocker.gate}",
                "issue_type": "readiness_blocker",
                "severity": blocker.severity,
                "gate": blocker.gate,
                "affected_object": blocker.object_id,
            }
            body = f"# {blocker.gate}\n\n{blocker.message}\n\n"
            body += "**Profile:** readiness check\n"
            if blocker.object_id:
                body += f"**Affected object:** `{blocker.object_id}`\n"

            import yaml

            yaml_text = yaml.safe_dump(
                frontmatter, default_flow_style=False, sort_keys=False, allow_unicode=True
            )
            content = f"---\n{yaml_text}---\n\n{body}\n"
            (issues_dir / f"{issue_id}.md").write_text(content, encoding="utf-8")

        return issue_ids

    def _write_draft_issue(
        self,
        blockers: list[ReadinessBlocker],
        repo_root: Path,
        generated_path: Path,
    ) -> Path | None:
        """Generate a GitHub-ready issue draft summarizing blockers."""
        if not blockers:
            return None

        title = f"[Readiness] {len(blockers)} blocker(s) for pilot"
        lines: list[str] = []
        lines.append("## Goal")
        lines.append("Address readiness blockers before pilot/demo.")
        lines.append("")
        lines.append("### Blockers")
        for blocker in blockers:
            obj = f" (`{blocker.object_id}`)" if blocker.object_id else ""
            lines.append(f"- **{blocker.gate}**{obj} — {blocker.message}")
        lines.append("")
        lines.append("### Suggested Next Actions")
        lines.append("1. Review each blocker above.")
        lines.append("2. Create PatchProposals or assign owners as needed.")
        lines.append("3. Re-run `martenweave agent readiness --repo .`.")
        lines.append("")
        generated_at = datetime.now(UTC).isoformat()
        lines.append(f"---\n*Generated by martenweave readiness agent at {generated_at}*")

        draft = DraftResult(
            title=title,
            body="\n".join(lines),
            source_type="readiness",
            labels=["readiness", "pilot-blocker"],
        )
        return write_draft(repo_root, draft)

    def _emit_notifications(
        self,
        repo_root: Path,
        model_path: Path,
        blockers: list[ReadinessBlocker],
        proposal_id: str | None,
    ) -> list[str]:
        """Emit notification events for affected owners."""
        event_ids: list[str] = []
        affected_objects = [b.object_id for b in blockers if b.object_id]

        try:
            recipients = preview_notifications(
                model_path=model_path,
                proposal_id=proposal_id,
            )
        except Exception:
            recipients = []

        for entry in recipients:
            try:
                event = emit_notification_event(
                    repo_root=repo_root,
                    event_type="readiness_blocker_detected",
                    source_type="ReadinessAgent",
                    source_id="readiness-agent",
                    recipient_id=entry.recipient_id,
                    recipient_role=entry.recipient_role,
                    reason=f"Readiness agent found {len(blockers)} blocker(s).",
                    affected_objects=affected_objects,
                    message_summary=f"{len(blockers)} readiness blocker(s) require review.",
                )
                event_ids.append(event.event_id)
            except Exception:
                continue

        return event_ids

    def _next_proposal_id(self, model_path: Path) -> str:
        """Generate the next readiness PatchProposal ID."""
        proposals_dir = model_path / "patch-proposals"
        existing: list[int] = []
        if proposals_dir.exists():
            for path in proposals_dir.glob("PP-READINESS-*.md"):
                suffix = path.stem.replace("PP-READINESS-", "")
                if suffix.isdigit():
                    existing.append(int(suffix))
        next_num = max(existing, default=0) + 1
        return f"PP-READINESS-{next_num:04d}"
