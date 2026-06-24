"""Deterministic model governance scorecard and readiness metrics."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from modelops_core.config import load_repo_config
from modelops_core.repository import parse_file, scan_repository


@dataclass
class ScorecardMetric:
    """A single deterministic scorecard metric."""

    name: str
    value: float | int
    target: float | int
    status: str  # "pass", "warning", "fail"
    explanation: str
    suggested_action: str | None = None


@dataclass
class ScorecardGap:
    """An actionable gap found during scorecard generation."""

    object_id: str | None
    object_type: str | None
    gap_type: str
    suggested_action: str


@dataclass
class ScorecardReport:
    """Compact governance scorecard for a model repository."""

    repo_name: str
    generated_at: str
    readiness_level: str  # "seed", "draft", "review", "ready"
    object_count: int
    metrics: list[ScorecardMetric] = field(default_factory=list)
    gaps: list[ScorecardGap] = field(default_factory=list)
    summary: str = ""


def _parse_timestamp(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def _compute_traceability_coverage(conn: sqlite3.Connection) -> tuple[int, int]:
    """Return (objects_with_relationships, total_objects)."""
    total = conn.execute("SELECT COUNT(*) FROM objects").fetchone()[0]
    if not total:
        return 0, 0
    with_rels = conn.execute(
        "SELECT COUNT(DISTINCT from_object_id) FROM object_relationships"
    ).fetchone()[0]
    return with_rels, total


def _count_open_issues(model_path: Path) -> int:
    count = 0
    for file_path in scan_repository(model_path):
        parsed = parse_file(file_path)
        if parsed.frontmatter and parsed.frontmatter.get("type") == "Issue":
            status = str(parsed.frontmatter.get("status", "")).lower()
            if status in ("active", "draft", "open"):
                count += 1
    return count


def _count_pending_changes(model_path: Path) -> tuple[int, int]:
    """Return (pending_proposals, pending_crs, high_risk_count)."""
    proposals_dir = model_path / "patch-proposals"
    crs_dir = model_path / "change-requests"

    pending_proposals = 0
    pending_crs = 0
    high_risk = 0

    _HIGH_RISK_TYPES = {"Mapping", "ValidationRule", "ValueList", "ValueMapping"}

    if proposals_dir.exists():
        for f in proposals_dir.glob("*.md"):
            parsed = parse_file(f)
            fm = parsed.frontmatter or {}
            if fm.get("status") == "pending_review":
                pending_proposals += 1
                ops = fm.get("operations") or []
                affected = fm.get("affected_objects") or []
                if len(affected) > 5:
                    high_risk += 1
                else:
                    for op in ops:
                        if op.get("object_type") in _HIGH_RISK_TYPES:
                            high_risk += 1
                            break

    if crs_dir.exists():
        for f in crs_dir.glob("*.md"):
            parsed = parse_file(f)
            fm = parsed.frontmatter or {}
            if fm.get("status") == "pending" and fm.get("approval_status") == "pending":
                pending_crs += 1
                affected = fm.get("affected_objects") or []
                if len(affected) > 5:
                    high_risk += 1
                else:
                    for _obj_id in affected:
                        # We don't have type readily available without registry;
                        # skip type check for CRs to keep it light
                        pass

    return pending_proposals, pending_crs, high_risk


def generate_scorecard(
    db_path: Path,
    repo_root: Path,
    max_gaps: int = 20,
) -> ScorecardReport:
    """Generate a deterministic governance scorecard from the SQLite index.

    Args:
        db_path: Path to the SQLite index database.
        repo_root: Path to the repository root.
        max_gaps: Maximum number of actionable gaps to include.

    Returns:
        ScorecardReport with metrics, gaps, and readiness level.
    """
    config = load_repo_config(repo_root)
    repo_name = config.name if config else "Untitled Repository"

    if not db_path.exists():
        return ScorecardReport(
            repo_name=repo_name,
            generated_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            readiness_level="seed",
            object_count=0,
            summary="No index found. Run `martenweave build-index` first.",
        )

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    try:
        # Manifest
        manifest_rows = conn.execute("SELECT key, value FROM index_manifest").fetchall()
        manifest = {k: v for k, v in manifest_rows}
        build_ts = _parse_timestamp(manifest.get("build_timestamp"))

        # Object counts
        total_objects = conn.execute("SELECT COUNT(*) FROM objects").fetchone()[0]

        type_counts: dict[str, int] = {}
        for row in conn.execute("SELECT type, COUNT(*) FROM objects GROUP BY type"):
            type_counts[row[0]] = row[1]

        # Coverage: names and descriptions
        name_missing = conn.execute(
            "SELECT COUNT(*) FROM objects WHERE name IS NULL OR name = ''"
        ).fetchone()[0]
        desc_missing = conn.execute(
            "SELECT COUNT(*) FROM objects WHERE description IS NULL OR description = ''"
        ).fetchone()[0]

        name_complete = total_objects - name_missing
        desc_complete = total_objects - desc_missing

        # Load frontmatter for enriched metrics
        rows = conn.execute(
            "SELECT id, type, name, status, frontmatter_json FROM objects"
        ).fetchall()

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

        total_eligible = 0
        with_owner = 0
        active_attributes = 0
        attributes_with_rules = 0
        active_endpoints = 0
        endpoints_with_lov = 0
        active_mappings = 0
        mappings_with_vm = 0
        active_datasets = 0
        datasets_with_profile = 0
        active_objects = 0
        objects_with_owner = 0

        # Evidence coverage tracking
        decisions_total = 0
        decisions_with_evidence = 0

        # SAP table coverage tracking
        _TARGET_SAP_TABLES = {"KNVV", "KNB1", "KNVP", "BUT000"}
        sap_total = 0
        sap_with_attribute = 0
        sap_by_table: dict[str, dict[str, int]] = {}
        for t in _TARGET_SAP_TABLES:
            sap_by_table[t] = {"total": 0, "covered": 0}

        validation_rule_attributes: set[str] = set()
        endpoint_value_lists: set[str] = set()
        mapping_value_mappings: set[str] = set()
        dataset_profiles: set[str] = set()

        # Pre-build lookups
        for r in rows:
            if r[1] == "ValidationRule":
                fm = json.loads(r[4] or "{}")
                attr = fm.get("attribute")
                if attr:
                    validation_rule_attributes.add(attr)
            if r[1] == "FieldEndpoint":
                fm = json.loads(r[4] or "{}")
                vl = fm.get("value_list")
                if vl:
                    endpoint_value_lists.add(vl)
            if r[1] == "Mapping":
                fm = json.loads(r[4] or "{}")
                vm = fm.get("value_mapping")
                if vm:
                    mapping_value_mappings.add(vm)

        profile_dir = db_path.parent / "dataset_profiles"
        if profile_dir.exists():
            for f in profile_dir.glob("*.json"):
                dataset_profiles.add(f.stem)

        gaps: list[ScorecardGap] = []

        for obj_id, obj_type, _obj_name, status, fm_json in rows:
            fm = json.loads(fm_json or "{}")
            active = str(status or "").lower() in ("active", "draft")

            if obj_type in _OWNERSHIP_TYPES and active:
                total_eligible += 1
                if any(
                    fm.get(f)
                    for f in (
                        "business_owner",
                        "technical_owner",
                        "data_steward",
                        "accountable_team",
                        "approver",
                    )
                ):
                    with_owner += 1
                else:
                    gaps.append(
                        ScorecardGap(
                            object_id=obj_id,
                            object_type=obj_type,
                            gap_type="missing_owner",
                            suggested_action="Add an ownership field.",
                        )
                    )

            if obj_type == "Attribute" and active:
                active_attributes += 1
                if obj_id in validation_rule_attributes:
                    attributes_with_rules += 1
                else:
                    gaps.append(
                        ScorecardGap(
                            object_id=obj_id,
                            object_type=obj_type,
                            gap_type="missing_validation_rule",
                            suggested_action="Add a ValidationRule referencing this attribute.",
                        )
                    )

            if obj_type == "FieldEndpoint" and active:
                active_endpoints += 1
                if fm.get("value_list"):
                    endpoints_with_lov += 1
                else:
                    gaps.append(
                        ScorecardGap(
                            object_id=obj_id,
                            object_type=obj_type,
                            gap_type="missing_lov",
                            suggested_action="Link a ValueList to this field endpoint.",
                        )
                    )

            if obj_type == "Mapping" and active:
                active_mappings += 1
                if fm.get("value_mapping"):
                    mappings_with_vm += 1
                else:
                    gaps.append(
                        ScorecardGap(
                            object_id=obj_id,
                            object_type=obj_type,
                            gap_type="missing_value_mapping",
                            suggested_action="Link a ValueMapping to this mapping.",
                        )
                    )

            if obj_type == "Dataset" and active:
                active_datasets += 1
                if obj_id in dataset_profiles or fm.get("profile"):
                    datasets_with_profile += 1
                else:
                    gaps.append(
                        ScorecardGap(
                            object_id=obj_id,
                            object_type=obj_type,
                            gap_type="missing_profile",
                            suggested_action="Run profile-dataset on this dataset.",
                        )
                    )

            if active and obj_type in _OWNERSHIP_TYPES:
                active_objects += 1
                if any(
                    fm.get(f)
                    for f in (
                        "business_owner",
                        "technical_owner",
                        "data_steward",
                        "accountable_team",
                        "approver",
                    )
                ):
                    objects_with_owner += 1

            # Evidence coverage
            if obj_type == "Decision":
                decisions_total += 1
                if fm.get("evidence"):
                    decisions_with_evidence += 1

            # SAP table coverage
            if obj_type == "FieldEndpoint" and active:
                sap_table = fm.get("sap_table")
                if sap_table in _TARGET_SAP_TABLES:
                    sap_total += 1
                    sap_by_table[sap_table]["total"] += 1
                    if fm.get("business_attribute") or fm.get("attribute"):
                        sap_with_attribute += 1
                        sap_by_table[sap_table]["covered"] += 1

        # Traceability
        trace_with, trace_total = _compute_traceability_coverage(conn)

        # Source freshness
        hours_old = 0
        if build_ts:
            hours_old = int((datetime.now(UTC) - build_ts).total_seconds() // 3600)

        model_path = repo_root / (config.model_path if config else "model")
        open_issues = _count_open_issues(model_path)
        pending_proposals, pending_crs, high_risk_changes = _count_pending_changes(model_path)

        # Build metrics
        metrics: list[ScorecardMetric] = []

        def _pct(part: int, whole: int) -> float:
            return round(part / whole * 100, 1) if whole else 0.0

        def _status(value: float, warn: float, fail: float) -> str:
            if value >= warn:
                return "pass"
            if value >= fail:
                return "warning"
            return "fail"

        metrics.append(
            ScorecardMetric(
                name="model_completeness",
                value=_pct(name_complete + desc_complete, total_objects * 2),
                target=95.0,
                status=_status(_pct(name_complete + desc_complete, total_objects * 2), 80.0, 50.0),
                explanation=(
                    f"{name_missing} objects missing name, {desc_missing} missing description."
                ),
                suggested_action="Add names and descriptions to all objects.",
            )
        )

        metrics.append(
            ScorecardMetric(
                name="ownership_coverage",
                value=_pct(with_owner, total_eligible),
                target=95.0,
                status=_status(_pct(with_owner, total_eligible), 80.0, 50.0),
                explanation=(
                    f"{total_eligible - with_owner} of {total_eligible} "
                    f"eligible objects lack an owner."
                ),
                suggested_action="Assign business_owner or technical_owner.",
            )
        )

        metrics.append(
            ScorecardMetric(
                name="validation_rule_coverage",
                value=_pct(attributes_with_rules, active_attributes),
                target=90.0,
                status=_status(_pct(attributes_with_rules, active_attributes), 70.0, 40.0),
                explanation=(
                    f"{active_attributes - attributes_with_rules} "
                    f"active attributes have no validation rule."
                ),
                suggested_action="Add ValidationRule objects for uncovered attributes.",
            )
        )

        metrics.append(
            ScorecardMetric(
                name="lov_coverage",
                value=_pct(endpoints_with_lov, active_endpoints),
                target=90.0,
                status=_status(_pct(endpoints_with_lov, active_endpoints), 70.0, 40.0),
                explanation=(
                    f"{active_endpoints - endpoints_with_lov} "
                    f"active field endpoints lack a value list."
                ),
                suggested_action="Link ValueList references to field endpoints.",
            )
        )

        metrics.append(
            ScorecardMetric(
                name="mapping_logic_coverage",
                value=_pct(mappings_with_vm, active_mappings),
                target=90.0,
                status=_status(_pct(mappings_with_vm, active_mappings), 70.0, 40.0),
                explanation=(
                    f"{active_mappings - mappings_with_vm} active mappings lack a value mapping."
                ),
                suggested_action="Link ValueMapping references to mappings.",
            )
        )

        metrics.append(
            ScorecardMetric(
                name="dataset_profile_coverage",
                value=_pct(datasets_with_profile, active_datasets),
                target=80.0,
                status=_status(_pct(datasets_with_profile, active_datasets), 60.0, 30.0),
                explanation=(
                    f"{active_datasets - datasets_with_profile} active datasets lack a profile."
                ),
                suggested_action="Run profile-dataset on uncovered datasets.",
            )
        )

        metrics.append(
            ScorecardMetric(
                name="traceability_coverage",
                value=_pct(trace_with, trace_total),
                target=80.0,
                status=_status(_pct(trace_with, trace_total), 60.0, 30.0),
                explanation=f"{trace_total - trace_with} objects have no relationships.",
                suggested_action="Add domain, entity, attribute, and mapping references.",
            )
        )

        metrics.append(
            ScorecardMetric(
                name="source_freshness_hours",
                value=hours_old,
                target=24,
                status=("pass" if hours_old <= 24 else "warning" if hours_old <= 72 else "fail"),
                explanation=(
                    f"Index was built {hours_old} hour(s) ago."
                    if build_ts
                    else "Index build timestamp unknown."
                ),
                suggested_action=(
                    "Run `martenweave build-index` to refresh the index."
                    if hours_old > 24
                    else None
                ),
            )
        )

        metrics.append(
            ScorecardMetric(
                name="unresolved_issue_count",
                value=open_issues,
                target=0,
                status="pass" if open_issues == 0 else "warning" if open_issues <= 3 else "fail",
                explanation=f"{open_issues} open issue(s) found in the model.",
                suggested_action="Resolve or close open issues." if open_issues > 0 else None,
            )
        )

        metrics.append(
            ScorecardMetric(
                name="pending_change_count",
                value=pending_proposals + pending_crs,
                target=0,
                status=("pass" if pending_proposals + pending_crs == 0 else "warning"),
                explanation=(
                    f"{pending_proposals} pending proposal(s), "
                    f"{pending_crs} pending change request(s)."
                ),
                suggested_action=(
                    "Review and approve or reject pending changes."
                    if pending_proposals + pending_crs > 0
                    else None
                ),
            )
        )

        metrics.append(
            ScorecardMetric(
                name="high_risk_change_count",
                value=high_risk_changes,
                target=0,
                status=(
                    "pass"
                    if high_risk_changes == 0
                    else "warning"
                    if high_risk_changes <= 2
                    else "fail"
                ),
                explanation=f"{high_risk_changes} pending high-risk change(s).",
                suggested_action=(
                    "Prioritize review of high-risk pending changes."
                    if high_risk_changes > 0
                    else None
                ),
            )
        )

        # Evidence coverage metric
        if decisions_total > 0:
            ev_value = _pct(decisions_with_evidence, decisions_total)
            ev_status = _status(ev_value, 80.0, 50.0)
            ev_explanation = (
                f"{decisions_with_evidence} of {decisions_total} decisions have evidence."
            )
        else:
            ev_value = 0.0
            ev_status = "pass"
            ev_explanation = "No Decision objects in model."
        metrics.append(
            ScorecardMetric(
                name="evidence_coverage",
                value=ev_value,
                target=80.0,
                status=ev_status,
                explanation=ev_explanation,
                suggested_action="Add evidence references to decisions."
                if decisions_total > decisions_with_evidence
                else None,
            )
        )

        # SAP table coverage metric
        if sap_total > 0:
            sap_value = _pct(sap_with_attribute, sap_total)
            sap_status = _status(sap_value, 90.0, 60.0)
            sap_explanation = (
                f"{sap_with_attribute} of {sap_total} "
                f"target SAP FieldEndpoints have attribute linkage."
            )
        else:
            sap_value = 0.0
            sap_status = "pass"
            sap_explanation = "No target SAP FieldEndpoints in model."
        metrics.append(
            ScorecardMetric(
                name="sap_table_coverage",
                value=sap_value,
                target=90.0,
                status=sap_status,
                explanation=sap_explanation,
                suggested_action="Link attributes to SAP FieldEndpoints."
                if sap_total > sap_with_attribute
                else None,
            )
        )

        # Readiness level
        pass_count = sum(1 for m in metrics if m.status == "pass")
        fail_count = sum(1 for m in metrics if m.status == "fail")

        if total_objects < 10:
            readiness = "seed"
        elif fail_count > 2 or open_issues > 5 or high_risk_changes > 2:
            readiness = "draft"
        elif pass_count >= len(metrics) * 0.8:
            readiness = "ready"
        else:
            readiness = "review"

        summary_parts = [
            f"Repository '{repo_name}' has {total_objects} objects.",
            f"Readiness: {readiness}. {pass_count}/{len(metrics)} metrics pass.",
        ]
        if gaps:
            summary_parts.append(f"Top gap: {gaps[0].gap_type} ({len(gaps)} total).")

        return ScorecardReport(
            repo_name=repo_name,
            generated_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            readiness_level=readiness,
            object_count=total_objects,
            metrics=metrics,
            gaps=gaps[:max_gaps],
            summary=" ".join(summary_parts),
        )
    finally:
        conn.close()
