"""Deterministic Migration Model Readiness Assessment package generator.

Composes existing Martenweave services into a client-reviewable output folder.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from modelops_core.config import load_repo_config
from modelops_core.exports.export_service import export_model_xlsx
from modelops_core.impact.impact_report import render_impact_report_markdown
from modelops_core.impact.impact_service import generate_impact_report
from modelops_core.index import build_index
from modelops_core.reports.analysis_service import generate_analysis_report
from modelops_core.reports.gap_summary import generate_gap_summary_report
from modelops_core.reports.health_report import generate_repository_health
from modelops_core.reports.scorecard_service import generate_scorecard


@dataclass
class AssessmentArtifact:
    """A single file produced by the assessment."""

    path: Path
    description: str


@dataclass
class AssessmentPackage:
    """Metadata for a generated assessment output package."""

    repo_name: str
    generated_at: str
    readiness_level: str
    object_count: int
    gap_score: float
    high_risk_count: int
    artifacts: list[AssessmentArtifact] = field(default_factory=list)


@dataclass
class _RiskItem:
    object_id: str
    object_name: str | None
    object_type: str | None
    severity: str  # high, medium, low
    reasons: list[str] = field(default_factory=list)


def _ensure_index(repo_root: Path) -> Path:
    """Build index if missing; return db path."""
    db_path = repo_root / "generated" / "modelops.db"
    if not db_path.exists():
        build_index(repo_root)
    return db_path


def _collect_validation_errors(db_path: Path) -> list[dict[str, Any]]:
    """Query validation_results table for ERROR items."""
    gaps: list[dict[str, Any]] = []
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            "SELECT severity, code, message, object_id, object_type "
            "FROM validation_results WHERE severity = 'ERROR'"
        ).fetchall()
        for severity, code, message, object_id, object_type in rows:
            gaps.append(
                {
                    "object_id": object_id or "",
                    "object_type": object_type or "",
                    "code": code,
                    "message": message,
                    "severity": severity,
                }
            )
    finally:
        conn.close()
    return gaps


def _build_high_risk_items(
    analysis: Any,
    validation_errors: list[dict[str, Any]],
) -> list[_RiskItem]:
    """Aggregate risk signals from analysis and validation into ranked items."""
    risks: dict[str, _RiskItem] = {}

    def _ensure(obj_id: str, name: str | None, obj_type: str | None) -> _RiskItem:
        if obj_id not in risks:
            risks[obj_id] = _RiskItem(
                object_id=obj_id,
                object_name=name or obj_id,
                object_type=obj_type,
                severity="medium",
                reasons=[],
            )
        return risks[obj_id]

    # Orphan fields
    if analysis.orphan_fields:
        for f in analysis.orphan_fields.field_endpoints_without_attribute:
            item = _ensure(f["object_id"], f.get("object_name"), "FieldEndpoint")
            item.reasons.append("Orphan field: no linked business attribute")
            item.severity = "high"

    # Attributes without fields
    if analysis.attribute_coverage:
        for f in analysis.attribute_coverage.attributes_without_fields:
            item = _ensure(f["object_id"], f.get("object_name"), "Attribute")
            item.reasons.append("No physical field representation")
            item.severity = max(item.severity, "medium")

    # Ownership gaps
    for g in analysis.ownership_gaps:
        item = _ensure(g["object_id"], g.get("object_name"), g.get("object_type"))
        item.reasons.append("Missing owner")
        item.severity = max(item.severity, "medium")

    # Missing validation rules
    for g in analysis.validation_coverage:
        item = _ensure(g["object_id"], g.get("object_name"), "Attribute")
        item.reasons.append("Missing validation rule")

    # Missing LoV
    for g in analysis.lov_coverage:
        item = _ensure(g["object_id"], g.get("object_name"), "FieldEndpoint")
        item.reasons.append("Missing value list")

    # Missing value mapping
    for g in analysis.mapping_coverage:
        item = _ensure(g["object_id"], g.get("object_name"), "Mapping")
        item.reasons.append("Missing value mapping")

    # Open issues
    if analysis.risk_report:
        for i in analysis.risk_report.open_issues:
            item = _ensure(i["object_id"], i.get("object_name"), "Issue")
            item.reasons.append(f"Open issue (status: {i.get('status', 'unknown')})")
            item.severity = "high"
        for r in analysis.risk_report.open_risks:
            item = _ensure(r["object_id"], r.get("object_name"), "Risk")
            item.reasons.append(f"Open risk (status: {r.get('status', 'unknown')})")
            item.severity = "high"

    # Validation errors
    for e in validation_errors:
        obj_id = e["object_id"]
        if not obj_id:
            continue
        item = _ensure(obj_id, None, e.get("object_type"))
        item.reasons.append(f"Validation error ({e['code']}): {e['message']}")
        item.severity = "high"

    # Deduplicate reasons and sort
    for item in risks.values():
        item.reasons = sorted(set(item.reasons))

    # Sort: high first, then by reason count descending, then id
    severity_order = {"high": 0, "medium": 1, "low": 2}
    return sorted(
        risks.values(),
        key=lambda x: (severity_order.get(x.severity, 3), -len(x.reasons), x.object_id),
    )


def _render_scorecard_md(scorecard: Any, repo_name: str, generated_at: str) -> str:
    lines: list[str] = [
        "# Migration Model Readiness Scorecard",
        "",
        f"**Repository**: {repo_name}",
        f"**Generated**: {generated_at}",
        f"**Readiness Level**: {scorecard.readiness_level}",
        f"**Total Objects**: {scorecard.object_count}",
        "",
        "## Metrics",
        "",
        "| Metric | Value | Target | Status | Explanation |",
        "|--------|-------|--------|--------|-------------|",
    ]
    for m in scorecard.metrics:
        status_emoji = {"pass": "✅", "warning": "⚠️", "fail": "❌"}.get(m.status, "")
        lines.append(
            f"| {m.name} | {m.value} | {m.target} | {status_emoji} {m.status} | {m.explanation} |"
        )
    lines.append("")
    if scorecard.gaps:
        lines.append("## Actionable Gaps")
        lines.append("")
        for g in scorecard.gaps:
            lines.append(f"- **{g.gap_type}**")
            if g.object_id:
                lines.append(f"  - Object: `{g.object_id}`")
            if g.suggested_action:
                lines.append(f"  - Suggested action: {g.suggested_action}")
        lines.append("")
    if scorecard.summary:
        lines.append("## Summary")
        lines.append("")
        lines.append(scorecard.summary)
        lines.append("")
    return "\n".join(lines)


def _render_gap_report_md(gap_summary: Any, repo_name: str, generated_at: str) -> str:
    lines: list[str] = [
        "# Gap Report",
        "",
        f"**Repository**: {repo_name}",
        f"**Generated**: {generated_at}",
        f"**Total Gaps**: {gap_summary.total_gap_count}",
        f"**Gap Score**: {gap_summary.gap_score}",
        f"**Total Objects**: {gap_summary.total_objects}",
        "",
        "## Gaps by Type",
        "",
        "| Gap Type | Count | Sample Objects |",
        "|----------|-------|----------------|",
    ]
    for gap_type, summary in gap_summary.gaps_by_type.items():
        samples = ", ".join(summary.sample_object_ids[:3])
        lines.append(f"| {gap_type} | {summary.count} | {samples} |")
    lines.append("")
    if gap_summary.top_objects:
        lines.append("## Top Affected Objects")
        lines.append("")
        for obj_id in gap_summary.top_objects:
            lines.append(f"- `{obj_id}`")
        lines.append("")
    lines.append("## Sources Checked")
    lines.append("")
    for source in gap_summary.sources_checked:
        lines.append(f"- {source}")
    lines.append("")
    return "\n".join(lines)


def _render_high_risk_fields_md(risk_items: list[_RiskItem], repo_name: str) -> str:
    lines: list[str] = [
        "# High Risk Fields",
        "",
        f"**Repository**: {repo_name}",
        f"**Total High Risk Items**: {len(risk_items)}",
        "",
        "## Risk Register",
        "",
        "| Object ID | Type | Name | Severity | Reasons |",
        "|-----------|------|------|----------|---------|",
    ]
    for item in risk_items:
        reasons = "; ".join(item.reasons[:3])
        if len(item.reasons) > 3:
            reasons += f"; +{len(item.reasons) - 3} more"
        name = item.object_name or "—"
        obj_type = item.object_type or "—"
        lines.append(f"| `{item.object_id}` | {obj_type} | {name} | {item.severity} | {reasons} |")
    lines.append("")
    lines.append("## Severity Legend")
    lines.append("")
    lines.append("- **high**: Blocking migration risk — needs immediate attention")
    lines.append("- **medium**: Important gap — should be resolved before go-live")
    lines.append("- **low**: Minor gap — track and resolve during stabilization")
    lines.append("")
    return "\n".join(lines)


def _render_recommendations_md(
    scorecard: Any,
    gap_summary: Any,
    risk_items: list[_RiskItem],
    repo_name: str,
) -> str:
    lines: list[str] = [
        "# Recommendations",
        "",
        f"**Repository**: {repo_name}",
        f"**Readiness Level**: {scorecard.readiness_level}",
        "",
        "## Executive Summary",
        "",
    ]
    if scorecard.summary:
        lines.append(scorecard.summary)
    else:
        lines.append(
            "This assessment identifies priority actions to improve migration model readiness."
        )
    lines.append("")

    # Group recommendations by theme
    themes: dict[str, list[str]] = {
        "Governance & Ownership": [],
        "Data Quality & Validation": [],
        "Mapping & Transformation": [],
        "Risk & Issues": [],
    }

    for g in scorecard.gaps:
        action = g.suggested_action or f"Address {g.gap_type}"
        if g.gap_type in ("missing_owner", "ownership_gap"):
            themes["Governance & Ownership"].append(action)
        elif g.gap_type in (
            "missing_validation_rule",
            "missing_lov",
            "attribute_without_field",
        ):
            themes["Data Quality & Validation"].append(action)
        elif g.gap_type in ("missing_value_mapping", "orphan_field"):
            themes["Mapping & Transformation"].append(action)
        else:
            themes["Risk & Issues"].append(action)

    # Add high-risk items as recommendations
    high_risk = [r for r in risk_items if r.severity == "high"]
    if high_risk:
        for r in high_risk[:10]:
            themes["Risk & Issues"].append(f"Resolve risks for `{r.object_id}`: {r.reasons[0]}")

    for theme, actions in themes.items():
        if not actions:
            continue
        lines.append(f"## {theme}")
        lines.append("")
        for a in sorted(set(actions)):
            lines.append(f"- {a}")
        lines.append("")

    lines.append("## Next Steps")
    lines.append("")
    lines.append(
        "1. Review the [Readiness Scorecard](01_readiness_scorecard.md) for overall health."
    )
    lines.append("2. Triage [High Risk Fields](03_high_risk_fields.md) by severity.")
    lines.append("3. Review [Impact Reports](04_impact_reports/) before making changes.")
    lines.append("4. Assign owners to unowned objects.")
    lines.append("5. Re-run assessment after changes to track progress.")
    lines.append("")
    return "\n".join(lines)


def generate_assessment_package(
    repo_root: Path,
    out_dir: Path,
    generated_at: str | None = None,
) -> AssessmentPackage:
    """Generate a full Migration Model Readiness Assessment package.

    Args:
        repo_root: Path to the model repository.
        out_dir: Directory where the assessment folder will be written.
        generated_at: Optional ISO timestamp. Defaults to the current UTC time.

    Returns:
        AssessmentPackage metadata with artifact list.
    """
    repo_root = repo_root.resolve()
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    config = load_repo_config(repo_root)
    repo_name = config.name if config else repo_root.name

    db_path = _ensure_index(repo_root)

    # Collect data from existing services
    scorecard = generate_scorecard(db_path, repo_root)
    gap_summary = generate_gap_summary_report(db_path, repo_root)
    analysis = generate_analysis_report(db_path, repo_root)
    # Health data is available through gap_summary and scorecard;
    # generate_repository_health is called here to ensure consistency.
    generate_repository_health(db_path)

    # Validation errors from SQLite
    validation_errors = _collect_validation_errors(db_path)

    # High-risk items
    risk_items = _build_high_risk_items(analysis, validation_errors)

    generated_at = generated_at or datetime.now(UTC).isoformat().replace("+00:00", "Z")
    artifacts: list[AssessmentArtifact] = []

    # 01_readiness_scorecard.md
    scorecard_path = out_dir / "01_readiness_scorecard.md"
    scorecard_path.write_text(
        _render_scorecard_md(scorecard, repo_name, generated_at),
        encoding="utf-8",
    )
    artifacts.append(AssessmentArtifact(scorecard_path, "Readiness scorecard"))

    # 02_gap_report.md
    gap_path = out_dir / "02_gap_report.md"
    gap_path.write_text(
        _render_gap_report_md(gap_summary, repo_name, generated_at),
        encoding="utf-8",
    )
    artifacts.append(AssessmentArtifact(gap_path, "Consolidated gap report"))

    # 03_high_risk_fields.md
    risk_path = out_dir / "03_high_risk_fields.md"
    risk_path.write_text(
        _render_high_risk_fields_md(risk_items, repo_name),
        encoding="utf-8",
    )
    artifacts.append(AssessmentArtifact(risk_path, "High risk fields register"))

    # 04_impact_reports/
    impact_dir = out_dir / "04_impact_reports"
    impact_dir.mkdir(parents=True, exist_ok=True)
    top_risk_ids = [r.object_id for r in risk_items[:5]]
    for obj_id in top_risk_ids:
        report = generate_impact_report(db_path, obj_id, max_depth=2, direction="both")
        md = render_impact_report_markdown(report)
        impact_path = impact_dir / f"{obj_id}.md"
        impact_path.write_text(md, encoding="utf-8")
        artifacts.append(AssessmentArtifact(impact_path, f"Impact report for {obj_id}"))

    # 05_business_review.xlsx
    model_path = repo_root / "model"
    if model_path.exists():
        xlsx_path = out_dir / "05_business_review.xlsx"
        export_model_xlsx(
            repo_model_path=model_path,
            output_path=xlsx_path,
            business_review=True,
            generated_at=datetime.fromisoformat(generated_at.replace("Z", "+00:00")),
        )
        artifacts.append(AssessmentArtifact(xlsx_path, "Business review workbook"))

    # 06_recommendations.md
    rec_path = out_dir / "06_recommendations.md"
    rec_path.write_text(
        _render_recommendations_md(scorecard, gap_summary, risk_items, repo_name),
        encoding="utf-8",
    )
    artifacts.append(AssessmentArtifact(rec_path, "Recommendations"))

    return AssessmentPackage(
        repo_name=repo_name,
        generated_at=generated_at,
        readiness_level=scorecard.readiness_level,
        object_count=scorecard.object_count,
        gap_score=gap_summary.gap_score,
        high_risk_count=len(risk_items),
        artifacts=artifacts,
    )


def generate_risk_report(repo_root: Path) -> str:
    """Generate a standalone high-risk fields Markdown report.

    Args:
        repo_root: Path to the model repository.

    Returns:
        Markdown content for the high-risk fields report.
    """
    repo_root = repo_root.resolve()
    config = load_repo_config(repo_root)
    repo_name = config.name if config else repo_root.name

    db_path = _ensure_index(repo_root)
    analysis = generate_analysis_report(db_path, repo_root)
    validation_errors = _collect_validation_errors(db_path)
    risk_items = _build_high_risk_items(analysis, validation_errors)

    return _render_high_risk_fields_md(risk_items, repo_name)


def _render_summary_md(
    scorecard: Any,
    risk_items: list[_RiskItem],
    repo_name: str,
    generated_at: str,
) -> str:
    lines: list[str] = [
        "# Business Review Pack",
        "",
        f"**Repository**: {repo_name}",
        f"**Generated**: {generated_at}",
        f"**Readiness Level**: {scorecard.readiness_level}",
        f"**Total Objects**: {scorecard.object_count}",
        f"**High Risk Items**: {len(risk_items)}",
        "",
        "## Purpose",
        "",
        "This pack is designed for business stakeholders who need to review model content "
        "without using the CLI, Git, or Markdown editors. Each section highlights a specific "
        "area that needs attention, decision, or sign-off.",
        "",
        "## Pack Contents",
        "",
        "- [summary.md](summary.md) — this overview",
        "- [missing_owners.md](missing_owners.md) — objects without an assigned owner",
        "- [fields_needing_decision.md](fields_needing_decision.md) — fields needing a decision",
        "- [high_risk_mappings.md](high_risk_mappings.md) — highest-risk mappings",
        "- [signoff_checklist.md](signoff_checklist.md) — stakeholder sign-off checklist",
        "- [business_review.xlsx](business_review.xlsx) — reviewable workbook",
        "",
        "## How to Use",
        "",
        "1. Review the missing owners list and assign stewards.",
        "2. Open `fields_needing_decision.md` and record decisions in the model.",
        "3. Triage `high_risk_mappings.md` by severity.",
        "4. Complete the sign-off checklist before go-live.",
        "",
    ]
    return "\n".join(lines)


def _render_missing_owners_md(ownership_gaps: list[dict[str, Any]], repo_name: str) -> str:
    lines: list[str] = [
        "# Missing Owners",
        "",
        f"**Repository**: {repo_name}",
        f"**Total Objects Without Owner**: {len(ownership_gaps)}",
        "",
        "Objects listed below do not have an assigned owner. Assign a steward before final review.",
        "",
        "| Object ID | Type | Name |",
        "|-----------|------|------|",
    ]
    for g in ownership_gaps:
        obj_id = g.get("object_id") or "—"
        obj_type = g.get("object_type") or "—"
        name = g.get("object_name") or "—"
        lines.append(f"| `{obj_id}` | {obj_type} | {name} |")
    lines.append("")
    return "\n".join(lines)


def _render_fields_needing_decision_md(
    validation_coverage: list[dict[str, Any]],
    lov_coverage: list[dict[str, Any]],
    mapping_coverage: list[dict[str, Any]],
    repo_name: str,
) -> str:
    items: list[tuple[str, str, str, str]] = []
    for g in validation_coverage:
        items.append(
            (
                g.get("object_id") or "—",
                g.get("object_type") or "Attribute",
                g.get("object_name") or "—",
                "Missing validation rule",
            )
        )
    for g in lov_coverage:
        items.append(
            (
                g.get("object_id") or "—",
                g.get("object_type") or "FieldEndpoint",
                g.get("object_name") or "—",
                "Missing value list",
            )
        )
    for g in mapping_coverage:
        items.append(
            (
                g.get("object_id") or "—",
                g.get("object_type") or "Mapping",
                g.get("object_name") or "—",
                "Missing value mapping",
            )
        )

    lines: list[str] = [
        "# Fields Needing Decision",
        "",
        f"**Repository**: {repo_name}",
        f"**Total Items**: {len(items)}",
        "",
        "The following objects need a business decision before migration. "
        "Record the decision as a canonical `Decision` object and link it to the affected object.",
        "",
        "| Object ID | Type | Name | Reason |",
        "|-----------|------|------|--------|",
    ]
    for obj_id, obj_type, name, reason in sorted(set(items)):
        lines.append(f"| `{obj_id}` | {obj_type} | {name} | {reason} |")
    lines.append("")
    return "\n".join(lines)


def _render_high_risk_mappings_md(risk_items: list[_RiskItem], repo_name: str) -> str:
    mapping_items = [r for r in risk_items if r.object_type == "Mapping"]
    lines: list[str] = [
        "# High Risk Mappings",
        "",
        f"**Repository**: {repo_name}",
        f"**Total High Risk Mappings**: {len(mapping_items)}",
        "",
        "Mappings listed below have risk signals such as missing value mappings or open issues. "
        "Review them before cutover.",
        "",
        "| Object ID | Name | Severity | Reasons |",
        "|-----------|------|----------|---------|",
    ]
    for item in mapping_items:
        reasons = "; ".join(item.reasons[:3])
        if len(item.reasons) > 3:
            reasons += f"; +{len(item.reasons) - 3} more"
        name = item.object_name or "—"
        lines.append(f"| `{item.object_id}` | {name} | {item.severity} | {reasons} |")
    lines.append("")
    return "\n".join(lines)


def _render_signoff_checklist_md(
    scorecard: Any,
    risk_items: list[_RiskItem],
    repo_name: str,
) -> str:
    high_risk_count = sum(1 for r in risk_items if r.severity == "high")
    lines: list[str] = [
        "# Sign-off Checklist",
        "",
        f"**Repository**: {repo_name}",
        f"**Readiness Level**: {scorecard.readiness_level}",
        f"**High Risk Items**: {high_risk_count}",
        "",
        "Use this checklist to confirm that business stakeholders have reviewed and approved "
        "the model before migration.",
        "",
        "- [ ] All missing owners have been assigned",
        "- [ ] All fields needing a decision have a recorded Decision object",
        "- [ ] High risk mappings have been triaged and accepted or resolved",
        "- [ ] Business review workbook has been reviewed and annotated",
        "- [ ] Readiness level has been accepted by the migration lead",
        "- [ ] Sign-off has been recorded in the project decision log",
        "",
    ]
    return "\n".join(lines)


def generate_review_pack(
    repo_root: Path,
    out_dir: Path,
    generated_at: str | None = None,
) -> list[AssessmentArtifact]:
    """Generate a business-reviewable pack for non-technical stakeholders.

    Args:
        repo_root: Path to the model repository.
        out_dir: Directory where the review pack will be written.
        generated_at: Optional ISO timestamp. Defaults to the current UTC time.

    Returns:
        List of artifacts generated.
    """
    repo_root = repo_root.resolve()
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    config = load_repo_config(repo_root)
    repo_name = config.name if config else repo_root.name

    db_path = _ensure_index(repo_root)
    scorecard = generate_scorecard(db_path, repo_root)
    analysis = generate_analysis_report(db_path, repo_root)
    validation_errors = _collect_validation_errors(db_path)
    risk_items = _build_high_risk_items(analysis, validation_errors)

    generated_at = generated_at or datetime.now(UTC).isoformat().replace("+00:00", "Z")
    artifacts: list[AssessmentArtifact] = []

    # summary.md
    summary_path = out_dir / "summary.md"
    summary_path.write_text(
        _render_summary_md(scorecard, risk_items, repo_name, generated_at),
        encoding="utf-8",
    )
    artifacts.append(AssessmentArtifact(summary_path, "Review pack summary"))

    # missing_owners.md
    missing_owners_path = out_dir / "missing_owners.md"
    missing_owners_path.write_text(
        _render_missing_owners_md(analysis.ownership_gaps, repo_name),
        encoding="utf-8",
    )
    artifacts.append(AssessmentArtifact(missing_owners_path, "Missing owners list"))

    # fields_needing_decision.md
    decisions_path = out_dir / "fields_needing_decision.md"
    decisions_path.write_text(
        _render_fields_needing_decision_md(
            analysis.validation_coverage,
            analysis.lov_coverage,
            analysis.mapping_coverage,
            repo_name,
        ),
        encoding="utf-8",
    )
    artifacts.append(AssessmentArtifact(decisions_path, "Fields needing decision"))

    # high_risk_mappings.md
    high_risk_path = out_dir / "high_risk_mappings.md"
    high_risk_path.write_text(
        _render_high_risk_mappings_md(risk_items, repo_name),
        encoding="utf-8",
    )
    artifacts.append(AssessmentArtifact(high_risk_path, "High risk mappings"))

    # signoff_checklist.md
    checklist_path = out_dir / "signoff_checklist.md"
    checklist_path.write_text(
        _render_signoff_checklist_md(scorecard, risk_items, repo_name),
        encoding="utf-8",
    )
    artifacts.append(AssessmentArtifact(checklist_path, "Sign-off checklist"))

    # business_review.xlsx
    model_path = repo_root / "model"
    if model_path.exists():
        xlsx_path = out_dir / "business_review.xlsx"
        export_model_xlsx(
            repo_model_path=model_path,
            output_path=xlsx_path,
            business_review=True,
            generated_at=datetime.fromisoformat(generated_at.replace("Z", "+00:00")),
        )
        artifacts.append(AssessmentArtifact(xlsx_path, "Business review workbook"))

    return artifacts
