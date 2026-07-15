"""One-page executive migration readiness summary.

Consumes a migration-assessment output directory and produces a concise,
stakeholder-facing readiness verdict with blocking findings, required decisions,
and recommended next actions. Every reported fact cites a stable source
artifact or finding ID.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from modelops_core.config import load_repo_config
from modelops_core.index import build_index
from modelops_core.pilot.review import load_findings, load_reviews
from modelops_core.reports.analysis_service import generate_analysis_report
from modelops_core.reports.decisions_report import generate_decisions_report
from modelops_core.reports.gap_summary import generate_gap_summary_report
from modelops_core.reports.scorecard_service import generate_scorecard


@dataclass
class ExecutiveSummary:
    """Compact, deterministic executive readiness summary."""

    repo_name: str
    generated_at: str
    readiness_verdict: str
    scope: str
    key_metrics: dict[str, Any] = field(default_factory=dict)
    blocking_findings: list[dict[str, Any]] = field(default_factory=list)
    required_decisions: list[dict[str, Any]] = field(default_factory=list)
    unmapped_fields: list[dict[str, Any]] = field(default_factory=list)
    validation_coverage_gaps: list[dict[str, Any]] = field(default_factory=list)
    accepted_risks: list[dict[str, Any]] = field(default_factory=list)
    top_blockers: list[dict[str, Any]] = field(default_factory=list)
    recommended_next_action: str = ""
    unavailable_metrics: list[str] = field(default_factory=list)
    source_artifacts: dict[str, str | None] = field(default_factory=dict)


def _assessment_dir_from_manifest(manifest_path: Path) -> Path:
    return manifest_path.resolve().parent


def _load_manifest(manifest_path: Path) -> dict[str, Any]:
    if not manifest_path.exists():
        raise FileNotFoundError(f"Assessment manifest not found: {manifest_path}")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def _repo_root_from_manifest(manifest: dict[str, Any]) -> Path:
    repo_path = manifest.get("repo_path") or manifest.get("inputs", {}).get("repo")
    if not repo_path:
        raise ValueError("Manifest does not contain a repository path")
    return Path(repo_path).resolve()


def _ensure_index(repo_root: Path) -> Path:
    db_path = repo_root / "generated" / "modelops.db"
    if not db_path.exists():
        build_index(repo_root)
    return db_path


def _severity_rank(severity: str) -> int:
    return {"high": 0, "medium": 1, "low": 2}.get(severity.lower(), 3)


def _classify_verdict(
    high_confirmed: int,
    medium_confirmed: int,
    scorecard_fails: int,
    unresolved_decisions: int,
    open_issues: int,
) -> str:
    """Return a deterministic readiness verdict based on explicit gates."""
    if high_confirmed > 0 or scorecard_fails > 2 or unresolved_decisions > 3:
        return "blocked"
    if medium_confirmed > 0 or scorecard_fails > 0 or open_issues > 0:
        return "at_risk"
    if high_confirmed == 0 and medium_confirmed == 0 and scorecard_fails == 0:
        return "ready"
    return "review"


def generate_executive_summary(manifest_path: Path) -> ExecutiveSummary:
    """Generate a one-page executive summary from an assessment manifest.

    Args:
        manifest_path: Path to ``manifest.json`` from a migration assessment run.

    Returns:
        ``ExecutiveSummary`` with deterministic verdict, blockers, and next action.
    """
    manifest = _load_manifest(manifest_path)
    assessment_dir = _assessment_dir_from_manifest(manifest_path)
    repo_root = _repo_root_from_manifest(manifest)

    config = load_repo_config(repo_root)
    repo_name = config.name if config else manifest.get("repo_name", repo_root.name)

    # Source artifact paths
    source_artifacts: dict[str, str | None] = {
        "manifest": str(manifest_path.resolve()),
        "findings": None,
        "reviews": None,
        "scorecard": None,
        "gap_report": None,
    }
    for artifact in manifest.get("generated_artifacts", []):
        path = artifact.get("path", "")
        if path.endswith("01_readiness_scorecard.md"):
            source_artifacts["scorecard"] = str(assessment_dir / path)
        elif path.endswith("02_gap_report.md"):
            source_artifacts["gap_report"] = str(assessment_dir / path)

    # Findings and reviews
    findings_data: dict[str, Any] = {"findings": []}
    reviews_data: dict[str, Any] = {"reviews": {}, "history": []}
    findings_path = assessment_dir / "findings.json"
    if findings_path.exists():
        findings_data = load_findings(assessment_dir)
        source_artifacts["findings"] = str(findings_path.resolve())
    reviews_path = assessment_dir / "finding-reviews.json"
    if reviews_path.exists():
        reviews_data = load_reviews(assessment_dir)
        source_artifacts["reviews"] = str(reviews_path.resolve())

    confirmed_ids = {
        fid
        for fid, rec in reviews_data.get("reviews", {}).items()
        if rec.get("disposition") == "confirmed"
    }
    accepted_risk_ids = {
        fid
        for fid, rec in reviews_data.get("reviews", {}).items()
        if rec.get("disposition") == "accepted_risk"
    }

    # Model-side reports
    db_path = _ensure_index(repo_root)
    scorecard = generate_scorecard(db_path, repo_root)
    gap_summary = generate_gap_summary_report(db_path, repo_root)
    analysis = generate_analysis_report(db_path, repo_root)
    decisions_report = generate_decisions_report(db_path, repo_root)

    # Confirmed findings from mapping profile
    blocking_findings: list[dict[str, Any]] = []
    for finding in findings_data.get("findings", []):
        fid = finding.get("id", "")
        if fid in confirmed_ids:
            provenance = finding.get("provenance", {})
            blocking_findings.append(
                {
                    "id": fid,
                    "category": finding.get("category", "unknown"),
                    "severity": finding.get("severity", "medium"),
                    "message": finding.get("message", ""),
                    "source": finding.get("source", "mapping_profile"),
                    "readiness_impact": finding.get("readiness_impact", "informational"),
                    "detection_mode": provenance.get("detection_mode", "deterministic"),
                    "rule_id": provenance.get("rule_id", ""),
                }
            )
    blocking_findings.sort(key=lambda x: (_severity_rank(x["severity"]), x["id"]))

    high_confirmed = sum(1 for f in blocking_findings if f["severity"] == "high")
    medium_confirmed = sum(1 for f in blocking_findings if f["severity"] == "medium")

    # Accepted risks
    accepted_risks: list[dict[str, Any]] = []
    for finding in findings_data.get("findings", []):
        fid = finding.get("id", "")
        if fid in accepted_risk_ids:
            accepted_risks.append(
                {
                    "id": fid,
                    "category": finding.get("category", "unknown"),
                    "severity": finding.get("severity", "medium"),
                    "message": finding.get("message", ""),
                }
            )

    # Required decisions: unresolved decisions from mapping + uncovered canonical decisions
    required_decisions: list[dict[str, Any]] = []
    for finding in findings_data.get("findings", []):
        category = finding.get("category", "")
        if category in {"unresolved_decision", "conflicting_decision"}:
            required_decisions.append(
                {
                    "id": finding.get("id", ""),
                    "type": "mapping_decision",
                    "topic": finding.get("location", {}).get("topic", ""),
                    "severity": finding.get("severity", "medium"),
                    "source": "mapping_profile",
                    "source_finding_id": finding.get("id", ""),
                }
            )
    for decision in decisions_report.uncovered_decisions[:10]:
        required_decisions.append(
            {
                "id": decision.object_id,
                "type": "canonical_decision",
                "topic": decision.object_name or decision.object_id,
                "severity": "medium",
                "source": "model_decision",
                "source_object_id": decision.object_id,
            }
        )
    required_decisions.sort(key=lambda x: (_severity_rank(x["severity"]), x["id"]))

    # Unmapped fields: missing_mapping findings from mapping profile + orphan fields from model
    unmapped_fields: list[dict[str, Any]] = []
    for finding in findings_data.get("findings", []):
        if finding.get("category") == "missing_mapping":
            loc = finding.get("location", {})
            unmapped_fields.append(
                {
                    "id": finding.get("id", ""),
                    "source_field": loc.get("source_field", ""),
                    "source_system": loc.get("source_system", ""),
                    "source_table": loc.get("source_table", ""),
                    "severity": finding.get("severity", "high"),
                    "source": "mapping_profile",
                    "source_finding_id": finding.get("id", ""),
                }
            )
    if analysis.orphan_fields:
        for orphan in analysis.orphan_fields.field_endpoints_without_attribute[:10]:
            unmapped_fields.append(
                {
                    "id": orphan.get("object_id", ""),
                    "source_field": orphan.get("object_name", orphan.get("object_id", "")),
                    "source_system": "",
                    "source_table": "",
                    "severity": "high",
                    "source": "model_analysis",
                    "source_object_id": orphan.get("object_id", ""),
                }
            )

    # Validation coverage gaps
    validation_coverage_gaps: list[dict[str, Any]] = []
    for finding in findings_data.get("findings", []):
        if finding.get("category") == "validation_coverage_gap":
            loc = finding.get("location", {})
            validation_coverage_gaps.append(
                {
                    "id": finding.get("id", ""),
                    "source_field": loc.get("source_field", ""),
                    "condition": loc.get("condition", ""),
                    "severity": finding.get("severity", "medium"),
                    "source": "mapping_profile",
                    "source_finding_id": finding.get("id", ""),
                }
            )
    if analysis.validation_coverage:
        for gap in analysis.validation_coverage[:10]:
            validation_coverage_gaps.append(
                {
                    "id": gap.get("object_id", ""),
                    "source_field": gap.get("object_name", gap.get("object_id", "")),
                    "condition": "Missing validation rule",
                    "severity": "medium",
                    "source": "model_analysis",
                    "source_object_id": gap.get("object_id", ""),
                }
            )

    # Scorecard metrics summary
    scorecard_fails = sum(1 for m in scorecard.metrics if m.status == "fail")
    scorecard_warnings = sum(1 for m in scorecard.metrics if m.status == "warning")
    failed_metrics = [m.name for m in scorecard.metrics if m.status == "fail"]

    open_issues = analysis.risk_report.issue_count if analysis.risk_report else 0
    unresolved_decisions = len(required_decisions)

    verdict = _classify_verdict(
        high_confirmed=high_confirmed,
        medium_confirmed=medium_confirmed,
        scorecard_fails=scorecard_fails,
        unresolved_decisions=unresolved_decisions,
        open_issues=open_issues,
    )

    # Top blockers: confirmed high-severity findings + scorecard failures + open issues
    top_blockers: list[dict[str, Any]] = []
    for finding in blocking_findings[:5]:
        top_blockers.append(
            {
                "description": finding["message"],
                "severity": finding["severity"],
                "source": "finding",
                "source_id": finding["id"],
            }
        )
    for metric in scorecard.metrics:
        if metric.status == "fail" and metric.suggested_action:
            top_blockers.append(
                {
                    "description": f"{metric.name}: {metric.explanation}",
                    "severity": "high",
                    "source": "scorecard",
                    "source_id": metric.name,
                    "suggested_action": metric.suggested_action,
                }
            )
    if open_issues > 0:
        top_blockers.append(
            {
                "description": f"{open_issues} open issue(s) in the model",
                "severity": "high",
                "source": "model_analysis",
                "source_id": "open_issues",
            }
        )
    top_blockers = top_blockers[:5]

    # Recommended next action
    if verdict == "blocked":
        recommended_next_action = (
            f"Resolve the {high_confirmed} high-severity confirmed finding(s) and "
            f"{scorecard_fails} failed scorecard metric(s) before proceeding."
        )
    elif verdict == "at_risk":
        recommended_next_action = (
            f"Address {medium_confirmed} medium-severity confirmed finding(s) and "
            f"record decisions for {unresolved_decisions} open decision(s)."
        )
    elif verdict == "ready":
        recommended_next_action = (
            "No blocking findings. Proceed to stakeholder sign-off and migration planning."
        )
    else:
        recommended_next_action = (
            "Complete the review of remaining findings and validate accepted risks."
        )

    # Key metrics
    key_metrics = {
        "readiness_level": scorecard.readiness_level,
        "object_count": scorecard.object_count,
        "gap_score": gap_summary.gap_score,
        "total_findings": len(findings_data.get("findings", [])),
        "confirmed_findings": len(blocking_findings),
        "accepted_risks": len(accepted_risks),
        "unresolved_decisions": unresolved_decisions,
        "unmapped_fields": len(unmapped_fields),
        "validation_coverage_gaps": len(validation_coverage_gaps),
        "open_issues": open_issues,
        "scorecard_fails": scorecard_fails,
        "scorecard_warnings": scorecard_warnings,
        "failed_metrics": failed_metrics,
    }

    # Unavailable metrics: manual baselines not captured in this assessment
    unavailable_metrics: list[str] = []
    if not manifest.get("inputs", {}).get("dataset"):
        unavailable_metrics.append("Dataset readiness profile (no dataset provided)")
    if not manifest.get("inputs", {}).get("evidence"):
        unavailable_metrics.append("Evidence notes (no evidence files provided)")

    return ExecutiveSummary(
        repo_name=repo_name,
        generated_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        readiness_verdict=verdict,
        scope=manifest.get("repo_path", str(repo_root)),
        key_metrics=key_metrics,
        blocking_findings=blocking_findings,
        required_decisions=required_decisions,
        unmapped_fields=unmapped_fields,
        validation_coverage_gaps=validation_coverage_gaps,
        accepted_risks=accepted_risks,
        top_blockers=top_blockers,
        recommended_next_action=recommended_next_action,
        unavailable_metrics=unavailable_metrics,
        source_artifacts=source_artifacts,
    )


def executive_summary_to_dict(summary: ExecutiveSummary) -> dict[str, Any]:
    """Convert an ``ExecutiveSummary`` to a JSON-serializable dict."""
    return {
        "repo_name": summary.repo_name,
        "generated_at": summary.generated_at,
        "readiness_verdict": summary.readiness_verdict,
        "scope": summary.scope,
        "key_metrics": summary.key_metrics,
        "blocking_findings": summary.blocking_findings,
        "required_decisions": summary.required_decisions,
        "unmapped_fields": summary.unmapped_fields,
        "validation_coverage_gaps": summary.validation_coverage_gaps,
        "accepted_risks": summary.accepted_risks,
        "top_blockers": summary.top_blockers,
        "recommended_next_action": summary.recommended_next_action,
        "unavailable_metrics": summary.unavailable_metrics,
        "source_artifacts": summary.source_artifacts,
    }


def render_executive_summary_markdown(summary: ExecutiveSummary) -> str:
    """Render a one-page executive summary as Markdown."""
    lines: list[str] = [
        "# Executive Migration Readiness Summary",
        "",
        f"**Repository**: {summary.repo_name}",
        f"**Generated**: {summary.generated_at}",
        f"**Readiness Verdict**: {summary.readiness_verdict.upper()}",
        "",
        "## Scope",
        "",
        f"{summary.scope}",
        "",
        "## Key Metrics",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Readiness level | {summary.key_metrics.get('readiness_level', '—')} |",
        f"| Objects | {summary.key_metrics.get('object_count', '—')} |",
        f"| Gap score | {summary.key_metrics.get('gap_score', '—')} |",
        f"| Total findings | {summary.key_metrics.get('total_findings', '—')} |",
        f"| Confirmed findings | {summary.key_metrics.get('confirmed_findings', '—')} |",
        f"| Accepted risks | {summary.key_metrics.get('accepted_risks', '—')} |",
        f"| Unresolved decisions | {summary.key_metrics.get('unresolved_decisions', '—')} |",
        f"| Unmapped fields | {summary.key_metrics.get('unmapped_fields', '—')} |",
        (f"| Validation gaps | {summary.key_metrics.get('validation_coverage_gaps', '—')} |"),
        f"| Open issues | {summary.key_metrics.get('open_issues', '—')} |",
        f"| Scorecard fails | {summary.key_metrics.get('scorecard_fails', '—')} |",
        "",
    ]

    if summary.top_blockers:
        lines.extend(["## Top Blockers", ""])
        for idx, blocker in enumerate(summary.top_blockers, start=1):
            severity = blocker.get("severity", "medium")
            source = blocker.get("source", "")
            source_id = blocker.get("source_id", "")
            lines.append(
                f"{idx}. **{severity.upper()}** — {blocker['description']} "
                f"_(source: {source} `{source_id}`)_"
            )
        lines.append("")

    if summary.blocking_findings:
        lines.extend(["## Blocking Findings (Confirmed)", ""])
        for finding in summary.blocking_findings[:10]:
            lines.append(
                f"- **{finding['severity'].upper()}** `{finding['id']}` — {finding['message']}"
            )
        if len(summary.blocking_findings) > 10:
            lines.append(f"- ... and {len(summary.blocking_findings) - 10} more")
        lines.append("")

    if summary.required_decisions:
        lines.extend(["## Required Business Decisions", ""])
        for decision in summary.required_decisions[:10]:
            lines.append(
                f"- `{decision['id']}` — {decision['topic']} _(source: {decision['source']})_"
            )
        if len(summary.required_decisions) > 10:
            lines.append(f"- ... and {len(summary.required_decisions) - 10} more")
        lines.append("")

    if summary.unmapped_fields:
        lines.extend(["## Unmapped Fields", ""])
        for field in summary.unmapped_fields[:10]:
            src = field.get("source_field", "")
            system = field.get("source_system", "")
            table = field.get("source_table", "")
            loc = f"{system}/{table}/{src}".strip("/")
            lines.append(f"- `{field['id']}` — {loc} _(source: {field['source']})_")
        if len(summary.unmapped_fields) > 10:
            lines.append(f"- ... and {len(summary.unmapped_fields) - 10} more")
        lines.append("")

    if summary.validation_coverage_gaps:
        lines.extend(["## Validation Coverage Gaps", ""])
        for gap in summary.validation_coverage_gaps[:10]:
            lines.append(
                f"- `{gap['id']}` — {gap.get('source_field', '')}: {gap.get('condition', '')}"
            )
        if len(summary.validation_coverage_gaps) > 10:
            lines.append(f"- ... and {len(summary.validation_coverage_gaps) - 10} more")
        lines.append("")

    if summary.accepted_risks:
        lines.extend(["## Accepted Risks", ""])
        for risk in summary.accepted_risks[:10]:
            lines.append(f"- **{risk['severity'].upper()}** `{risk['id']}` — {risk['message']}")
        if len(summary.accepted_risks) > 10:
            lines.append(f"- ... and {len(summary.accepted_risks) - 10} more")
        lines.append("")

    if summary.unavailable_metrics:
        lines.extend(["## Unavailable Metrics", ""])
        for metric in summary.unavailable_metrics:
            lines.append(f"- {metric}")
        lines.append("")

    lines.extend(
        [
            "## Recommended Next Action",
            "",
            summary.recommended_next_action,
            "",
            "## Source Artifacts",
            "",
        ]
    )
    for name, path in sorted(summary.source_artifacts.items()):
        if path:
            lines.append(f"- **{name}**: `{path}`")
    lines.append("")

    return "\n".join(lines)


def write_executive_summary(
    summary: ExecutiveSummary,
    out_path: Path,
) -> None:
    """Write both Markdown and JSON executive summary outputs.

    Args:
        summary: The executive summary to write.
        out_path: Output file path. ``.md`` and ``.json`` siblings are written.
    """
    out_path = out_path.resolve()
    if out_path.is_dir() or out_path.suffix == "":
        out_path.mkdir(parents=True, exist_ok=True)
        md_path = out_path / "executive-summary.md"
        json_path = out_path / "executive-summary.json"
    else:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        md_path = out_path.with_suffix(".md")
        json_path = out_path.with_suffix(".json")

    md_path.write_text(render_executive_summary_markdown(summary), encoding="utf-8")
    json_path.write_text(
        json.dumps(
            executive_summary_to_dict(summary),
            indent=2,
            default=str,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
