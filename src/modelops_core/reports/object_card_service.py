"""Object card service: compact, factual context for a single canonical object."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from modelops_core.impact.impact_service import generate_impact_report
from modelops_core.reports.index_freshness import check_index_freshness
from modelops_core.trace.trace_service import trace_object


@dataclass
class ObjectCard:
    """Compact context card for one canonical object."""

    object_id: str
    object_type: str
    status: str
    name: str | None = None
    title: str | None = None
    domain: str | None = None
    description: str | None = None
    source_file: str = ""
    frontmatter: dict[str, Any] = field(default_factory=dict)
    body: str | None = None
    stale_index: bool = False
    stale_reason: str | None = None
    validation_results: list[dict[str, Any]] = field(default_factory=list)
    incoming: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    outgoing: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    open_issues: list[dict[str, Any]] = field(default_factory=list)
    decisions: list[dict[str, Any]] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    impact: dict[str, Any] = field(default_factory=dict)
    trace: dict[str, Any] = field(default_factory=dict)


def _load_object(conn: sqlite3.Connection, object_id: str) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT id, type, status, name, title, domain, description, "
        "source_file, frontmatter_json, body FROM objects WHERE id = ?",
        (object_id,),
    ).fetchone()
    if row is None:
        return None
    return {
        "id": row[0],
        "type": row[1],
        "status": row[2],
        "name": row[3],
        "title": row[4],
        "domain": row[5],
        "description": row[6],
        "source_file": row[7],
        "frontmatter": json.loads(row[8] or "{}"),
        "body": row[9],
    }


def _load_relationships(
    conn: sqlite3.Connection, object_id: str
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    """Return (incoming, outgoing) relationships grouped by relationship_type."""
    incoming: dict[str, list[dict[str, Any]]] = {}
    outgoing: dict[str, list[dict[str, Any]]] = {}

    rows = conn.execute(
        "SELECT from_object_id, to_object_id, relationship_type, relationship_class "
        "FROM object_relationships WHERE from_object_id = ? OR to_object_id = ?",
        (object_id, object_id),
    ).fetchall()

    ids = {oid for row in rows for oid in (row[0], row[1])}
    names: dict[str, dict[str, str | None]] = {}
    if ids:
        placeholders = ", ".join("?" * len(ids))
        for row in conn.execute(
            f"SELECT id, type, name FROM objects WHERE id IN ({placeholders})",
            tuple(ids),
        ).fetchall():
            names[row[0]] = {"type": row[1], "name": row[2]}

    for from_id, to_id, rel_type, rel_class in rows:
        target = {"object_id": to_id, **names.get(to_id, {})}
        source = {"object_id": from_id, **names.get(from_id, {})}
        if from_id == object_id:
            outgoing.setdefault(rel_type, []).append({**target, "relationship_class": rel_class})
        if to_id == object_id:
            incoming.setdefault(rel_type, []).append({**source, "relationship_class": rel_class})

    return incoming, outgoing


def _load_validation_results(conn: sqlite3.Connection, object_id: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT severity, code, message, field_path, details_json "
        "FROM validation_results WHERE object_id = ? AND severity IN ('ERROR', 'WARNING')",
        (object_id,),
    ).fetchall()
    return [
        {
            "severity": severity,
            "code": code,
            "message": message,
            "field_path": field_path,
            "details": json.loads(details_json or "{}"),
        }
        for severity, code, message, field_path, details_json in rows
    ]


def _load_open_issues_and_decisions(
    conn: sqlite3.Connection, object_id: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Find Issue/Decision objects that reference the target object."""
    open_issues: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []

    # Direct references via object_relationships (affected_object, etc.)
    rows = conn.execute(
        "SELECT from_object_id, relationship_type FROM object_relationships WHERE to_object_id = ?",
        (object_id,),
    ).fetchall()
    related_ids = {from_id for from_id, _ in rows}

    # Also include objects that mention this object in frontmatter evidence/affected_object.
    # This is a lightweight heuristic; exact references are already in object_relationships.
    for row in conn.execute(
        "SELECT id, type, status, name, frontmatter_json FROM objects "
        "WHERE type IN ('Issue', 'Decision') AND status IN ('active', 'open', 'draft')"
    ).fetchall():
        obj_id, obj_type, status, name, fm_json = row
        fm = json.loads(fm_json or "{}")
        affected = fm.get("affected_object") or fm.get("affected_objects") or []
        if isinstance(affected, str):
            affected = [affected]
        if obj_id in related_ids or object_id in affected:
            entry = {"object_id": obj_id, "status": status, "name": name}
            if obj_type == "Issue":
                entry["severity"] = fm.get("severity")
                open_issues.append(entry)
            else:
                entry["evidence"] = fm.get("evidence")
                decisions.append(entry)

    return open_issues, decisions


def _extract_evidence(frontmatter: dict[str, Any]) -> list[str]:
    """Extract evidence references from frontmatter."""
    evidence: list[str] = []
    value = frontmatter.get("evidence")
    if isinstance(value, str) and value:
        evidence.append(value)
    elif isinstance(value, list):
        evidence.extend(str(v) for v in value if v)
    return evidence


def generate_object_card(
    repo_root: Path,
    object_id: str,
    db_path: Path | None = None,
) -> ObjectCard:
    """Build an ObjectCard from the SQLite index."""
    if db_path is None:
        from modelops_core.config import resolve_generated_path

        db_path = resolve_generated_path(repo_root) / "modelops.db"

    if not db_path.exists():
        return ObjectCard(
            object_id=object_id,
            object_type="Unknown",
            status="unknown",
        )

    stale = False
    stale_reason: str | None = None
    try:
        freshness = check_index_freshness(repo_root)
        if not freshness.fresh:
            stale = True
            stale_reason = freshness.reason
    except Exception as exc:
        stale_reason = f"Could not determine freshness: {exc}"

    conn = sqlite3.connect(str(db_path))
    try:
        obj = _load_object(conn, object_id)
        if obj is None:
            return ObjectCard(
                object_id=object_id,
                object_type="Unknown",
                status="unknown",
                stale_index=stale,
                stale_reason=stale_reason,
            )

        incoming, outgoing = _load_relationships(conn, object_id)
        validation_results = _load_validation_results(conn, object_id)
        open_issues, decisions = _load_open_issues_and_decisions(conn, object_id)
    finally:
        conn.close()

    frontmatter = obj["frontmatter"]
    evidence = _extract_evidence(frontmatter)

    impact = generate_impact_report(db_path, object_id, max_depth=2, direction="both")
    impact_summary = {
        "affected_object_count": len(impact.affected_objects),
        "downstream_count": len(
            [a for a in impact.affected_objects if a.direction == "downstream"]
        ),
        "upstream_count": len([a for a in impact.affected_objects if a.direction == "upstream"]),
    }

    trace = trace_object(db_path, object_id, max_depth=3, direction="both")
    trace_summary = {
        "upstream_ids": sorted({n.object_id for n in trace.upstream}),
        "downstream_ids": sorted({n.object_id for n in trace.downstream}),
    }

    return ObjectCard(
        object_id=obj["id"],
        object_type=obj["type"],
        status=obj["status"],
        name=obj["name"],
        title=obj["title"],
        domain=obj["domain"],
        description=obj["description"],
        source_file=obj["source_file"],
        frontmatter=frontmatter,
        body=obj["body"],
        stale_index=stale,
        stale_reason=stale_reason,
        validation_results=validation_results,
        incoming=incoming,
        outgoing=outgoing,
        open_issues=open_issues,
        decisions=decisions,
        evidence=evidence,
        impact=impact_summary,
        trace=trace_summary,
    )


def object_card_to_dict(card: ObjectCard) -> dict[str, Any]:
    """Convert an ObjectCard to a JSON-serializable dict."""
    return {
        "object_id": card.object_id,
        "object_type": card.object_type,
        "status": card.status,
        "name": card.name,
        "title": card.title,
        "domain": card.domain,
        "description": card.description,
        "source_file": card.source_file,
        "stale_index": card.stale_index,
        "stale_reason": card.stale_reason,
        "validation_results": card.validation_results,
        "incoming_relationships": card.incoming,
        "outgoing_relationships": card.outgoing,
        "open_issues": card.open_issues,
        "decisions": card.decisions,
        "evidence": card.evidence,
        "impact": card.impact,
        "trace": card.trace,
    }
