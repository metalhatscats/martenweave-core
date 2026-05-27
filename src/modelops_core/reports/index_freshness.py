"""Index freshness check service.

Compares the generated index mtime against canonical source file mtimes
to determine whether the index is stale.
"""

from __future__ import annotations

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


def check_index_freshness(
    repo_root: Path,
    model_path: Path | None = None,
    generated_path: Path | None = None,
) -> IndexFreshnessReport:
    """Check whether the generated index is stale relative to canonical files.

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

    is_fresh = not stale_sources

    return IndexFreshnessReport(
        fresh=is_fresh,
        db_path=db_path,
        db_mtime=db_mtime,
        newest_source_mtime=newest_source_mtime,
        reason=None if is_fresh else "stale sources detected",
        stale_sources=stale_sources,
    )
