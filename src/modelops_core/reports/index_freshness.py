"""Index freshness check service.

Compares the generated index against canonical source files using both
content hash and mtime to determine whether the index is stale.
"""

from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path


@dataclass
class IndexFreshnessReport:
    """Result of an index freshness check."""

    fresh: bool
    db_path: Path
    db_mtime: datetime | None = None
    newest_source_mtime: datetime | None = None
    reason: str | None = None
    stale_sources: list[str] = field(default_factory=list)
    stored_source_hash: str | None = None
    current_source_hash: str | None = None
    hash_mismatch: bool | None = None


def _compute_current_source_hash(model_path: Path) -> str | None:
    """Compute a deterministic hash of all canonical source files.

    Uses the same ordering and hashing logic as the index builder.
    """
    from modelops_core.repository import parse_file, scan_repository

    if not model_path.exists():
        return None

    files = scan_repository(model_path)
    if not files:
        return None

    parsed_objects = [parse_file(f) for f in files]
    hasher = hashlib.sha256()
    for obj in sorted(parsed_objects, key=lambda o: o.source_path):
        hasher.update(obj.source_path.encode("utf-8"))
        hasher.update(obj.content_hash.encode("utf-8"))
    return hasher.hexdigest()[:16]


def _read_stored_source_hash(db_path: Path) -> str | None:
    """Read the source_content_hash from the index manifest."""
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute(
            "SELECT value FROM index_manifest WHERE key = 'source_content_hash'"
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return row[0]
    except Exception:
        pass
    return None


def check_index_freshness(
    repo_root: Path,
    model_path: Path | None = None,
    generated_path: Path | None = None,
) -> IndexFreshnessReport:
    """Check whether the generated index is stale relative to canonical files.

    Uses content hash comparison as the primary signal and mtime as
    diagnostic context.

    Args:
        repo_root: Root of the model repository.
        model_path: Optional override for the canonical model directory.
        generated_path: Optional override for the generated artifacts directory.

    Returns:
        IndexFreshnessReport with freshness status and details.
    """
    from modelops_core.config import resolve_generated_path, resolve_model_path

    if model_path is None:
        model_path = resolve_model_path(repo_root)
    if generated_path is None:
        generated_path = resolve_generated_path(repo_root)

    db_path = generated_path / "modelops.db"

    # No index at all
    if not db_path.exists():
        return IndexFreshnessReport(
            fresh=False,
            db_path=db_path,
            reason="no index",
        )

    db_mtime = datetime.fromtimestamp(db_path.stat().st_mtime, tz=UTC)

    # No canonical files
    if not model_path.exists():
        return IndexFreshnessReport(
            fresh=True,
            db_path=db_path,
            db_mtime=db_mtime,
            reason="no canonical files",
        )

    canonical_files = list(model_path.rglob("*"))
    canonical_files = [f for f in canonical_files if f.is_file()]

    if not canonical_files:
        return IndexFreshnessReport(
            fresh=True,
            db_path=db_path,
            db_mtime=db_mtime,
            reason="no canonical files",
        )

    newest_source_mtime: datetime | None = None
    stale_sources: list[str] = []

    for source_file in canonical_files:
        source_mtime = datetime.fromtimestamp(
            source_file.stat().st_mtime, tz=UTC
        )
        if newest_source_mtime is None or source_mtime > newest_source_mtime:
            newest_source_mtime = source_mtime

        if source_mtime > db_mtime:
            # Store relative path for cleaner output
            try:
                rel_path = str(source_file.relative_to(repo_root))
            except ValueError:
                rel_path = str(source_file)
            stale_sources.append(rel_path)

    # Deterministic sorting
    stale_sources.sort()

    # Content-hash-based freshness check
    stored_hash = _read_stored_source_hash(db_path)
    current_hash = _compute_current_source_hash(model_path)
    hash_mismatch: bool | None = None

    if stored_hash is not None and current_hash is not None:
        hash_mismatch = stored_hash != current_hash

    # Primary signal: content hash. Fallback: mtime.
    if hash_mismatch is not None:
        is_fresh = not hash_mismatch
    else:
        is_fresh = not stale_sources

    if hash_mismatch is True:
        reason = "content hash mismatch"
    elif not is_fresh:
        reason = "stale sources detected"
    else:
        reason = None

    return IndexFreshnessReport(
        fresh=is_fresh,
        db_path=db_path,
        db_mtime=db_mtime,
        newest_source_mtime=newest_source_mtime,
        reason=reason,
        stale_sources=stale_sources,
        stored_source_hash=stored_hash,
        current_source_hash=current_hash,
        hash_mismatch=hash_mismatch,
    )
