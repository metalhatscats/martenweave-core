"""SQLite index builder for canonical model objects."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from modelops_core.config import load_repo_config, resolve_generated_path, resolve_model_path
from modelops_core.errors import ResourceLimitExceeded
from modelops_core.repository import parse_file, scan_repository
from modelops_core.schemas.registry import get_relationship_classes, get_relationship_fields
from modelops_core.validation import ValidationSummary, validate_objects

_INIT_SCHEMA = """
DROP TABLE IF EXISTS objects;
DROP TABLE IF EXISTS validation_results;
DROP TABLE IF EXISTS object_relationships;
DROP TABLE IF EXISTS index_manifest;

CREATE TABLE index_manifest (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE objects (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    status TEXT NOT NULL,
    name TEXT,
    title TEXT,
    domain TEXT,
    description TEXT,
    source_file TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    frontmatter_json TEXT NOT NULL,
    body TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE validation_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    severity TEXT NOT NULL,
    code TEXT NOT NULL,
    message TEXT NOT NULL,
    object_id TEXT,
    object_type TEXT,
    source_file TEXT,
    field_path TEXT,
    details_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE object_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_object_id TEXT NOT NULL,
    relationship_type TEXT NOT NULL,
    relationship_class TEXT NOT NULL DEFAULT 'reference',
    to_object_id TEXT NOT NULL,
    source_file TEXT NOT NULL,
    confidence TEXT NOT NULL DEFAULT 'explicit'
);

CREATE TABLE tags (
    object_id TEXT NOT NULL,
    tag TEXT NOT NULL,
    PRIMARY KEY (object_id, tag)
);
"""


def _init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(_INIT_SCHEMA)


def _insert_objects(conn: sqlite3.Connection, objects: list[Any]) -> None:
    for obj in objects:
        if obj.parser_error is not None or obj.frontmatter is None:
            continue
        fm = obj.frontmatter
        obj_id = fm.get("id")
        conn.execute(
            """
            INSERT INTO objects (
                id, type, status, name, title, domain, description,
                source_file, content_hash, frontmatter_json, body,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                obj_id,
                fm.get("type"),
                fm.get("status"),
                fm.get("name"),
                fm.get("title"),
                fm.get("domain"),
                fm.get("description"),
                obj.source_path,
                obj.content_hash,
                json.dumps(fm, default=str),
                obj.body,
                fm.get("created_at"),
                fm.get("updated_at"),
            ),
        )
        tags = fm.get("tags")
        if isinstance(tags, list):
            for tag in tags:
                if isinstance(tag, str) and tag:
                    conn.execute(
                        "INSERT OR IGNORE INTO tags (object_id, tag) VALUES (?, ?)",
                        (obj_id, tag),
                    )


def _insert_validation_results(conn: sqlite3.Connection, results: list[Any]) -> None:
    for result in results:
        conn.execute(
            """
            INSERT INTO validation_results (
                severity, code, message, object_id, object_type,
                source_file, field_path, details_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(result.severity),
                result.code,
                result.message,
                result.object_id,
                result.object_type,
                result.source_file,
                result.field_path,
                json.dumps(result.details, default=str),
            ),
        )


def _insert_relationships(conn: sqlite3.Connection, objects: list[Any]) -> None:
    for obj in objects:
        if obj.parser_error is not None or obj.frontmatter is None:
            continue
        obj_id = obj.frontmatter.get("id")
        if not isinstance(obj_id, str):
            continue

        relationship_fields = get_relationship_fields()
        relationship_classes = get_relationship_classes()
        for field, rel_type in relationship_fields.items():
            value = obj.frontmatter.get(field)
            if value is None:
                continue

            refs: list[str] = []
            if isinstance(value, str):
                refs = [value]
            elif isinstance(value, list):
                refs = [str(v) for v in value if isinstance(v, str)]
            else:
                continue

            rel_class = relationship_classes.get(field, "reference")
            for ref_id in refs:
                conn.execute(
                    """
                    INSERT INTO object_relationships (
                        from_object_id, relationship_type, relationship_class,
                        to_object_id, source_file, confidence
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (obj_id, rel_type, rel_class, ref_id, obj.source_path, "explicit"),
                )


def _compute_source_hash(objects: list[Any]) -> str:
    hasher = hashlib.sha256()
    for obj in sorted(objects, key=lambda o: o.source_path):
        hasher.update(obj.source_path.encode("utf-8"))
        hasher.update(obj.content_hash.encode("utf-8"))
    return hasher.hexdigest()[:16]


def _write_manifest(
    conn: sqlite3.Connection,
    repo_root: Path,
    object_count: int,
    summary: ValidationSummary,
    source_hash: str,
) -> None:
    manifest = {
        "build_timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_repo_path": str(repo_root.resolve()),
        "object_count": str(object_count),
        "validation_status": "valid" if summary.is_valid else "invalid",
        "source_content_hash": source_hash,
    }
    conn.executemany(
        "INSERT OR REPLACE INTO index_manifest (key, value) VALUES (?, ?)",
        list(manifest.items()),
    )


def build_index(
    repo_root: Path,
    db_path: Path | None = None,
    *,
    allow_invalid: bool = False,
    export_jsonl: bool = False,
    max_objects: int | None = None,
    dry_run: bool = False,
) -> ValidationSummary:
    """Build a SQLite index from canonical repository objects.

    Rebuilds are atomic: the new index is written to a temporary file and
    swapped into place only after a successful commit.

    Args:
        repo_root: Path to the canonical model repository root.
        db_path: Path where the SQLite database will be written. If None,
            writes to ``<repo_root>/generated/modelops.db``.
        allow_invalid: If False (default), raises when validation errors exist.
        export_jsonl: If True, also writes ``search_documents.jsonl`` and
            ``lineage_edges.jsonl`` to the generated directory.
        max_objects: Maximum number of canonical objects to index. If None,
            reads from repository config defaults.
        dry_run: If True, runs validation and parsing but does not write
            the database or JSONL exports.

    Returns:
        The validation summary from the pipeline.

    Raises:
        ValueError: If validation has errors and *allow_invalid* is False.
        ResourceLimitExceeded: If the repository exceeds the object count limit.
    """
    model_path = resolve_model_path(repo_root)
    files = scan_repository(model_path)

    config = load_repo_config(repo_root)
    enabled_packs = config.enabled_domain_packs if config else None
    if max_objects is None:
        max_objects = config.resource_limits.max_index_objects if config else 10_000

    if len(files) > max_objects:
        raise ResourceLimitExceeded(
            resource="max_index_objects",
            message=(
                f"Repository contains {len(files)} canonical files, "
                f"exceeding max_index_objects limit of {max_objects}. "
                f"Increase the limit in modelops.config.yaml or split "
                f"the model into multiple repositories."
            ),
        )

    parsed_objects = [parse_file(f) for f in files]
    summary = validate_objects(parsed_objects, enabled_packs)

    if not summary.is_valid and not allow_invalid:
        raise ValueError(
            f"Validation failed with {summary.error_count} error(s). "
            f"Set allow_invalid=True to force index build."
        )

    if db_path is None:
        db_path = resolve_generated_path(repo_root) / "modelops.db"

    if dry_run:
        return summary

    source_hash = _compute_source_hash(parsed_objects)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    temp_db = db_path.with_suffix(".db.tmp")

    conn = sqlite3.connect(str(temp_db))
    try:
        _init_schema(conn)
        _insert_objects(conn, parsed_objects)
        _insert_validation_results(conn, summary.results)
        _insert_relationships(conn, parsed_objects)
        _write_manifest(conn, repo_root, len(parsed_objects), summary, source_hash)
        conn.commit()
    except Exception:
        conn.close()
        if temp_db.exists():
            temp_db.unlink()
        raise
    finally:
        if conn:
            conn.close()

    os.replace(str(temp_db), str(db_path))

    if export_jsonl:
        from modelops_core.index.lineage_edges import export_lineage_jsonl
        from modelops_core.index.search_documents import export_search_jsonl

        generated_path = resolve_generated_path(repo_root)
        generated_path.mkdir(parents=True, exist_ok=True)
        export_search_jsonl(db_path, generated_path / "search_documents.jsonl")
        export_lineage_jsonl(db_path, generated_path / "lineage_edges.jsonl")

    return summary
