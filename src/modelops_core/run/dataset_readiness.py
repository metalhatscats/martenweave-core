"""Dataset readiness workflow orchestration.

Turns a raw dataset and a canonical model repository into a single shareable
readiness report by orchestrating validation, indexing, profiling, and gap
detection services that already exist in the core.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from modelops_core import __version__
from modelops_core.assessment.finding_contract import AssessmentFinding, FindingProvenance
from modelops_core.config import (
    load_repo_config,
    load_resource_limits,
    resolve_generated_path,
    resolve_model_path,
)
from modelops_core.gaps.gap_detection import (
    ColumnGap,
    ColumnMatch,
    DatasetCoverageMetrics,
    DatasetGapReport,
    detect_dataset_gaps,
    detect_model_gaps,
    promote_gaps_to_proposal,
)
from modelops_core.imports.dataset_profiler import (
    DatasetProfile,
    WorkbookProfile,
    profile_csv,
    profile_json,
    profile_xlsx,
    profile_xml,
)
from modelops_core.imports.privacy import (
    DatasetPrivacyPolicy,
    apply_privacy_to_profile,
    apply_privacy_to_workbook,
    detect_high_risk_columns,
)
from modelops_core.index import build_index as _build_index
from modelops_core.issue_draft.draft_service import (
    create_draft_from_readiness,
)
from modelops_core.issue_draft.draft_service import (
    write_draft as _write_issue_draft,
)
from modelops_core.repository import parse_file, scan_repository
from modelops_core.validation import validate_objects
from modelops_core.validation.result import ValidationSummary


@dataclass
class DatasetReadinessReport:
    """Consolidated readiness verdict for a dataset against a canonical model."""

    martenweave_version: str
    repo: str
    dataset: str
    timestamp: str
    validation: dict[str, Any]
    dataset_profile: dict[str, Any]
    coverage: dict[str, Any]
    matches: list[dict[str, Any]]
    dataset_gaps: list[dict[str, Any]]
    model_gaps: list[dict[str, Any]]
    gap_summary: dict[str, Any]
    verdict: str
    dry_run: bool = False
    promoted_proposal_path: str | None = None
    issue_draft_path: str | None = None


def _profile_dataset(
    dataset_path: Path, repo_root: Path
) -> tuple[DatasetProfile | WorkbookProfile, list[str]]:
    """Profile a supported local dataset and apply privacy controls."""
    limits = load_resource_limits(repo_root)
    dataset_id = dataset_path.stem
    suffix = dataset_path.suffix.lower()

    if suffix == ".csv":
        raw_profile = profile_csv(
            dataset_path,
            dataset_id=dataset_id,
            max_file_size=limits.max_file_size_bytes,
            max_rows=limits.max_profile_rows,
            max_columns=limits.max_profile_columns,
            sample_interval=limits.profile_sample_interval,
        )
    elif suffix in {".xlsx", ".xls"}:
        raw_profile = profile_xlsx(
            dataset_path,
            dataset_id=dataset_id,
            max_file_size=limits.max_file_size_bytes,
            max_rows=limits.max_profile_rows,
            max_columns=limits.max_profile_columns,
            sample_interval=limits.profile_sample_interval,
        )
    elif suffix == ".json":
        raw_profile = profile_json(
            dataset_path,
            dataset_id=dataset_id,
            max_file_size=limits.max_file_size_bytes,
            max_rows=limits.max_profile_rows,
            max_columns=limits.max_profile_columns,
        )
    elif suffix == ".xml":
        raw_profile = profile_xml(
            dataset_path,
            dataset_id=dataset_id,
            max_file_size=limits.max_file_size_bytes,
            max_rows=limits.max_profile_rows,
            max_columns=limits.max_profile_columns,
        )
    else:
        raise ValueError(f"Unsupported dataset format: {suffix}")

    policy = DatasetPrivacyPolicy(include_raw_samples=False)
    if isinstance(raw_profile, WorkbookProfile):
        profile = apply_privacy_to_workbook(raw_profile, policy)
        high_risk_cols: list[str] = []
        for sheet in profile.sheets:
            high_risk_cols.extend(detect_high_risk_columns(sheet))
    else:
        profile = apply_privacy_to_profile(raw_profile, policy)
        high_risk_cols = detect_high_risk_columns(profile)

    return profile, sorted(set(high_risk_cols))


def _detect_gaps(
    profile: DatasetProfile | WorkbookProfile,
    db_path: Path,
    check_model: bool,
) -> tuple[list[ColumnMatch], list[ColumnGap], list[ColumnGap], DatasetCoverageMetrics | None]:
    """Match dataset columns to FieldEndpoints and optionally detect model-side gaps."""
    sheet_reports: list[DatasetGapReport] = []
    if isinstance(profile, WorkbookProfile):
        for sheet in profile.sheets:
            sheet_report = detect_dataset_gaps(sheet, db_path)
            for match in sheet_report.matches:
                match.sheet_name = sheet.sheet_name
            for gap in sheet_report.gaps:
                gap.sheet_name = sheet.sheet_name
            sheet_reports.append(sheet_report)
    else:
        sheet_reports.append(detect_dataset_gaps(profile, db_path))

    all_matches: list[ColumnMatch] = []
    all_dataset_gaps: list[ColumnGap] = []
    total_columns = 0
    matched_columns = 0
    unmatched_columns = 0
    duplicate_columns = 0
    coverage: DatasetCoverageMetrics | None = None

    for sheet_report in sheet_reports:
        all_matches.extend(sheet_report.matches)
        all_dataset_gaps.extend(sheet_report.gaps)
        if sheet_report.coverage:
            total_columns += sheet_report.coverage.total_columns
            matched_columns += sheet_report.coverage.matched_columns
            unmatched_columns += sheet_report.coverage.unmatched_columns
            duplicate_columns += sheet_report.coverage.duplicate_columns

    if total_columns > 0:
        match_rate = round(matched_columns / total_columns, 4)
        coverage = DatasetCoverageMetrics(
            total_columns=total_columns,
            matched_columns=matched_columns,
            unmatched_columns=unmatched_columns,
            duplicate_columns=duplicate_columns,
            match_rate=match_rate,
        )

    model_gaps: list[ColumnGap] = []
    if check_model:
        model_gaps = detect_model_gaps(db_path)

    promotion_report = DatasetGapReport(
        dataset_id=profile.dataset_id,
        matches=all_matches,
        gaps=all_dataset_gaps,
        coverage=coverage,
    )

    return all_matches, all_dataset_gaps, model_gaps, coverage, promotion_report


def _compute_verdict(
    summary: ValidationSummary,
    coverage: DatasetCoverageMetrics | None,
    dataset_gaps: list[ColumnGap],
    model_gaps: list[ColumnGap],
) -> str:
    """Compute a readiness verdict from validation, coverage, and gaps."""
    if summary.error_count > 0:
        return "blocked"
    if coverage is None or coverage.match_rate == 0.0:
        return "blocked"
    if summary.warning_count > 0 or dataset_gaps or model_gaps:
        return "ready_with_warnings"
    return "ready"


def _readiness_impact_for_gap(gap_code: str, severity: str) -> str:
    """Map gap code and severity to a readiness impact label."""
    if severity in ("high", "critical") or gap_code == "MODEL_ATTRIBUTE_MISSING_SOURCE":
        return "blocking"
    if severity == "medium":
        return "ready_with_warnings"
    return "informational"


def _recommended_action_for_gap(gap: ColumnGap) -> str:
    """Return a deterministic recommended action for a dataset/model gap."""
    if gap.recommended_proposal_op:
        op = gap.recommended_proposal_op
        return f"{op['op']} {op['object_type']} {op['object_id']}: {op['reason']}"
    actions: dict[str, str] = {
        "UNMODELED_DATASET_COLUMN": (
            "Create a FieldEndpoint and link it to the matching attribute."
        ),
        "DATASET_COLUMN_MULTIPLE_MATCHES": (
            "Resolve the ambiguous column-to-endpoint match and update the mapping."
        ),
        "MODEL_ATTRIBUTE_MISSING_SOURCE": (
            "Add a source FieldEndpoint or Mapping for the unattributed attribute."
        ),
        "MISSING_OWNER": "Assign a business_owner or technical_owner to the object.",
        "DUPLICATE_COLUMN_NAME": (
            "Deduplicate the source column or map it to a single canonical representation."
        ),
        "EMPTY_DATASET": (
            "Provide a non-empty dataset or exclude the source from readiness checks."
        ),
        "NO_MATCHING_ENDPOINTS": (
            "Model the dataset columns as FieldEndpoints or update the source profile."
        ),
    }
    return actions.get(gap.gap_code, "Review the gap and record a decision or proposal.")


def _gap_to_dict(gap: ColumnGap, readiness_run_id: str) -> dict[str, Any]:
    data = {
        "column_name": gap.column_name,
        "gap_code": gap.gap_code,
        "severity": gap.severity,
        "message": gap.message,
        "sheet_name": gap.sheet_name,
        "evidence_ids": gap.evidence_ids,
        "recommended_proposal_op": gap.recommended_proposal_op,
    }
    finding_id = gap.gap_id or f"GAP-{gap.gap_code}-{gap.column_name}"
    source_kind = "model_validation" if finding_id.startswith("GAP-MODEL-") else "dataset_readiness"
    severity = gap.severity if gap.severity in {"low", "medium", "high", "critical"} else "medium"
    affected_objects = [gap.column_name] if gap.column_name else []
    if finding_id.startswith("GAP-MODEL-") and gap.column_name:
        affected_objects = [gap.column_name]
    data["finding"] = AssessmentFinding(
        id=finding_id,
        category=gap.gap_code.lower(),
        severity=severity,
        message=gap.message,
        status="open",
        lifecycle_state="open",
        provenance=FindingProvenance(
            assessment_run_id=readiness_run_id,
            source_kind=source_kind,
            detection_mode="deterministic",
            rule_id=f"gap:{gap.gap_code}",
            location={"sheet_name": gap.sheet_name, "column_name": gap.column_name},
            evidence_refs=["readiness.json", "dataset_profile.json"],
            affected_objects=affected_objects,
        ),
        rule_id=f"gap:{gap.gap_code}",
        evidence_refs=["readiness.json", "dataset_profile.json"],
        affected_objects=affected_objects,
        recommended_action=_recommended_action_for_gap(gap),
        readiness_impact=_readiness_impact_for_gap(gap.gap_code, severity),
    ).model_dump(mode="json")
    return data


def _match_to_dict(match: ColumnMatch) -> dict[str, Any]:
    return {
        "column_name": match.column_name,
        "matched_endpoint_id": match.matched_endpoint_id,
        "match_type": match.match_type,
        "sheet_name": match.sheet_name,
    }


def _build_finding_summary(
    dataset_gaps: list[dict[str, Any]],
    model_gaps: list[dict[str, Any]],
    coverage: DatasetCoverageMetrics | None,
    check_model: bool,
) -> dict[str, Any]:
    """Summarize this run's own findings.

    The readiness report is a decision artifact for one dataset assessment run,
    so its gap summary is scoped to the findings persisted in the same report —
    not to repo-wide gap sources. This keeps the manifest, JSON, Markdown, API,
    and Workbench views counting the same findings.
    """
    findings = dataset_gaps + model_gaps
    gaps_by_type: dict[str, dict[str, Any]] = {}
    for gap in findings:
        entry = gaps_by_type.setdefault(gap["gap_code"], {"count": 0, "sample_finding_ids": []})
        entry["count"] += 1
        finding_id = gap["finding"]["id"]
        if finding_id not in entry["sample_finding_ids"]:
            entry["sample_finding_ids"].append(finding_id)
    for entry in gaps_by_type.values():
        entry["sample_finding_ids"] = sorted(entry["sample_finding_ids"])[:5]
    gaps_by_type = dict(sorted(gaps_by_type.items(), key=lambda item: (-item[1]["count"], item[0])))

    total_columns = coverage.total_columns if coverage else 0
    total = len(findings)
    # Gap score = findings per assessed dataset column, capped at 1.0.
    if total_columns > 0:
        gap_score = round(min(total / total_columns, 1.0), 3)
    else:
        gap_score = 1.0 if total else 0.0

    sources_checked = ["dataset_gaps"] + (["model_gaps"] if check_model else [])
    return {
        "total_gap_count": total,
        "dataset_gap_count": len(dataset_gaps),
        "model_gap_count": len(model_gaps),
        "gap_score": gap_score,
        "total_columns": total_columns,
        "sources_checked": sources_checked,
        "gaps_by_type": gaps_by_type,
    }


def _recommended_next_action(report: DatasetReadinessReport) -> str:
    """Return the single next safe review action for the report verdict."""
    error_count = report.validation["error_count"]
    if error_count:
        return (
            f"Resolve the {error_count} validation error(s) in the canonical model, then re-run "
            "`martenweave run dataset-readiness`. No changes are applied automatically."
        )
    findings = report.dataset_gaps + report.model_gaps
    if report.verdict == "blocked":
        if findings:
            top = next(
                (g for g in findings if g["finding"]["readiness_impact"] == "blocking"),
                findings[0],
            )
            return (
                f"Review finding `{top['finding']['id']}` ({top['column_name']}): "
                f"{top['finding']['recommended_action']} "
                "Then re-run readiness; draft proposals require human approval before "
                "anything is applied."
            )
        return (
            "Provide a dataset whose columns match canonical FieldEndpoints, or model the "
            "dataset columns through a reviewed PatchProposal."
        )
    if report.verdict == "ready_with_warnings":
        return (
            f"Review the {len(findings)} open finding(s) above and record a decision or draft "
            "PatchProposal for each before relying on this dataset."
        )
    total_columns = report.coverage.get("total_columns", 0)
    return (
        f"No action required: all {total_columns} dataset column(s) matched canonical "
        "FieldEndpoints and validation reported no errors or warnings."
    )


def _build_dataset_profile_dict(
    profile: DatasetProfile | WorkbookProfile,
    dataset_path: Path,
    privacy_warnings: list[str],
) -> dict[str, Any]:
    base: dict[str, Any] = {
        "dataset_id": profile.dataset_id,
        "file_path": str(dataset_path),
        "file_hash": profile.file_hash,
        "privacy_warnings": privacy_warnings,
    }

    if isinstance(profile, WorkbookProfile):
        base["type"] = "workbook"
        base["sheets"] = [
            {
                "sheet_name": sheet.sheet_name,
                "row_count": sheet.row_count,
                "column_count": sheet.column_count,
            }
            for sheet in profile.sheets
        ]
    else:
        base["type"] = "dataset"
        base["row_count"] = profile.row_count
        base["column_count"] = profile.column_count
        base["columns"] = [
            {
                "name": col.name,
                "position": col.position,
                "inferred_type": col.inferred_type,
                "blank_count": col.blank_count,
                "non_blank_count": col.non_blank_count,
                "distinct_count": col.distinct_count,
            }
            for col in profile.columns
        ]

    return base


def generate_dataset_readiness_report(
    repo_root: Path,
    dataset_path: Path,
    check_model: bool = False,
    dry_run: bool = False,
    promote_to_proposal: bool = False,
    issue_draft: bool = False,
) -> DatasetReadinessReport:
    """Generate a consolidated dataset readiness report.

    The workflow is:
      1. Validate canonical model files.
      2. Build the SQLite index (even if validation has errors, so the report
         can surface those errors instead of failing opaquely).
      3. Profile the dataset.
      4. Detect dataset-to-model gaps.
      5. Detect optional model-side gaps.
      6. Summarize this run's findings (scoped to the report itself).
      7. Compute a readiness verdict.
      8. Optionally promote dataset gaps to a draft PatchProposal.
      9. Optionally generate a GitHub-ready issue draft.

    Args:
        repo_root: Path to the canonical model repository.
        dataset_path: Path to the CSV or XLSX dataset file.
        check_model: If True, also include model-side gaps in the report.
        dry_run: If True, do not persist any generated artifacts.
        promote_to_proposal: If True, create a draft PatchProposal from dataset
            gaps in ``model/patch-proposals/``. Ignored when ``dry_run`` is True.
        issue_draft: If True, create a GitHub-ready issue draft in
            ``generated/issues/``. Ignored when ``dry_run`` is True.

    Returns:
        A ``DatasetReadinessReport`` dataclass with the full results.

    Raises:
        ValueError: If the model path or dataset file does not exist, or if the
            dataset format is unsupported.
    """
    model_path = resolve_model_path(repo_root)
    if not model_path.exists():
        raise ValueError(f"Model path does not exist: {model_path}")
    if not dataset_path.exists():
        raise ValueError(f"Dataset not found: {dataset_path}")

    files = scan_repository(model_path)
    parsed_objects = [parse_file(f) for f in files]
    config = load_repo_config(repo_root)
    enabled_packs = config.enabled_domain_packs if config else None
    summary = validate_objects(parsed_objects, enabled_packs)

    db_path = resolve_generated_path(repo_root) / "modelops.db"
    if not dry_run:
        _build_index(
            repo_root,
            db_path=db_path,
            allow_invalid=True,
            export_jsonl=False,
        )
    elif not db_path.exists():
        # Dry-run still needs a temporary index to query gaps. Build it in a
        # temp location and discard it after the report is generated.
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmp:
            temp_db = Path(tmp) / "modelops.db"
            _build_index(
                repo_root,
                db_path=temp_db,
                allow_invalid=True,
                export_jsonl=False,
            )
            return _build_report(
                repo_root,
                dataset_path,
                summary,
                temp_db,
                check_model,
                dry_run=True,
                promote_to_proposal=False,
                issue_draft=False,
            )

    return _build_report(
        repo_root,
        dataset_path,
        summary,
        db_path,
        check_model,
        dry_run=dry_run,
        promote_to_proposal=promote_to_proposal,
        issue_draft=issue_draft,
    )


def _build_report(
    repo_root: Path,
    dataset_path: Path,
    summary: ValidationSummary,
    db_path: Path,
    check_model: bool,
    dry_run: bool,
    promote_to_proposal: bool,
    issue_draft: bool,
) -> DatasetReadinessReport:
    """Assemble the readiness report from already-built inputs."""
    profile, privacy_warnings = _profile_dataset(dataset_path, repo_root)
    matches, dataset_gaps, model_gaps, coverage, promotion_report = _detect_gaps(
        profile, db_path, check_model
    )
    verdict = _compute_verdict(summary, coverage, dataset_gaps, model_gaps)

    promoted_proposal_path: str | None = None
    if promote_to_proposal and not dry_run and promotion_report.gaps:
        proposal_path = promote_gaps_to_proposal(promotion_report, resolve_model_path(repo_root))
        promoted_proposal_path = str(proposal_path)

    coverage_dict: dict[str, Any] = {}
    if coverage:
        coverage_dict = {
            "total_columns": coverage.total_columns,
            "matched_columns": coverage.matched_columns,
            "unmatched_columns": coverage.unmatched_columns,
            "duplicate_columns": coverage.duplicate_columns,
            "match_rate": coverage.match_rate,
        }

    readiness_run_id = f"READINESS-{dataset_path.stem.upper()}"
    dataset_gap_dicts = [_gap_to_dict(g, readiness_run_id) for g in dataset_gaps]
    model_gap_dicts = [_gap_to_dict(g, readiness_run_id) for g in model_gaps]
    report = DatasetReadinessReport(
        martenweave_version=__version__,
        repo=str(repo_root),
        dataset=str(dataset_path),
        timestamp=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        validation={
            "is_valid": summary.is_valid,
            "error_count": summary.error_count,
            "warning_count": summary.warning_count,
            "info_count": summary.info_count,
            "summary_by_code": summary.summary_by_code,
        },
        dataset_profile=_build_dataset_profile_dict(profile, dataset_path, privacy_warnings),
        coverage=coverage_dict,
        matches=[_match_to_dict(m) for m in matches],
        dataset_gaps=dataset_gap_dicts,
        model_gaps=model_gap_dicts,
        gap_summary=_build_finding_summary(
            dataset_gap_dicts, model_gap_dicts, coverage, check_model
        ),
        verdict=verdict,
        dry_run=dry_run,
        promoted_proposal_path=promoted_proposal_path,
    )

    if issue_draft and not dry_run:
        draft = create_draft_from_readiness(report.__dict__)
        draft_path = _write_issue_draft(repo_root, draft)
        report.issue_draft_path = str(draft_path)

    return report


def write_readiness_report(
    report: DatasetReadinessReport,
    out_dir: Path,
) -> tuple[Path, Path]:
    """Write the readiness report as JSON and Markdown files.

    Returns the paths to the written JSON and Markdown files.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "readiness.json"
    md_path = out_dir / "readiness.md"

    json_path.write_text(
        json.dumps(report.__dict__, indent=2, default=str, sort_keys=True),
        encoding="utf-8",
    )
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    return json_path, md_path


def _render_finding_lines(lines: list[str], gaps: list[dict[str, Any]]) -> None:
    """Render findings with stable IDs, evidence links, and recommended actions."""
    for gap in gaps:
        finding = gap["finding"]
        lines.append(
            f"- **{gap['column_name'] or '(dataset)'}** — "
            f"`{gap['gap_code']}` ({gap['severity']}): {gap['message']}"
        )
        lines.append(f"  - Finding ID: `{finding['id']}`")
        evidence = ", ".join(f"`{ref}`" for ref in finding["evidence_refs"]) or "—"
        lines.append(f"  - Evidence: {evidence}")
        lines.append(f"  - Recommended action: {finding['recommended_action']}")


def _render_markdown(report: DatasetReadinessReport) -> str:
    """Render a human-readable, decision-ready Markdown readiness report."""
    summary = report.gap_summary
    dataset_name = Path(report.dataset).name
    lines: list[str] = [
        "# Dataset Readiness Report",
        "",
        f"**Repository:** `{report.repo}`",
        f"**Dataset:** `{report.dataset}`",
        f"**Generated:** {report.timestamp}",
        f"**Martenweave version:** {report.martenweave_version}",
        "",
        f"## Verdict: {report.verdict}",
        "",
        f"**Scope:** dataset `{dataset_name}` assessed against the canonical model in "
        f"`{report.repo}`.",
        f"**Findings:** {summary['total_gap_count']} total — "
        f"{summary['dataset_gap_count']} dataset-to-model, "
        f"{summary['model_gap_count']} model-side.",
        f"**Recommended next action:** {_recommended_next_action(report)}",
        "",
    ]

    lines.extend(
        [
            "## Facts (deterministic)",
            "",
            "### Validation Summary",
            "",
            f"- Errors: {report.validation['error_count']}",
            f"- Warnings: {report.validation['warning_count']}",
            f"- Info: {report.validation['info_count']}",
            f"- Valid: {report.validation['is_valid']}",
            "",
            "### Dataset Profile",
            "",
        ]
    )

    profile = report.dataset_profile
    if profile.get("type") == "workbook":
        lines.append(f"Type: workbook ({len(profile['sheets'])} sheets)")
        for sheet in profile["sheets"]:
            lines.append(
                f"- {sheet['sheet_name']}: {sheet['row_count']} rows, "
                f"{sheet['column_count']} columns"
            )
    else:
        lines.append("Type: dataset")
        lines.append(f"- Rows: {profile.get('row_count', '—')}")
        lines.append(f"- Columns: {profile.get('column_count', '—')}")

    if profile.get("privacy_warnings"):
        lines.append("")
        lines.append(
            "**Privacy warnings (high-risk columns, samples redacted):** "
            + ", ".join(f"`{name}`" for name in profile["privacy_warnings"])
        )

    lines.extend(
        [
            "",
            "### Coverage",
            "",
            f"- Total columns: {report.coverage.get('total_columns', '—')}",
            f"- Matched columns: {report.coverage.get('matched_columns', '—')}",
            f"- Unmatched columns: {report.coverage.get('unmatched_columns', '—')}",
            f"- Duplicate columns: {report.coverage.get('duplicate_columns', '—')}",
            f"- Match rate: {report.coverage.get('match_rate', '—')}",
            "",
            "### Findings",
            "",
        ]
    )

    if report.dataset_gaps:
        lines.append("#### Dataset-to-model gaps")
        lines.append("")
        _render_finding_lines(lines, report.dataset_gaps)
        lines.append("")

    if report.model_gaps:
        lines.append("#### Model-side gaps")
        lines.append("")
        _render_finding_lines(lines, report.model_gaps)
        lines.append("")

    if not report.dataset_gaps and not report.model_gaps:
        lines.append("No gaps detected.")
        lines.append("")

    lines.extend(
        [
            "### Gap Summary",
            "",
            "Counts below summarize exactly the findings persisted in this report.",
            "",
            f"- Total gap count: {summary['total_gap_count']}",
            f"- Dataset-to-model gaps: {summary['dataset_gap_count']}",
            f"- Model-side gaps: {summary['model_gap_count']}",
            f"- Gap score: {summary['gap_score']}",
            f"- Dataset columns assessed: {summary['total_columns']}",
            f"- Sources checked: {', '.join(summary['sources_checked']) or '—'}",
            "",
        ]
    )

    if summary["gaps_by_type"]:
        lines.append("#### Gaps by type")
        lines.append("")
        for gap_type, type_summary in summary["gaps_by_type"].items():
            samples = ", ".join(f"`{fid}`" for fid in type_summary["sample_finding_ids"]) or "—"
            lines.append(f"- **{gap_type}**: {type_summary['count']} (findings: {samples})")
        lines.append("")

    lines.extend(
        [
            "## Assumptions and privacy boundaries",
            "",
            "- Raw dataset sample values are excluded from this report; high-risk column "
            "samples are redacted.",
            "- Invalid values are not assessed without governed value lists.",
            "- This report never modifies canonical model files.",
            "",
            "## AI suggestions",
            "",
            "None. No AI provider is configured or required; every finding in this report "
            "is produced deterministically.",
            "",
            "## Human review and dispositions",
            "",
        ]
    )

    if report.promoted_proposal_path:
        lines.append(
            f"- Draft PatchProposal: `{report.promoted_proposal_path}` — pending human "
            "review; nothing is applied automatically."
        )
    if report.issue_draft_path:
        lines.append(f"- Issue draft: `{report.issue_draft_path}`")
    if not report.promoted_proposal_path and not report.issue_draft_path:
        lines.append("- No draft proposals or issue drafts were created for this run.")
    lines.append("- No human dispositions are recorded in this report; all findings are open.")
    lines.append("")

    return "\n".join(lines)
