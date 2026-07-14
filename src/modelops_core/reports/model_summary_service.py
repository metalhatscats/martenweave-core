"""Model summary report generation for a domain or entire repository."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from modelops_core.config import resolve_generated_path
from modelops_core.reports.health_report import (
    CoverageGap,
    generate_repository_health,
)


@dataclass
class AttributeSummary:
    object_id: str
    name: str | None
    status: str | None
    source_endpoints: list[dict[str, Any]] = field(default_factory=list)
    target_endpoints: list[dict[str, Any]] = field(default_factory=list)
    open_issues: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class FieldEndpointSummary:
    object_id: str
    name: str | None
    status: str | None
    endpoint_type: str | None
    system: str | None
    sap_table: str | None
    sap_field: str | None
    column_name: str | None
    field_name: str | None = None
    business_attribute: str | None = None


@dataclass
class MappingSummary:
    object_id: str
    name: str | None
    status: str | None
    source_endpoint: str | None
    target_endpoint: str | None
    value_mapping: str | None


@dataclass
class IssueSummary:
    object_id: str
    name: str | None
    status: str | None
    severity: str | None
    issue_type: str | None


@dataclass
class DecisionSummary:
    object_id: str
    name: str | None
    status: str | None
    evidence: Any = None


@dataclass
class ModelSummaryReport:
    """Compact Markdown-ready summary of a domain or repository."""

    repo_name: str
    domain_id: str | None
    generated_at: str
    object_count: int
    type_counts: dict[str, int]
    attributes: list[AttributeSummary]
    source_fields: list[FieldEndpointSummary]
    target_fields: list[FieldEndpointSummary]
    mappings: list[MappingSummary]
    validation_summary: dict[str, Any]
    coverage_gaps: list[CoverageGap]
    open_issues: list[IssueSummary]
    decisions: list[DecisionSummary]
    owners: list[str]
    evidence: list[str]


def _objects_in_scope(conn: sqlite3.Connection, domain_id: str | None) -> list[dict[str, Any]]:
    """Return objects in the given domain, or all objects if no domain."""
    if domain_id:
        rows = conn.execute(
            "SELECT id, type, status, name, title, domain, description, "
            "source_file, frontmatter_json FROM objects WHERE domain = ? OR id = ?",
            (domain_id, domain_id),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, type, status, name, title, domain, description, "
            "source_file, frontmatter_json FROM objects"
        ).fetchall()

    return [
        {
            "id": r[0],
            "type": r[1],
            "status": r[2],
            "name": r[3],
            "title": r[4],
            "domain": r[5],
            "description": r[6],
            "source_file": r[7],
            "frontmatter": json.loads(r[8] or "{}"),
        }
        for r in rows
    ]


def _frontmatter_evidence(frontmatter: dict[str, Any]) -> list[str]:
    value = frontmatter.get("evidence")
    if isinstance(value, str) and value:
        return [value]
    if isinstance(value, list):
        return [str(v) for v in value if v]
    return []


def _load_attribute_endpoints(
    conn: sqlite3.Connection, attribute_ids: set[str]
) -> dict[str, list[dict[str, Any]]]:
    """Map attribute id -> list of related FieldEndpoint summaries."""
    if not attribute_ids:
        return {}

    placeholders = ", ".join("?" * len(attribute_ids))
    rows = conn.execute(
        f"""
        SELECT o.id, o.type, o.status, o.name, o.frontmatter_json
        FROM objects o
        JOIN object_relationships rel
          ON rel.from_object_id = o.id
        WHERE rel.to_object_id IN ({placeholders})
          AND rel.relationship_type IN ('represents_attribute', 'has_attribute')
          AND o.type = 'FieldEndpoint'
        """,
        tuple(attribute_ids),
    ).fetchall()

    result: dict[str, list[dict[str, Any]]] = {aid: [] for aid in attribute_ids}
    for row in rows:
        fm = json.loads(row[4] or "{}")
        ep = {
            "object_id": row[0],
            "name": row[3],
            "status": row[2],
            "endpoint_type": fm.get("endpoint_type"),
            "system": fm.get("system"),
            "sap_table": fm.get("sap_table"),
            "sap_field": fm.get("sap_field"),
            "column_name": fm.get("column_name"),
            "field_name": fm.get("field_name"),
        }
        # Attribute mapping determined by the relationship target.
        # We attach to every attribute in the IN set; the caller filters by relationship target.
        for aid in attribute_ids:
            result[aid].append(ep)

    # Re-attach correctly via relationship target to avoid over-attachment.
    result = {aid: [] for aid in attribute_ids}
    rows = conn.execute(
        f"""
        SELECT rel.to_object_id, o.id, o.status, o.name, o.frontmatter_json
        FROM object_relationships rel
        JOIN objects o ON o.id = rel.from_object_id
        WHERE rel.to_object_id IN ({placeholders})
          AND rel.relationship_type IN ('represents_attribute', 'has_attribute')
          AND o.type = 'FieldEndpoint'
        """,
        tuple(attribute_ids),
    ).fetchall()
    for aid, ep_id, status, name, fm_json in rows:
        fm = json.loads(fm_json or "{}")
        result.setdefault(aid, []).append(
            {
                "object_id": ep_id,
                "name": name,
                "status": status,
                "endpoint_type": fm.get("endpoint_type"),
                "system": fm.get("system"),
                "sap_table": fm.get("sap_table"),
                "sap_field": fm.get("sap_field"),
                "column_name": fm.get("column_name"),
                "field_name": fm.get("field_name"),
            }
        )
    return result


def _load_issues_and_decisions(
    conn: sqlite3.Connection, object_ids: set[str]
) -> tuple[list[IssueSummary], list[DecisionSummary]]:
    """Find Issue/Decision objects in scope or referencing scope objects."""
    issues: list[IssueSummary] = []
    decisions: list[DecisionSummary] = []
    if not object_ids:
        return issues, decisions

    # Direct domain membership
    rows = conn.execute(
        "SELECT id, type, status, name, frontmatter_json FROM objects "
        "WHERE type IN ('Issue', 'Decision')"
    ).fetchall()

    for obj_id, obj_type, status, name, fm_json in rows:
        fm = json.loads(fm_json or "{}")
        obj_domain = fm.get("domain")
        affected = fm.get("affected_object") or fm.get("affected_objects") or []
        if isinstance(affected, str):
            affected = [affected]
        in_scope = (
            obj_id in object_ids
            or obj_domain in object_ids
            or any(aid in object_ids for aid in affected)
        )
        if not in_scope:
            continue
        if obj_type == "Issue":
            issues.append(
                IssueSummary(
                    object_id=obj_id,
                    name=name,
                    status=status,
                    severity=fm.get("severity"),
                    issue_type=fm.get("issue_type"),
                )
            )
        else:
            decisions.append(
                DecisionSummary(
                    object_id=obj_id,
                    name=name,
                    status=status,
                    evidence=fm.get("evidence"),
                )
            )

    return issues, decisions


def _validation_summary_for_scope(conn: sqlite3.Connection, object_ids: set[str]) -> dict[str, Any]:
    if not object_ids:
        return {"error_count": 0, "warning_count": 0, "info_count": 0, "by_code": {}}

    placeholders = ", ".join("?" * len(object_ids))
    rows = conn.execute(
        f"SELECT severity, code, COUNT(*) FROM validation_results "
        f"WHERE object_id IN ({placeholders}) "
        f"GROUP BY severity, code",
        tuple(object_ids),
    ).fetchall()

    by_code: dict[str, dict[str, Any]] = {}
    error_count = 0
    warning_count = 0
    info_count = 0
    for severity, code, count in rows:
        by_code[code] = {"severity": severity, "count": count}
        if severity == "ERROR":
            error_count += count
        elif severity == "WARNING":
            warning_count += count
        elif severity == "INFO":
            info_count += count

    return {
        "error_count": error_count,
        "warning_count": warning_count,
        "info_count": info_count,
        "by_code": by_code,
    }


def _collect_owners(objects: list[dict[str, Any]]) -> list[str]:
    owners: set[str] = set()
    for obj in objects:
        fm = obj.get("frontmatter", {})
        for key in (
            "business_owner",
            "technical_owner",
            "data_steward",
            "accountable_team",
            "approver",
        ):
            value = fm.get(key)
            if value:
                if isinstance(value, list):
                    owners.update(str(v) for v in value if v)
                else:
                    owners.add(str(value))
    return sorted(owners)


def _coverage_gaps_for_scope(db_path: Path, object_ids: set[str]) -> list[CoverageGap]:
    if not object_ids:
        return []

    report = generate_repository_health(db_path)
    return [g for g in report.coverage_gaps_list if g.object_id in object_ids]


def generate_model_summary(
    repo_root: Path,
    domain_id: str | None = None,
    db_path: Path | None = None,
) -> ModelSummaryReport:
    """Generate a compact Markdown-ready summary for a domain or repository."""
    if db_path is None:
        db_path = resolve_generated_path(repo_root) / "modelops.db"

    repo_name = "Untitled Repository"
    from modelops_core.config import load_repo_config

    config = load_repo_config(repo_root)
    if config:
        repo_name = config.name

    if not db_path.exists():
        return ModelSummaryReport(
            repo_name=repo_name,
            domain_id=domain_id,
            generated_at=datetime.now(UTC).isoformat(),
            object_count=0,
            type_counts={},
            attributes=[],
            source_fields=[],
            target_fields=[],
            mappings=[],
            validation_summary={
                "error_count": 0,
                "warning_count": 0,
                "info_count": 0,
                "by_code": {},
            },
            coverage_gaps=[],
            open_issues=[],
            decisions=[],
            owners=[],
            evidence=[],
        )

    conn = sqlite3.connect(str(db_path))
    try:
        objects = _objects_in_scope(conn, domain_id)
        object_ids = {o["id"] for o in objects}

        type_counts: dict[str, int] = {}
        for obj in objects:
            type_counts[obj["type"]] = type_counts.get(obj["type"], 0) + 1

        attribute_objs = [o for o in objects if o["type"] == "Attribute"]
        attribute_ids = {o["id"] for o in attribute_objs}
        endpoints_by_attr = _load_attribute_endpoints(conn, attribute_ids)

        open_issues, decisions = _load_issues_and_decisions(conn, object_ids)
        validation_summary = _validation_summary_for_scope(conn, object_ids)
        coverage_gaps = _coverage_gaps_for_scope(db_path, object_ids)

        attributes: list[AttributeSummary] = []
        for obj in attribute_objs:
            eps = endpoints_by_attr.get(obj["id"], [])
            source = [e for e in eps if e.get("endpoint_type") != "sap_table_field"]
            target = [e for e in eps if e.get("endpoint_type") == "sap_table_field"]
            attr_issues = [i for i in open_issues if obj["id"] in {i.object_id}]
            attributes.append(
                AttributeSummary(
                    object_id=obj["id"],
                    name=obj.get("name"),
                    status=obj.get("status"),
                    source_endpoints=source,
                    target_endpoints=target,
                    open_issues=[
                        {
                            "object_id": i.object_id,
                            "name": i.name,
                            "severity": i.severity,
                        }
                        for i in attr_issues
                    ],
                )
            )

        source_fields: list[FieldEndpointSummary] = []
        target_fields: list[FieldEndpointSummary] = []
        for obj in objects:
            if obj["type"] != "FieldEndpoint":
                continue
            fm = obj.get("frontmatter", {})
            ep = FieldEndpointSummary(
                object_id=obj["id"],
                name=obj.get("name"),
                status=obj.get("status"),
                endpoint_type=fm.get("endpoint_type"),
                system=fm.get("system"),
                sap_table=fm.get("sap_table"),
                sap_field=fm.get("sap_field"),
                column_name=fm.get("column_name"),
                field_name=fm.get("field_name") or fm.get("sap_field"),
                business_attribute=fm.get("business_attribute"),
            )
            if ep.endpoint_type == "sap_table_field":
                target_fields.append(ep)
            else:
                source_fields.append(ep)

        mappings: list[MappingSummary] = []
        for obj in objects:
            if obj["type"] != "Mapping":
                continue
            fm = obj.get("frontmatter", {})
            mappings.append(
                MappingSummary(
                    object_id=obj["id"],
                    name=obj.get("name"),
                    status=obj.get("status"),
                    source_endpoint=fm.get("source_endpoint"),
                    target_endpoint=fm.get("target_endpoint"),
                    value_mapping=fm.get("value_mapping"),
                )
            )

        evidence: set[str] = set()
        for obj in objects:
            evidence.update(_frontmatter_evidence(obj.get("frontmatter", {})))
        for decision in decisions:
            if isinstance(decision.evidence, str) and decision.evidence:
                evidence.add(decision.evidence)
            elif isinstance(decision.evidence, list):
                evidence.update(str(v) for v in decision.evidence if v)

        owners = _collect_owners(objects)

        return ModelSummaryReport(
            repo_name=repo_name,
            domain_id=domain_id,
            generated_at=datetime.now(UTC).isoformat(),
            object_count=len(objects),
            type_counts=type_counts,
            attributes=attributes,
            source_fields=source_fields,
            target_fields=target_fields,
            mappings=mappings,
            validation_summary=validation_summary,
            coverage_gaps=coverage_gaps,
            open_issues=open_issues,
            decisions=decisions,
            owners=owners,
            evidence=sorted(evidence),
        )
    finally:
        conn.close()


def model_summary_to_markdown(report: ModelSummaryReport) -> str:
    """Render a ModelSummaryReport as Markdown."""
    lines: list[str] = []

    scope = report.domain_id or "Entire repository"
    lines.append(f"# Model Summary: {scope}")
    lines.append("")
    lines.append(f"- **Repository:** {report.repo_name}")
    lines.append(f"- **Generated:** {report.generated_at}")
    lines.append(f"- **Objects:** {report.object_count}")
    lines.append("")

    if report.type_counts:
        lines.append("## Object counts")
        lines.append("")
        lines.append("| Type | Count |")
        lines.append("|------|-------|")
        for obj_type, count in sorted(report.type_counts.items()):
            lines.append(f"| {obj_type} | {count} |")
        lines.append("")

    if report.attributes:
        lines.append("## Attributes")
        lines.append("")
        lines.append("| Attribute | Status | Source fields | Target fields | Open issues |")
        lines.append("|-----------|--------|---------------|---------------|-------------|")
        for attr in report.attributes:
            src = ", ".join(f"`{e['object_id']}`" for e in attr.source_endpoints) or "—"
            tgt = ", ".join(f"`{e['object_id']}`" for e in attr.target_endpoints) or "—"
            issues = str(len(attr.open_issues)) if attr.open_issues else "—"
            name = attr.name or attr.object_id
            lines.append(
                f"| `{attr.object_id}` {name} | {attr.status or '—'} | {src} | {tgt} | {issues} |"
            )
        lines.append("")

    if report.source_fields:
        lines.append("## Source fields")
        lines.append("")
        lines.append("| Field | Type | System | Source column/field | Attribute |")
        lines.append("|-------|------|--------|---------------------|-----------|")
        for ep in report.source_fields:
            col = ep.column_name or ep.field_name or "—"
            attr = f"`{ep.business_attribute}`" if ep.business_attribute else "—"
            lines.append(
                f"| `{ep.object_id}` {ep.name or ''} | {ep.endpoint_type or '—'} | "
                f"{ep.system or '—'} | {col} | {attr} |"
            )
        lines.append("")

    if report.target_fields:
        lines.append("## Target fields")
        lines.append("")
        lines.append("| Field | SAP table | SAP field | Attribute |")
        lines.append("|-------|-----------|-----------|-----------|")
        for ep in report.target_fields:
            attr = f"`{ep.business_attribute}`" if ep.business_attribute else "—"
            lines.append(
                f"| `{ep.object_id}` {ep.name or ''} | {ep.sap_table or '—'} | "
                f"{ep.sap_field or '—'} | {attr} |"
            )
        lines.append("")

    if report.mappings:
        lines.append("## Mappings")
        lines.append("")
        lines.append("| Mapping | Source | Target | Value mapping |")
        lines.append("|---------|--------|--------|---------------|")
        for m in report.mappings:
            vm = f"`{m.value_mapping}`" if m.value_mapping else "—"
            src = f"`{m.source_endpoint}`" if m.source_endpoint else "—"
            tgt = f"`{m.target_endpoint}`" if m.target_endpoint else "—"
            lines.append(f"| `{m.object_id}` {m.name or ''} | {src} | {tgt} | {vm} |")
        lines.append("")

    vs = report.validation_summary
    lines.append("## Validation scope")
    lines.append("")
    lines.append(
        f"Errors: {vs.get('error_count', 0)} | Warnings: {vs.get('warning_count', 0)} | "
        f"Info: {vs.get('info_count', 0)}"
    )
    lines.append("")
    if vs.get("by_code"):
        lines.append("| Code | Severity | Count |")
        lines.append("|------|----------|-------|")
        for code, info in vs["by_code"].items():
            lines.append(f"| {code} | {info['severity']} | {info['count']} |")
        lines.append("")

    if report.coverage_gaps:
        lines.append("## Open coverage gaps")
        lines.append("")
        lines.append("| Object | Type | Gap | Suggested action |")
        lines.append("|--------|------|-----|------------------|")
        for gap in report.coverage_gaps:
            lines.append(
                f"| `{gap.object_id}` | {gap.object_type or '—'} | {gap.gap_type} | "
                f"{gap.suggested_action or '—'} |"
            )
        lines.append("")

    if report.open_issues:
        lines.append("## Open issues")
        lines.append("")
        lines.append("| Issue | Severity | Type |")
        lines.append("|-------|----------|------|")
        for issue in report.open_issues:
            lines.append(
                f"| `{issue.object_id}` {issue.name or ''} | "
                f"{issue.severity or '—'} | {issue.issue_type or '—'} |"
            )
        lines.append("")

    if report.decisions:
        lines.append("## Decisions")
        lines.append("")
        lines.append("| Decision | Status | Evidence |")
        lines.append("|----------|--------|----------|")
        for decision in report.decisions:
            ev = "Yes" if decision.evidence else "—"
            lines.append(
                f"| `{decision.object_id}` {decision.name or ''} | "
                f"{decision.status or '—'} | {ev} |"
            )
        lines.append("")

    if report.owners:
        lines.append("## Owners")
        lines.append("")
        for owner in report.owners:
            lines.append(f"- {owner}")
        lines.append("")

    if report.evidence:
        lines.append("## Evidence references")
        lines.append("")
        for ev in report.evidence:
            lines.append(f"- {ev}")
        lines.append("")

    return "\n".join(lines)


def model_summary_to_dict(report: ModelSummaryReport) -> dict[str, Any]:
    """Convert a ModelSummaryReport to a JSON-serializable dict."""
    return {
        "repo_name": report.repo_name,
        "domain_id": report.domain_id,
        "generated_at": report.generated_at,
        "object_count": report.object_count,
        "type_counts": report.type_counts,
        "attributes": [a.__dict__ for a in report.attributes],
        "source_fields": [f.__dict__ for f in report.source_fields],
        "target_fields": [f.__dict__ for f in report.target_fields],
        "mappings": [m.__dict__ for m in report.mappings],
        "validation_summary": report.validation_summary,
        "coverage_gaps": [g.__dict__ for g in report.coverage_gaps],
        "open_issues": [i.__dict__ for i in report.open_issues],
        "decisions": [d.__dict__ for d in report.decisions],
        "owners": report.owners,
        "evidence": report.evidence,
    }
