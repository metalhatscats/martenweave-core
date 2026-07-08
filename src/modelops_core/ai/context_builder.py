"""Deterministic AI context builder using the SQLite index."""

from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from modelops_core.trace.trace_service import trace_object

# Default budgets per workflow type
_DEFAULT_BUDGETS: dict[str, dict[str, int]] = {
    "file-to-model": {"max_objects": 50, "max_relationships": 100, "max_tokens": 8000},
    "chat-to-model": {"max_objects": 30, "max_relationships": 60, "max_tokens": 4000},
    "trace-explanation": {"max_objects": 20, "max_relationships": 40, "max_tokens": 4000},
    "impact-explanation": {"max_objects": 20, "max_relationships": 40, "max_tokens": 4000},
    "metadata-gap-suggestion": {"max_objects": 40, "max_relationships": 80, "max_tokens": 6000},
    "lov-rule-suggestion": {"max_objects": 10, "max_relationships": 20, "max_tokens": 4000},
    "proposal-review": {"max_objects": 40, "max_relationships": 80, "max_tokens": 6000},
}


@dataclass
class ContextBundle:
    """A scoped, compacted, redacted bundle of model context for AI workflows."""

    bundle_id: str
    workflow: str
    included_objects: list[dict[str, Any]] = field(default_factory=list)
    included_sources: list[dict[str, Any]] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    relationship_refs: list[dict[str, Any]] = field(default_factory=list)
    excluded_sections: list[str] = field(default_factory=list)
    token_budget: int = 4000
    size_budget: int = 0
    redaction_policy: str = "summary_only"
    created_at: str = ""
    warnings: list[str] = field(default_factory=list)
    validation_summary: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    def to_metadata(self) -> dict[str, Any]:
        """Return metadata for telemetry or proposal tracking."""
        return {
            "bundle_id": self.bundle_id,
            "workflow": self.workflow,
            "object_count": len(self.included_objects),
            "relationship_count": len(self.relationship_refs),
            "excluded_sections": self.excluded_sections,
            "token_budget": self.token_budget,
            "redaction_policy": self.redaction_policy,
            "created_at": self.created_at,
            "warnings": self.warnings,
        }

    def estimate_size(self) -> int:
        """Rough size estimate in characters."""
        return len(json.dumps(self.included_objects, default=str)) + len(
            json.dumps(self.relationship_refs, default=str)
        )


def _fetch_object(conn: sqlite3.Connection, object_id: str) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT id, type, status, name, title, domain, description, "
        "source_file, frontmatter_json FROM objects WHERE id = ?",
        (object_id,),
    ).fetchone()
    if row is None:
        return None
    return {
        "object_id": row["id"],
        "object_type": row["type"],
        "status": row["status"],
        "name": row["name"],
        "title": row["title"],
        "domain": row["domain"],
        "description": row["description"],
        "source_file": row["source_file"],
    }


def _fetch_validation_summary(conn: sqlite3.Connection, object_ids: list[str]) -> dict[str, Any]:
    if not object_ids:
        return {"errors": 0, "warnings": 0, "details": []}
    placeholders = ",".join("?" * len(object_ids))
    rows = conn.execute(
        f"SELECT severity, code, message, object_id FROM validation_results "
        f"WHERE object_id IN ({placeholders})",
        tuple(object_ids),
    ).fetchall()
    errors = [r for r in rows if r["severity"] == "ERROR"]
    warnings = [r for r in rows if r["severity"] == "WARNING"]
    return {
        "errors": len(errors),
        "warnings": len(warnings),
        "details": [
            {
                "severity": r["severity"],
                "code": r["code"],
                "message": r["message"],
                "object_id": r["object_id"],
            }
            for r in rows
        ],
    }


def _fetch_redacted_sources(
    db_path: Path,
    object_ids: list[str],
) -> list[dict[str, Any]]:
    """Return redacted source metadata for dataset sources linked to included objects.

    Uses the source_registry.jsonl next to the database as a lightweight heuristic.
    Only metadata fields are returned; raw sample values are never included.
    """
    registry_path = db_path.parent / "source_registry.jsonl"
    if not registry_path.exists():
        return []

    try:
        raw = registry_path.read_text(encoding="utf-8")
    except OSError:
        return []

    object_id_set = set(object_ids)
    sources: list[dict[str, Any]] = []
    seen: set[str] = set()

    for line in raw.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue

        source_id = entry.get("source_id")
        if not source_id or source_id in seen:
            continue

        # Link source if its source_id matches an included object id. Fallback:
        # include all dataset_profile sources when the registry is present (heuristic).
        source_type = entry.get("source_type", "")
        if source_id not in object_id_set and source_type != "dataset_profile":
            continue

        metadata = entry.get("metadata", {}) or {}
        redacted = {
            "source_id": source_id,
            "dataset_id": source_id,
            "column_count": metadata.get("column_count"),
            "row_count": metadata.get("row_count"),
            "inferred_types": metadata.get("inferred_types", []),
        }
        sources.append(redacted)
        seen.add(source_id)

    return sources


def _compact_objects(
    objects: list[dict[str, Any]],
    max_objects: int,
    validation_summary: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Sort and truncate objects to fit budget. Return (kept, warnings)."""
    warnings: list[str] = []

    # Priority: objects with validation errors first, then by type priority
    type_priority = {
        "Attribute": 0,
        "FieldEndpoint": 1,
        "Mapping": 2,
        "AttributeUsage": 3,
        "ValidationRule": 4,
        "ValueList": 5,
        "ValueMapping": 6,
        "BusinessEntity": 7,
        "MasterDataDomain": 8,
    }

    error_counts: dict[str, int] = {}
    if validation_summary:
        for detail in validation_summary.get("details", []):
            if detail.get("severity") == "ERROR" and detail.get("object_id"):
                error_counts[detail["object_id"]] = error_counts.get(detail["object_id"], 0) + 1

    def sort_key(obj: dict[str, Any]) -> tuple[int, int, int]:
        error_count = error_counts.get(obj.get("object_id", ""), 0)
        # Negative error count so objects with more errors sort first.
        return (-error_count, type_priority.get(obj.get("object_type", ""), 99), 0)

    sorted_objs = sorted(objects, key=sort_key)
    kept = sorted_objs[:max_objects]
    excluded = len(sorted_objs) - len(kept)
    if excluded > 0:
        warnings.append(f"Excluded {excluded} objects over max_objects budget.")
    return kept, warnings


def _strip_descriptions(objects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove description fields to save space."""
    result = []
    for obj in objects:
        stripped = {k: v for k, v in obj.items() if k != "description"}
        result.append(stripped)
    return result


def build_context_bundle(
    db_path: Path,
    workflow: str,
    target_object_id: str | None = None,
    target_object_ids: list[str] | None = None,
    extra_query: dict[str, Any] | None = None,
    token_budget: int | None = None,
    max_objects: int | None = None,
    max_relationships: int | None = None,
    max_depth: int = 2,
    redaction_policy: str = "summary_only",
) -> ContextBundle:
    """Build a deterministic context bundle for an AI workflow.

    Args:
        db_path: Path to the SQLite index database.
        workflow: Workflow type (e.g. ``chat-to-model``).
        target_object_id: Primary object of interest.
        target_object_ids: Additional objects to include.
        extra_query: Optional structured query to select more objects.
        token_budget: Override default token budget.
        max_objects: Override default max objects.
        max_relationships: Override default max relationships.
        max_depth: Max BFS depth for relationship expansion.
        redaction_policy: ``summary_only`` strips raw data.
    """
    if not db_path.exists():
        return ContextBundle(
            bundle_id=str(uuid.uuid4()),
            workflow=workflow,
            warnings=["Index database not found. Empty context bundle."],
        )

    defaults = _DEFAULT_BUDGETS.get(workflow, _DEFAULT_BUDGETS["chat-to-model"])
    token_budget = token_budget or defaults["max_tokens"]
    max_objects = max_objects or defaults["max_objects"]
    max_relationships = max_relationships or defaults["max_relationships"]

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    seed_ids: set[str] = set()
    if target_object_id:
        seed_ids.add(target_object_id)
    if target_object_ids:
        seed_ids.update(target_object_ids)

    # Layer 1: Exact lookup
    all_objects: list[dict[str, Any]] = []
    for obj_id in seed_ids:
        obj = _fetch_object(conn, obj_id)
        if obj:
            all_objects.append(obj)

    # Layer 2: Structured query
    if extra_query:
        obj_type = extra_query.get("type")
        domain = extra_query.get("domain")
        status = extra_query.get("status", "active")
        conditions: list[str] = []
        params: list[Any] = []
        if obj_type:
            conditions.append("type = ?")
            params.append(obj_type)
        if domain:
            conditions.append("domain = ?")
            params.append(domain)
        if status:
            conditions.append("status = ?")
            params.append(status)
        if conditions:
            where = " AND ".join(conditions)
            rows = conn.execute(
                f"SELECT id, type, status, name, title, domain, description, "
                f"source_file FROM objects WHERE {where} LIMIT 100",
                tuple(params),
            ).fetchall()
            for row in rows:
                obj = {
                    "object_id": row["id"],
                    "object_type": row["type"],
                    "status": row["status"],
                    "name": row["name"],
                    "title": row["title"],
                    "domain": row["domain"],
                    "description": row["description"],
                    "source_file": row["source_file"],
                }
                if obj["object_id"] not in {o["object_id"] for o in all_objects}:
                    all_objects.append(obj)

    # Layer 3: Relationship expansion via trace (one call per seed)
    related_ids: set[str] = set()
    relationship_refs: list[dict[str, Any]] = []
    for obj_id in seed_ids:
        trace_result = trace_object(db_path, obj_id, max_depth=max_depth, direction="both")
        for node in trace_result.nodes:
            if node.object_id not in seed_ids:
                related_ids.add(node.object_id)
        for edge in trace_result.edges:
            relationship_refs.append(
                {
                    "from_object_id": edge.from_object_id,
                    "to_object_id": edge.to_object_id,
                    "relationship_type": edge.relationship_type,
                    "direction": edge.direction,
                }
            )
            related_ids.add(edge.from_object_id)
            related_ids.add(edge.to_object_id)

    for rel_id in related_ids:
        if rel_id not in {o["object_id"] for o in all_objects}:
            obj = _fetch_object(conn, rel_id)
            if obj:
                all_objects.append(obj)

    evidence_refs = [o["object_id"] for o in all_objects]
    validation_summary = _fetch_validation_summary(conn, evidence_refs)
    conn.close()

    # Compaction: truncate to max_objects
    kept_objects, warnings = _compact_objects(all_objects, max_objects, validation_summary)

    # If still over a rough size budget, strip descriptions
    excluded_sections: list[str] = []
    rough_size = sum(len(json.dumps(o, default=str)) for o in kept_objects) + sum(
        len(json.dumps(r, default=str)) for r in relationship_refs
    )
    if rough_size > token_budget * 2:  # rough chars-to-tokens ratio
        kept_objects = _strip_descriptions(kept_objects)
        excluded_sections.append("description")
        warnings.append("Stripped descriptions to fit size budget.")

    # Truncate relationships
    if len(relationship_refs) > max_relationships:
        excluded_count = len(relationship_refs) - max_relationships
        relationship_refs = relationship_refs[:max_relationships]
        warnings.append(f"Excluded {excluded_count} relationships over budget.")

    evidence_refs = [o["object_id"] for o in kept_objects]

    # Redaction: never include raw dataset samples
    included_sources: list[dict[str, Any]] = []
    if redaction_policy != "summary_only":
        included_sources = _fetch_redacted_sources(db_path, evidence_refs)

    bundle = ContextBundle(
        bundle_id=str(uuid.uuid4()),
        workflow=workflow,
        included_objects=kept_objects,
        included_sources=included_sources,
        evidence_refs=evidence_refs,
        relationship_refs=relationship_refs,
        excluded_sections=excluded_sections,
        token_budget=token_budget,
        size_budget=rough_size,
        redaction_policy=redaction_policy,
        warnings=warnings,
        validation_summary=validation_summary,
    )

    # Final fallback: if still oversized, return summary-only
    if bundle.estimate_size() > token_budget * 3:
        bundle.warnings.append(
            "Context exceeds budget even after compaction. Returning summary only."
        )
        bundle.included_objects = [
            {
                "object_id": o["object_id"],
                "object_type": o.get("object_type"),
                "name": o.get("name"),
            }
            for o in kept_objects[:20]
        ]
        bundle.relationship_refs = []
        bundle.excluded_sections.extend(["relationships", "metadata"])

    return bundle
