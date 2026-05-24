"""Streaming CSV profiler with bounded memory."""

from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ProfilingStatus:
    success: bool = True
    truncated: bool = False
    reason: str | None = None
    rows_processed: int = 0
    file_size_bytes: int = 0


@dataclass
class ColumnProfile:
    name: str
    position: int
    blank_count: int = 0
    non_blank_count: int = 0
    distinct_count: int = 0
    sample_values: list[str] = field(default_factory=list)
    inferred_type: str = "string"


@dataclass
class DatasetProfile:
    dataset_id: str
    file_path: str
    file_hash: str
    row_count: int = 0
    column_count: int = 0
    columns: list[ColumnProfile] = field(default_factory=list)
    status: ProfilingStatus = field(default_factory=ProfilingStatus)


MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB
MAX_ROWS = 500_000
MAX_COLUMNS = 1_000
SAMPLE_SIZE = 5


def _compute_file_hash(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _infer_type(values: list[str]) -> str:
    types_seen: set[str] = set()
    for v in values:
        v_stripped = v.strip()
        if v_stripped == "":
            types_seen.add("empty")
            continue
        if v_stripped.lower() in {"true", "false", "1", "0", "yes", "no"}:
            types_seen.add("boolean")
            continue
        try:
            int(v_stripped)
            types_seen.add("integer")
            continue
        except ValueError:
            pass
        try:
            float(v_stripped)
            types_seen.add("decimal")
            continue
        except ValueError:
            pass
        types_seen.add("string")

    if len(types_seen) == 1:
        return types_seen.pop()
    if "string" in types_seen:
        return "mixed"
    if {"integer", "decimal"} <= types_seen:
        return "decimal"
    return "mixed"


def profile_csv(
    csv_path: Path,
    dataset_id: str,
    max_file_size: int = MAX_FILE_SIZE_BYTES,
    max_rows: int = MAX_ROWS,
    max_columns: int = MAX_COLUMNS,
) -> DatasetProfile:
    """Profile a CSV file with bounded memory usage."""
    file_size = csv_path.stat().st_size
    if file_size > max_file_size:
        return DatasetProfile(
            dataset_id=dataset_id,
            file_path=str(csv_path),
            file_hash="",
            status=ProfilingStatus(
                success=False,
                truncated=True,
                reason=f"File size {file_size} exceeds limit {max_file_size}.",
                file_size_bytes=file_size,
            ),
        )

    file_hash = _compute_file_hash(csv_path)

    with csv_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh)
        try:
            headers = next(reader)
        except StopIteration:
            return DatasetProfile(
                dataset_id=dataset_id,
                file_path=str(csv_path),
                file_hash=file_hash,
                status=ProfilingStatus(
                    success=False,
                    truncated=True,
                    reason="Empty CSV file.",
                    file_size_bytes=file_size,
                ),
            )

        if len(headers) > max_columns:
            return DatasetProfile(
                dataset_id=dataset_id,
                file_path=str(csv_path),
                file_hash=file_hash,
                status=ProfilingStatus(
                    success=False,
                    truncated=True,
                    reason=f"Column count {len(headers)} exceeds limit {max_columns}.",
                    file_size_bytes=file_size,
                ),
            )

        columns: list[ColumnProfile] = [
            ColumnProfile(name=h, position=i + 1) for i, h in enumerate(headers)
        ]
        row_count = 0
        distinct_sets: list[set[str]] = [set() for _ in headers]

        for row in reader:
            if row_count >= max_rows:
                break
            row_count += 1
            for i, value in enumerate(row):
                if i >= len(columns):
                    break
                col = columns[i]
                if value.strip() == "":
                    col.blank_count += 1
                else:
                    col.non_blank_count += 1
                    distinct_sets[i].add(value.strip())
                    if len(col.sample_values) < SAMPLE_SIZE:
                        col.sample_values.append(value.strip())

        for i, col in enumerate(columns):
            col.distinct_count = len(distinct_sets[i])
            col.inferred_type = _infer_type(list(distinct_sets[i])[:SAMPLE_SIZE * 2])

    return DatasetProfile(
        dataset_id=dataset_id,
        file_path=str(csv_path),
        file_hash=file_hash,
        row_count=row_count,
        column_count=len(columns),
        columns=columns,
        status=ProfilingStatus(
            success=True,
            rows_processed=row_count,
            file_size_bytes=file_size,
        ),
    )
