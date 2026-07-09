"""Sync newly created dataset profiles into the generated SQLite index."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from modelops_core.config import resolve_generated_path


def link_dataset_profile_to_index(
    repo_root: Path,
    dataset_id: str,
    profile_path: Path,
    file_name: str | None = None,
) -> str | None:
    """Mark a Dataset object in the SQLite index as profiled.

    The function looks for a Dataset row matching *dataset_id* by object ID first,
    then falls back to matching by object name (with or without the file extension).
    When a match is found, the ``profile`` field in ``frontmatter_json`` is set to
    the profile path and the change is committed.

    Args:
        repo_root: Repository root path.
        dataset_id: Identifier used when profiling (usually the file stem).
        profile_path: Path where the profile JSON was written.
        file_name: Original dataset file name, used for name-based fallback matching.

    Returns:
        The object ID of the updated Dataset, or None if no index exists or no
        matching Dataset was found.
    """
    db_path = resolve_generated_path(repo_root) / "modelops.db"
    if not db_path.exists():
        return None

    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            "SELECT id, name, frontmatter_json FROM objects WHERE type = 'Dataset'"
        ).fetchall()

        candidates: list[tuple[str, dict[str, object]]] = []
        for obj_id, _name, fm_json in rows:
            fm = json.loads(fm_json or "{}")
            candidates.append((obj_id, fm))

        # Match by object ID first.
        target_id = next((oid for oid, _ in candidates if oid == dataset_id), None)

        # Fall back to matching by object name.
        if target_id is None and file_name:
            names_to_match = {file_name, Path(file_name).stem}
            target_id = next(
                (oid for oid, fm in candidates if fm.get("name") in names_to_match),
                None,
            )

        if target_id is None:
            return None

        target_fm = next(fm for oid, fm in candidates if oid == target_id)
        target_fm["profile"] = str(profile_path.relative_to(repo_root))
        conn.execute(
            "UPDATE objects SET frontmatter_json = ? WHERE id = ?",
            (json.dumps(target_fm, default=str), target_id),
        )
        conn.commit()
        return target_id
    finally:
        conn.close()
