"""Model analysis reports for completeness, risk, and readiness."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from modelops_core.reports.audit_service import AuditEventService


@dataclass
class OrphanFieldReport:
    """Fields without linked business attributes."""

    field_endpoints_without_attribute: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class AttributeCoverageReport:
    """Attributes without physical field representations."""

    attributes_without_fields: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class RiskReport:
    """Unresolved issues and risks."""

    open_issues: list[dict[str, Any]] = field(default_factory=list)
    open_risks: list[dict[str, Any]] = field(default_factory=list)
    issue_count: int = 0
    risk_count: int = 0


@dataclass
class ChangeActivityReport:
    """Recent audit log activity."""

    recent_events: list[dict[str, Any]] = field(default_factory=list)
    event_count: int = 0


@dataclass
class LifecycleSummary:
    """Counts of objects by lifecycle status category."""

    proposed: int = 0
    draft: int = 0
    active: int = 0
    under_review: int = 0
    deprecated: int = 0
    retired: int = 0
    blocked: int = 0
    planned: int = 0
    implemented: int = 0
    other: int = 0
    with_target_release: int = 0
    with_roadmap_priority: int = 0


@dataclass
class AnalysisReport:
    """Combined model analysis report."""

    object_count: int = 0
    type_counts: dict[str, int] = field(default_factory=dict)
    orphan_fields: OrphanFieldReport | None = None
    attribute_coverage: AttributeCoverageReport | None = None
    ownership_gaps: list[dict[str, Any]] = field(default_factory=list)
    validation_coverage: list[dict[str, Any]] = field(default_factory=list)
    lov_coverage: list[dict[str, Any]] = field(default_factory=list)
    mapping_coverage: list[dict[str, Any]] = field(default_factory=list)
    risk_report: RiskReport | None = None
    change_activity: ChangeActivityReport | None = None
    lifecycle_summary: LifecycleSummary | None = None


def _load_objects(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute("SELECT id, type, name, status, frontmatter_json FROM objects").fetchall()
    result = []
    for obj_id, obj_type, name, status, fm_json in rows:
        fm = json.loads(fm_json or "{}")
        result.append(
            {
                "id": obj_id,
                "type": obj_type,
                "name": name,
                "status": status,
                "frontmatter": fm,
            }
        )
    return result


def _is_active(status: str | None) -> bool:
    return str(status or "").lower() in ("active", "draft")


def _has_owner(fm: dict[str, Any]) -> bool:
    return any(
        fm.get(f)
        for f in (
            "business_owner",
            "technical_owner",
            "data_steward",
            "accountable_team",
            "approver",
        )
    )


def generate_analysis_report(
    db_path: Path,
    repo_root: Path,
    max_events: int = 20,
) -> AnalysisReport:
    """Generate a comprehensive analysis report from the SQLite index."""
    conn = sqlite3.connect(str(db_path))
    try:
        objects = _load_objects(conn)
        type_counts: dict[str, int] = {}
        for obj in objects:
            type_counts[obj["type"]] = type_counts.get(obj["type"], 0) + 1

        # Orphan fields: FieldEndpoints without business_attribute
        orphan_fields = OrphanFieldReport()
        for obj in objects:
            if obj["type"] == "FieldEndpoint" and _is_active(obj["status"]):
                if not obj["frontmatter"].get("business_attribute"):
                    orphan_fields.field_endpoints_without_attribute.append(
                        {
                            "object_id": obj["id"],
                            "object_name": obj["name"],
                            "reason": "No linked business_attribute",
                        }
                    )

        # Attributes without physical fields
        # Find all AttributeUsage objects and group by attribute
        attributes_with_fields: set[str] = set()
        for obj in objects:
            if obj["type"] == "AttributeUsage":
                attr = obj["frontmatter"].get("attribute")
                if attr:
                    attributes_with_fields.add(attr)

        attribute_coverage = AttributeCoverageReport()
        for obj in objects:
            if obj["type"] == "Attribute" and _is_active(obj["status"]):
                if obj["id"] not in attributes_with_fields:
                    attribute_coverage.attributes_without_fields.append(
                        {
                            "object_id": obj["id"],
                            "object_name": obj["name"],
                            "reason": "No AttributeUsage or FieldEndpoint linked",
                        }
                    )

        # Ownership gaps
        ownership_gaps: list[dict[str, Any]] = []
        _OWNERSHIP_TYPES = {
            "Attribute",
            "FieldEndpoint",
            "Dataset",
            "Mapping",
            "ValidationRule",
            "Issue",
            "Decision",
            "BusinessEntity",
            "ValueList",
            "ValueMapping",
        }
        for obj in objects:
            if obj["type"] in _OWNERSHIP_TYPES and _is_active(obj["status"]):
                if not _has_owner(obj["frontmatter"]):
                    ownership_gaps.append(
                        {
                            "object_id": obj["id"],
                            "object_type": obj["type"],
                            "object_name": obj["name"],
                            "gap_type": "missing_owner",
                        }
                    )

        # Validation coverage: active Attributes without ValidationRule
        validation_rule_attributes: set[str] = set()
        for obj in objects:
            if obj["type"] == "ValidationRule":
                attr = obj["frontmatter"].get("attribute")
                if attr:
                    validation_rule_attributes.add(attr)

        validation_coverage: list[dict[str, Any]] = []
        for obj in objects:
            if obj["type"] == "Attribute" and _is_active(obj["status"]):
                if obj["id"] not in validation_rule_attributes:
                    validation_coverage.append(
                        {
                            "object_id": obj["id"],
                            "object_name": obj["name"],
                            "gap_type": "missing_validation_rule",
                        }
                    )

        # LoV coverage: active FieldEndpoints without value_list
        lov_coverage: list[dict[str, Any]] = []
        for obj in objects:
            if obj["type"] == "FieldEndpoint" and _is_active(obj["status"]):
                if not obj["frontmatter"].get("value_list"):
                    lov_coverage.append(
                        {
                            "object_id": obj["id"],
                            "object_name": obj["name"],
                            "gap_type": "missing_lov",
                        }
                    )

        # Mapping coverage: active Mappings without value_mapping
        mapping_coverage: list[dict[str, Any]] = []
        for obj in objects:
            if obj["type"] == "Mapping" and _is_active(obj["status"]):
                if not obj["frontmatter"].get("value_mapping"):
                    mapping_coverage.append(
                        {
                            "object_id": obj["id"],
                            "object_name": obj["name"],
                            "gap_type": "missing_value_mapping",
                        }
                    )

        # Risk report: open Issues and Risks
        risk_report = RiskReport()
        for obj in objects:
            if obj["type"] == "Issue" and _is_active(obj["status"]):
                risk_report.open_issues.append(
                    {
                        "object_id": obj["id"],
                        "object_name": obj["name"],
                        "status": obj["status"],
                    }
                )
            if obj["type"] == "Risk" and _is_active(obj["status"]):
                risk_report.open_risks.append(
                    {
                        "object_id": obj["id"],
                        "object_name": obj["name"],
                        "status": obj["status"],
                    }
                )
        risk_report.issue_count = len(risk_report.open_issues)
        risk_report.risk_count = len(risk_report.open_risks)

        # Change activity from audit log
        change_activity = ChangeActivityReport()
        audit_service = AuditEventService(repo_root)
        events = audit_service.read_events()
        # Sort by timestamp descending
        events.sort(key=lambda e: e.timestamp, reverse=True)
        for event in events[:max_events]:
            change_activity.recent_events.append(
                {
                    "event_id": event.event_id,
                    "event_type": event.event_type,
                    "timestamp": event.timestamp,
                    "status": event.status,
                    "proposal_id": event.proposal_id,
                }
            )
        change_activity.event_count = len(events)

        # Lifecycle summary
        lifecycle_summary = LifecycleSummary()
        for obj in objects:
            status = str(obj["status"] or "").lower()
            if status == "proposed":
                lifecycle_summary.proposed += 1
            elif status == "draft":
                lifecycle_summary.draft += 1
            elif status == "active":
                lifecycle_summary.active += 1
            elif status == "under_review":
                lifecycle_summary.under_review += 1
            elif status == "deprecated":
                lifecycle_summary.deprecated += 1
            elif status == "retired":
                lifecycle_summary.retired += 1
            elif status == "blocked":
                lifecycle_summary.blocked += 1
            elif status == "planned":
                lifecycle_summary.planned += 1
            elif status == "implemented":
                lifecycle_summary.implemented += 1
            else:
                lifecycle_summary.other += 1

            fm = obj["frontmatter"]
            if fm.get("target_release"):
                lifecycle_summary.with_target_release += 1
            if fm.get("roadmap_priority"):
                lifecycle_summary.with_roadmap_priority += 1

        return AnalysisReport(
            object_count=len(objects),
            type_counts=type_counts,
            orphan_fields=orphan_fields,
            attribute_coverage=attribute_coverage,
            ownership_gaps=ownership_gaps,
            validation_coverage=validation_coverage,
            lov_coverage=lov_coverage,
            mapping_coverage=mapping_coverage,
            risk_report=risk_report,
            change_activity=change_activity,
            lifecycle_summary=lifecycle_summary,
        )
    finally:
        conn.close()
