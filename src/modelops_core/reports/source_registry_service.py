"""Source registry for tracking external inputs to the model."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from modelops_core.schemas.source_registry import SourceEntry


class SourceRegistryService:
    """Append-only source registry backed by JSONL.

    Writes to ``<repo_root>/generated/source_registry.jsonl``.
    """

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root
        self.registry_path = repo_root / "generated" / "source_registry.jsonl"

    def register(self, entry: SourceEntry) -> str:
        """Append a source entry to the registry.

        If an entry with the same ``source_id`` already exists, a new
        record is still appended (history is preserved). The latest
        record for a given ``source_id`` is considered current.

        Returns:
            The ``source_id`` that was registered.
        """
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        with self.registry_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry.to_dict(), default=str) + "\n")
        return entry.source_id

    def read_entries(self) -> list[SourceEntry]:
        """Read all entries from the registry.

        Returns:
            List of SourceEntry objects in append order.
        """
        if not self.registry_path.exists():
            return []

        entries: list[SourceEntry] = []
        with self.registry_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    entries.append(SourceEntry.from_dict(data))
                except (json.JSONDecodeError, KeyError):
                    continue
        return entries

    def get_latest_by_id(self, source_id: str) -> SourceEntry | None:
        """Return the most recent entry for a given ``source_id``."""
        entries = self.read_entries()
        matches = [e for e in entries if e.source_id == source_id]
        if not matches:
            return None
        # Sort by registered_at descending; fall back to last-in-file
        matches.sort(key=lambda e: e.registered_at, reverse=True)
        return matches[0]

    def list_sources(self) -> list[dict[str, Any]]:
        """Return deduplicated latest state of all sources."""
        entries = self.read_entries()
        by_id: dict[str, SourceEntry] = {}
        for e in entries:
            existing = by_id.get(e.source_id)
            if existing is None or e.registered_at > existing.registered_at:
                by_id[e.source_id] = e
        return [e.to_dict() for e in by_id.values()]


def _now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def register_dataset_source(
    service: SourceRegistryService,
    dataset_id: str,
    file_path: Path,
    file_hash: str,
    row_count: int,
    column_count: int,
) -> str:
    """Convenience helper to register a dataset profile source."""
    entry = SourceEntry(
        source_id=dataset_id,
        source_type="dataset_profile",
        display_name=f"Dataset profile: {dataset_id}",
        file_path=str(file_path),
        file_hash=file_hash,
        registered_at=_now_iso(),
        last_seen_at=_now_iso(),
        status="ok",
        metadata={
            "row_count": row_count,
            "column_count": column_count,
        },
    )
    return service.register(entry)


def register_import_source(
    service: SourceRegistryService,
    proposal_id: str,
    source_path: Path,
    operations_count: int,
    warnings_count: int,
) -> str:
    """Convenience helper to register a model-sheet import source."""
    entry = SourceEntry(
        source_id=proposal_id,
        source_type="model_sheet_import",
        display_name=f"Import: {source_path.name}",
        file_path=str(source_path),
        registered_at=_now_iso(),
        last_seen_at=_now_iso(),
        status="ok" if warnings_count == 0 else "warning",
        metadata={
            "operations_count": operations_count,
            "warnings_count": warnings_count,
        },
    )
    return service.register(entry)
