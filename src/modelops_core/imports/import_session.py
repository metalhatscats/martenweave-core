"""Non-mutating import session provenance capture."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from modelops_core.imports.dataset_profiler import DatasetProfile


@dataclass
class ImportSession:
    """Captures provenance for a dataset import without mutating canonical files."""

    session_id: str
    file_name: str
    file_path: str
    file_size_bytes: int
    file_hash: str
    row_count: int
    column_count: int
    profile_summary: dict[str, Any] = field(default_factory=dict)
    privacy_policy_applied: bool = True
    raw_samples_included: bool = False


def create_import_session(
    csv_path: Path,
    profile: DatasetProfile,
    privacy_policy_applied: bool = True,
    raw_samples_included: bool = False,
) -> ImportSession:
    """Create an import session from a profiled CSV."""
    session_id = f"import-{uuid.uuid4().hex[:12]}"
    profile_summary = {
        "dataset_id": profile.dataset_id,
        "row_count": profile.row_count,
        "column_count": profile.column_count,
        "columns": [
            {
                "name": c.name,
                "inferred_type": c.inferred_type,
                "blank_count": c.blank_count,
                "non_blank_count": c.non_blank_count,
                "distinct_count": c.distinct_count,
            }
            for c in profile.columns
        ],
        "status": {
            "success": profile.status.success,
            "truncated": profile.status.truncated,
            "reason": profile.status.reason,
        },
    }

    return ImportSession(
        session_id=session_id,
        file_name=csv_path.name,
        file_path=str(csv_path),
        file_size_bytes=profile.status.file_size_bytes,
        file_hash=profile.file_hash,
        row_count=profile.row_count,
        column_count=profile.column_count,
        profile_summary=profile_summary,
        privacy_policy_applied=privacy_policy_applied,
        raw_samples_included=raw_samples_included,
    )
