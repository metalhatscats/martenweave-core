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
    profile_xlsx,
)
from modelops_core.imports.privacy import (
    DatasetPrivacyPolicy,
    apply_privacy_to_profile,
    apply_privacy_to_workbook,
    detect_high_risk_columns,
)
from modelops_core.index import build_index as _build_index
from modelops_core.reports.gap_summary import generate_gap_summary_report
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


def _profile_dataset(
    dataset_path: Path, repo_root: Path
) -> tuple[DatasetProfile | WorkbookProfile, list[str]]:
    """Profile a CSV/XLSX dataset and apply privacy controls."""
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


def _gap_to_dict(gap: ColumnGap) -> dict[str, Any]:
    return {
        "column_name": gap.column_name,
        "gap_code": gap.gap_code,
        "severity": gap.severity,
        "message": gap.message,
        "sheet_name": gap.sheet_name,
        "evidence_ids": gap.evidence_ids,
        "recommended_proposal_op": gap.recommended_proposal_op,
    }


def _match_to_dict(match: ColumnMatch) -> dict[str, Any]:
    return {
        "column_name": match.column_name,
        "matched_endpoint_id": match.matched_endpoint_id,
        "match_type": match.match_type,
        "sheet_name": match.sheet_name,
    }


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
) -> DatasetReadinessReport:
    """Generate a consolidated dataset readiness report.

    The workflow is:
      1. Validate canonical model files.
      2. Build the SQLite index (even if validation has errors, so the report
         can surface those errors instead of failing opaquely).
      3. Profile the dataset.
      4. Detect dataset-to-model gaps.
      5. Detect optional model-side gaps.
      6. Generate a consolidated gap summary.
      7. Compute a readiness verdict.
      8. Optionally promote dataset gaps to a draft PatchProposal.

    Args:
        repo_root: Path to the canonical model repository.
        dataset_path: Path to the CSV or XLSX dataset file.
        check_model: If True, also include model-side gaps in the report.
        dry_run: If True, do not persist any generated artifacts.
        promote_to_proposal: If True, create a draft PatchProposal from dataset
            gaps in ``model/patch-proposals/``. Ignored when ``dry_run`` is True.

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
            )

    return _build_report(
        repo_root,
        dataset_path,
        summary,
        db_path,
        check_model,
        dry_run=dry_run,
        promote_to_proposal=promote_to_proposal,
    )


def _build_report(
    repo_root: Path,
    dataset_path: Path,
    summary: ValidationSummary,
    db_path: Path,
    check_model: bool,
    dry_run: bool,
    promote_to_proposal: bool,
) -> DatasetReadinessReport:
    """Assemble the readiness report from already-built inputs."""
    profile, privacy_warnings = _profile_dataset(dataset_path, repo_root)
    matches, dataset_gaps, model_gaps, coverage, promotion_report = _detect_gaps(
        profile, db_path, check_model
    )
    gap_summary_report = generate_gap_summary_report(db_path, repo_root)
    verdict = _compute_verdict(summary, coverage, dataset_gaps, model_gaps)

    promoted_proposal_path: str | None = None
    if promote_to_proposal and not dry_run and promotion_report.gaps:
        proposal_path = promote_gaps_to_proposal(
            promotion_report, resolve_model_path(repo_root)
        )
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

    return DatasetReadinessReport(
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
        dataset_gaps=[_gap_to_dict(g) for g in dataset_gaps],
        model_gaps=[_gap_to_dict(g) for g in model_gaps],
        gap_summary={
            "total_gap_count": gap_summary_report.total_gap_count,
            "gap_score": gap_summary_report.gap_score,
            "total_objects": gap_summary_report.total_objects,
            "sources_checked": gap_summary_report.sources_checked,
            "gaps_by_type": {
                key: {
                    "count": type_summary.count,
                    "sample_object_ids": type_summary.sample_object_ids,
                }
                for key, type_summary in gap_summary_report.gaps_by_type.items()
            },
        },
        verdict=verdict,
        dry_run=dry_run,
        promoted_proposal_path=promoted_proposal_path,
    )


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


def _render_markdown(report: DatasetReadinessReport) -> str:
    """Render a human-readable Markdown readiness report."""
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
    ]

    if report.promoted_proposal_path:
        lines.append(f"**Promoted to proposal:** `{report.promoted_proposal_path}`")
        lines.append("")

    lines.extend(
        [
            "## Validation Summary",
            "",
            f"- Errors: {report.validation['error_count']}",
            f"- Warnings: {report.validation['warning_count']}",
            f"- Info: {report.validation['info_count']}",
            f"- Valid: {report.validation['is_valid']}",
            "",
            "## Dataset Profile",
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
        lines.append("**Privacy warnings:** " + ", ".join(profile["privacy_warnings"]))

    lines.extend(
        [
            "",
            "## Coverage",
            "",
            f"- Total columns: {report.coverage.get('total_columns', '—')}",
            f"- Matched columns: {report.coverage.get('matched_columns', '—')}",
            f"- Unmatched columns: {report.coverage.get('unmatched_columns', '—')}",
            f"- Duplicate columns: {report.coverage.get('duplicate_columns', '—')}",
            f"- Match rate: {report.coverage.get('match_rate', '—')}",
            "",
            "## Gaps",
            "",
        ]
    )

    if report.dataset_gaps:
        lines.append("### Dataset-to-model gaps")
        lines.append("")
        for gap in report.dataset_gaps:
            lines.append(
                f"- **{gap['column_name']}** — "
                f"`{gap['gap_code']}` ({gap['severity']}): {gap['message']}"
            )
        lines.append("")

    if report.model_gaps:
        lines.append("### Model-side gaps")
        lines.append("")
        for gap in report.model_gaps:
            lines.append(
                f"- **{gap['column_name']}** — "
                f"`{gap['gap_code']}` ({gap['severity']}): {gap['message']}"
            )
        lines.append("")

    if not report.dataset_gaps and not report.model_gaps:
        lines.append("No gaps detected.")
        lines.append("")

    lines.extend(
        [
            "## Gap Summary",
            "",
            f"- Total gap count: {report.gap_summary['total_gap_count']}",
            f"- Gap score: {report.gap_summary['gap_score']}",
            f"- Total objects: {report.gap_summary['total_objects']}",
            f"- Sources checked: {', '.join(report.gap_summary['sources_checked']) or '—'}",
            "",
        ]
    )

    if report.gap_summary["gaps_by_type"]:
        lines.append("### Gaps by type")
        lines.append("")
        for gap_type, summary in report.gap_summary["gaps_by_type"].items():
            samples = ", ".join(summary["sample_object_ids"][:5]) or "—"
            lines.append(f"- **{gap_type}**: {summary['count']} (samples: {samples})")
        lines.append("")

    return "\n".join(lines)
