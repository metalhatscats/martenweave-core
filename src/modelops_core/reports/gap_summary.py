"""Consolidated gap summary report combining all model gap sources."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from modelops_core.gaps.gap_detection import detect_model_gaps
from modelops_core.reports.analysis_service import generate_analysis_report
from modelops_core.reports.health_report import generate_repository_health
from modelops_core.reports.scorecard_service import generate_scorecard


@dataclass
class GapTypeSummary:
    """Summary for a single gap type."""

    count: int = 0
    sample_object_ids: list[str] = field(default_factory=list)


@dataclass
class GapSummaryReport:
    """Consolidated gap summary across all gap sources."""

    gaps_by_type: dict[str, GapTypeSummary] = field(default_factory=dict)
    total_gap_count: int = 0
    gap_score: float = 0.0
    top_objects: list[str] = field(default_factory=list)
    total_objects: int = 0
    sources_checked: list[str] = field(default_factory=list)


def _collect_validation_gaps(db_path: Path) -> list[dict[str, Any]]:
    """Query validation_results table for ERROR/WARNING items."""
    gaps: list[dict[str, Any]] = []
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            "SELECT severity, code, message, object_id, object_type "
            "FROM validation_results WHERE severity IN ('ERROR', 'WARNING')"
        ).fetchall()
        for severity, code, message, object_id, object_type in rows:
            gaps.append(
                {
                    "object_id": object_id or "",
                    "object_type": object_type or "",
                    "gap_type": f"validation_{code.lower()}",
                    "severity": severity,
                    "message": message,
                }
            )
    finally:
        conn.close()
    return gaps


def _add_gaps(
    report: GapSummaryReport,
    gaps: list[dict[str, Any]],
    gap_type_key: str | None = None,
) -> None:
    """Add gap dicts to the report, grouping by gap_type."""
    object_gap_types: dict[str, set[str]] = {}
    for g in gaps:
        key = gap_type_key or g.get("gap_type", "unknown")
        obj_id = g.get("object_id", "")
        if not obj_id:
            continue

        if key not in report.gaps_by_type:
            report.gaps_by_type[key] = GapTypeSummary()
        if obj_id not in report.gaps_by_type[key].sample_object_ids:
            report.gaps_by_type[key].sample_object_ids.append(obj_id)
            report.gaps_by_type[key].count += 1

        if obj_id not in object_gap_types:
            object_gap_types[obj_id] = set()
        object_gap_types[obj_id].add(key)

    report.total_gap_count = sum(summary.count for summary in report.gaps_by_type.values())

    # top_objects = objects with the most gap types
    sorted_objs = sorted(
        object_gap_types.items(),
        key=lambda x: (-len(x[1]), x[0]),
    )
    report.top_objects = [obj_id for obj_id, _ in sorted_objs[:10]]


def generate_gap_summary_report(
    db_path: Path,
    repo_root: Path,
) -> GapSummaryReport:
    """Generate a consolidated gap summary report.

    Composes model gaps, analysis gaps, health coverage gaps, scorecard gaps,
    and validation results into a unified view.
    """
    report = GapSummaryReport()
    sources_checked: list[str] = []

    # Total objects
    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute("SELECT COUNT(*) FROM objects").fetchone()
        report.total_objects = row[0] if row else 0
    finally:
        conn.close()

    # 1. Model gaps (detect_model_gaps)
    if db_path.exists():
        model_gaps = detect_model_gaps(db_path)
        _add_gaps(
            report,
            [
                {
                    "object_id": g.column_name,
                    "gap_type": g.gap_code,
                }
                for g in model_gaps
            ],
        )
        sources_checked.append("model_gaps")

    # 2. Analysis report gaps
    if db_path.exists():
        analysis = generate_analysis_report(db_path, repo_root)

        # Orphan fields
        orphan = analysis.orphan_fields
        if orphan:
            _add_gaps(
                report,
                [
                    {
                        "object_id": f["object_id"],
                        "gap_type": "orphan_field",
                    }
                    for f in orphan.field_endpoints_without_attribute
                ],
            )

        # Attributes without fields
        attr_cov = analysis.attribute_coverage
        if attr_cov:
            _add_gaps(
                report,
                [
                    {
                        "object_id": f["object_id"],
                        "gap_type": "attribute_without_field",
                    }
                    for f in attr_cov.attributes_without_fields
                ],
            )

        # Ownership gaps
        if analysis.ownership_gaps:
            _add_gaps(report, analysis.ownership_gaps)

        # Validation coverage
        if analysis.validation_coverage:
            _add_gaps(report, analysis.validation_coverage)

        # LoV coverage
        if analysis.lov_coverage:
            _add_gaps(report, analysis.lov_coverage)

        # Mapping coverage
        if analysis.mapping_coverage:
            _add_gaps(report, analysis.mapping_coverage)

        # Risk report (open issues/risks)
        risk = analysis.risk_report
        if risk:
            _add_gaps(
                report,
                [{"object_id": i["object_id"], "gap_type": "open_issue"} for i in risk.open_issues],
            )
            _add_gaps(
                report,
                [{"object_id": r["object_id"], "gap_type": "open_risk"} for r in risk.open_risks],
            )

        sources_checked.append("analysis_report")

    # 3. Health report coverage gaps
    if db_path.exists():
        health = generate_repository_health(db_path)
        if health.coverage_gaps_list:
            _add_gaps(
                report,
                [
                    {
                        "object_id": g.object_id,
                        "gap_type": g.gap_type,
                    }
                    for g in health.coverage_gaps_list
                ],
            )
        sources_checked.append("health_report")

    # 4. Scorecard gaps
    if db_path.exists():
        scorecard = generate_scorecard(db_path, repo_root)
        if scorecard.gaps:
            _add_gaps(
                report,
                [
                    {
                        "object_id": g.object_id or "",
                        "gap_type": g.gap_type,
                    }
                    for g in scorecard.gaps
                ],
            )
        sources_checked.append("scorecard")

    # 5. Validation results from SQLite
    if db_path.exists():
        val_gaps = _collect_validation_gaps(db_path)
        _add_gaps(report, val_gaps)
        sources_checked.append("validation_results")

    report.sources_checked = sources_checked

    # Gap score = total gaps / total objects (capped at 1.0)
    if report.total_objects > 0:
        report.gap_score = round(min(report.total_gap_count / report.total_objects, 1.0), 3)
    else:
        report.gap_score = 0.0

    # Deterministic sorting
    report.gaps_by_type = dict(
        sorted(report.gaps_by_type.items(), key=lambda x: (-x[1].count, x[0]))
    )
    for summary in report.gaps_by_type.values():
        summary.sample_object_ids = sorted(summary.sample_object_ids)[:5]

    return report
