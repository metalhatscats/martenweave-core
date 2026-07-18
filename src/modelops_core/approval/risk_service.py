"""Deterministic risk assessment for PatchProposals and ChangeRequests."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from modelops_core.impact.proposal_impact_service import ProposalImpactReport
from modelops_core.repository import parse_file, scan_repository

_HIGH_RISK_OBJECT_TYPES: set[str] = {
    "Mapping",
    "ValidationRule",
    "ValueList",
    "ValueMapping",
}

_HIGH_RISK_FIELDS: set[str] = {
    "value_list",
    "validation_rule",
    "business_owner",
    "technical_owner",
    "data_steward",
    "approver",
    "owner",
    "watchers",
}

_OWNER_EXPECTED_TYPES: set[str] = {
    "Attribute",
    "FieldEndpoint",
    "Mapping",
    "ValueList",
    "ValidationRule",
    "BusinessEntity",
    "Dataset",
}

_RISK_THRESHOLDS = {
    "affected_objects": 5,
    "impact_depth": 2,
}


@dataclass
class RiskAssessment:
    """Result of a risk assessment."""

    requires_approval: bool
    risk_level: str  # low, medium, high
    risk_reasons: list[str] = field(default_factory=list)
    triggering_rules: list[str] = field(default_factory=list)
    affected_object_count: int = 0
    max_impact_depth: int = 0


def _build_object_registry(model_path: Path) -> dict[str, dict[str, Any]]:
    """Build a registry of object_id -> frontmatter for quick lookups."""
    registry: dict[str, dict[str, Any]] = {}
    if not model_path.exists():
        return registry
    for file_path in scan_repository(model_path):
        parsed = parse_file(file_path)
        if parsed.frontmatter and parsed.frontmatter.get("id"):
            registry[parsed.frontmatter["id"]] = parsed.frontmatter
    return registry


def _get_object_type(registry: dict[str, dict[str, Any]], object_id: str) -> str | None:
    return registry.get(object_id, {}).get("type")


def _get_object_status(registry: dict[str, dict[str, Any]], object_id: str) -> str | None:
    return registry.get(object_id, {}).get("status")


def _has_owner(registry: dict[str, dict[str, Any]], object_id: str) -> bool:
    fm = registry.get(object_id, {})
    return any(
        fm.get(field) for field in ("business_owner", "technical_owner", "data_steward", "owner")
    )


def _operation_has_owner(
    operation: dict[str, Any], registry: dict[str, dict[str, Any]], object_id: str
) -> bool:
    """Return the owner state after an operation without treating new objects as ownerless."""
    after = operation.get("after")
    if isinstance(after, dict):
        return any(
            after.get(field)
            for field in ("business_owner", "technical_owner", "data_steward", "owner")
        )

    target_path = operation.get("target_path")
    if target_path in {"business_owner", "technical_owner", "data_steward", "owner"}:
        return bool(after)

    return _has_owner(registry, object_id)


def compute_proposal_risk(
    operations: list[dict[str, Any]],
    model_path: Path,
    impact_report: ProposalImpactReport | None = None,
) -> RiskAssessment:
    """Compute risk for a PatchProposal.

    Evaluates object types, status, ownership, affected count, impact depth,
    and field-level changes to determine whether approval is required.
    """
    registry = _build_object_registry(model_path)
    reasons: list[str] = []
    rules: list[str] = []

    affected_ids: set[str] = set()
    max_depth = 0

    if impact_report:
        affected_ids = set(impact_report.affected_object_ids)
        for op_report in impact_report.operation_reports:
            depth = max(
                (obj.depth for obj in op_report.impact_report.affected_objects),
                default=0,
            )
            if depth > max_depth:
                max_depth = depth

    for op in operations:
        obj_id = op.get("object_id")
        obj_type = op.get("object_type") or _get_object_type(registry, obj_id or "")
        target_path = op.get("target_path", "")

        if not obj_id:
            continue

        affected_ids.add(obj_id)

        # Rule: high-risk object type
        if obj_type in _HIGH_RISK_OBJECT_TYPES:
            reasons.append(f"Operation touches high-risk object type '{obj_type}' ({obj_id})")
            rules.append("high_risk_object_type")

        # Rule: active object being modified
        status = _get_object_status(registry, obj_id)
        if status == "active":
            reasons.append(f"Operation modifies active object '{obj_id}'")
            rules.append("active_object_modified")

        # Rule: ownership field changes
        if target_path in _HIGH_RISK_FIELDS or (
            target_path and any(target_path.startswith(f) for f in _HIGH_RISK_FIELDS)
        ):
            reasons.append(f"Operation changes governance field '{target_path}' on '{obj_id}'")
            rules.append("governance_field_changed")

        # Rule: object without owner (only for types expected to have owners)
        if obj_type in _OWNER_EXPECTED_TYPES and not _operation_has_owner(op, registry, obj_id):
            reasons.append(f"Object '{obj_id}' has no assigned owner")
            rules.append("missing_owner")

    # Rule: many affected objects
    if len(affected_ids) > _RISK_THRESHOLDS["affected_objects"]:
        reasons.append(
            f"Proposal affects {len(affected_ids)} objects "
            f"(threshold: {_RISK_THRESHOLDS['affected_objects']})"
        )
        rules.append("many_affected_objects")

    # Rule: deep impact
    if max_depth > _RISK_THRESHOLDS["impact_depth"]:
        reasons.append(
            f"Impact depth {max_depth} exceeds threshold {_RISK_THRESHOLDS['impact_depth']}"
        )
        rules.append("deep_impact")

    # Deduplicate
    reasons = list(dict.fromkeys(reasons))
    rules = list(dict.fromkeys(rules))

    requires_approval = bool(rules)

    if "high_risk_object_type" in rules or "active_object_modified" in rules:
        risk_level = "high"
    elif rules:
        risk_level = "medium"
    else:
        risk_level = "low"

    return RiskAssessment(
        requires_approval=requires_approval,
        risk_level=risk_level,
        risk_reasons=reasons,
        triggering_rules=rules,
        affected_object_count=len(affected_ids),
        max_impact_depth=max_depth,
    )


def assess_change_request(
    cr_frontmatter: dict[str, Any],
    model_path: Path,
) -> RiskAssessment:
    """Assess risk for a ChangeRequest based on its affected objects."""
    registry = _build_object_registry(model_path)
    reasons: list[str] = []
    rules: list[str] = []

    affected_objects = cr_frontmatter.get("affected_objects") or []
    linked_proposals = cr_frontmatter.get("linked_proposals") or []

    for obj_id in affected_objects:
        obj_type = _get_object_type(registry, obj_id)
        status = _get_object_status(registry, obj_id)

        if obj_type in _HIGH_RISK_OBJECT_TYPES:
            reasons.append(f"Affected object '{obj_id}' is high-risk type '{obj_type}'")
            rules.append("high_risk_object_type")

        if status == "active":
            reasons.append(f"Affected object '{obj_id}' is active")
            rules.append("active_object_modified")

        if obj_type in _OWNER_EXPECTED_TYPES and not _has_owner(registry, obj_id):
            reasons.append(f"Affected object '{obj_id}' has no assigned owner")
            rules.append("missing_owner")

    if len(affected_objects) > _RISK_THRESHOLDS["affected_objects"]:
        reasons.append(
            f"ChangeRequest affects {len(affected_objects)} objects "
            f"(threshold: {_RISK_THRESHOLDS['affected_objects']})"
        )
        rules.append("many_affected_objects")

    if linked_proposals:
        reasons.append(f"Linked to {len(linked_proposals)} proposal(s)")
        # Not a gate by itself, but informative

    reasons = list(dict.fromkeys(reasons))
    rules = list(dict.fromkeys(rules))

    requires_approval = bool(rules)

    if "high_risk_object_type" in rules or "active_object_modified" in rules:
        risk_level = "high"
    elif rules:
        risk_level = "medium"
    else:
        risk_level = "low"

    return RiskAssessment(
        requires_approval=requires_approval,
        risk_level=risk_level,
        risk_reasons=reasons,
        triggering_rules=rules,
        affected_object_count=len(affected_objects),
        max_impact_depth=0,
    )
