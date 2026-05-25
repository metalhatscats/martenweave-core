"""Export canonical model objects to CSV and XLSX."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from modelops_core.errors import ResourceLimitExceeded
from modelops_core.repository import parse_file, scan_repository

_COMMON_COLUMNS = ("id", "type", "status", "name", "title", "domain", "description")


def _flatten_value(value: Any) -> str:
    """Flatten a frontmatter value to a string safe for tabular output."""
    if value is None:
        return ""
    if isinstance(value, list):
        return "; ".join(str(v) for v in value)
    if isinstance(value, dict):
        return str(value)
    return str(value)


def _collect_objects(repo_model_path: Path) -> dict[str, list[dict[str, Any]]]:
    """Scan and parse all canonical objects, grouped by type."""
    files = scan_repository(repo_model_path)
    objects_by_type: dict[str, list[dict[str, Any]]] = {}

    for file_path in files:
        parsed = parse_file(file_path)
        if parsed.parser_error or not parsed.frontmatter:
            continue
        fm = dict(parsed.frontmatter)
        obj_type = str(fm.get("type", "Unknown"))
        fm["source_file"] = Path(parsed.source_path).name
        objects_by_type.setdefault(obj_type, []).append(fm)

    return objects_by_type


def _build_columns(objects: list[dict[str, Any]]) -> list[str]:
    """Determine column order for a set of objects."""
    extra_keys: set[str] = set()
    for obj in objects:
        extra_keys.update(obj.keys())
    extra_keys.discard("source_file")
    for col in _COMMON_COLUMNS:
        extra_keys.discard(col)
    return list(_COMMON_COLUMNS) + sorted(extra_keys) + ["source_file"]


def export_model_csv(
    repo_model_path: Path,
    output_dir: Path | None = None,
    max_objects: int | None = None,
) -> list[Path]:
    """Export canonical objects to one CSV file per type.

    Args:
        repo_model_path: Path to the model directory.
        output_dir: Directory to write CSV files. Defaults to
            ``repo_model_path.parent / "generated" / "exports" / "csv"``.
        max_objects: Maximum objects per type. If exceeded, raises
            ``ResourceLimitExceeded``.

    Returns:
        List of written file paths.

    Raises:
        ResourceLimitExceeded: If any object type exceeds the limit.
    """
    if output_dir is None:
        output_dir = repo_model_path.parent / "generated" / "exports" / "csv"
    output_dir.mkdir(parents=True, exist_ok=True)

    objects_by_type = _collect_objects(repo_model_path)
    if max_objects is not None:
        for obj_type, objects in objects_by_type.items():
            if len(objects) > max_objects:
                raise ResourceLimitExceeded(
                    resource="max_export_objects",
                    message=(
                        f"Type '{obj_type}' has {len(objects)} objects, "
                        f"exceeding max_export_objects limit of {max_objects}. "
                        f"Increase the limit or filter by type."
                    ),
                )
    written: list[Path] = []

    for obj_type, objects in objects_by_type.items():
        safe_name = obj_type.replace(" ", "_").lower()
        file_path = output_dir / f"{safe_name}.csv"
        columns = _build_columns(objects)

        with file_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            for obj in objects:
                row = {col: _flatten_value(obj.get(col)) for col in columns}
                writer.writerow(row)

        written.append(file_path)

    return written


def export_model_xlsx(
    repo_model_path: Path,
    output_path: Path | None = None,
    max_objects: int | None = None,
) -> Path:
    """Export canonical objects to one XLSX workbook with a sheet per type.

    Args:
        repo_model_path: Path to the model directory.
        output_path: Path for the workbook. Defaults to
            ``repo_model_path.parent / "generated" / "exports" / "model.xlsx"``.
        max_objects: Maximum objects per sheet. If exceeded, raises
            ``ResourceLimitExceeded``.

    Returns:
        Path to the written workbook.

    Raises:
        ResourceLimitExceeded: If any object type exceeds the limit.
    """
    try:
        from openpyxl import Workbook
        from openpyxl.utils import get_column_letter
    except ImportError as exc:
        raise RuntimeError(
            "openpyxl is required for XLSX export. Install it with: pip install openpyxl"
        ) from exc

    if output_path is None:
        output_path = repo_model_path.parent / "generated" / "exports" / "model.xlsx"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    objects_by_type = _collect_objects(repo_model_path)
    if max_objects is not None:
        for obj_type, objects in objects_by_type.items():
            if len(objects) > max_objects:
                raise ResourceLimitExceeded(
                    resource="max_export_objects",
                    message=(
                        f"Type '{obj_type}' has {len(objects)} objects, "
                        f"exceeding max_export_objects limit of {max_objects}. "
                        f"Increase the limit or filter by type."
                    ),
                )
    wb = Workbook()
    # Remove default sheet; we'll add one per type
    wb.remove(wb.active)

    for obj_type, objects in objects_by_type.items():
        safe_name = obj_type.replace(" ", "_")[:31]  # Excel sheet name limit
        ws = wb.create_sheet(title=safe_name)
        columns = _build_columns(objects)

        # Header row
        for col_idx, col_name in enumerate(columns, start=1):
            ws.cell(row=1, column=col_idx, value=col_name)

        # Data rows
        for row_idx, obj in enumerate(objects, start=2):
            for col_idx, col_name in enumerate(columns, start=1):
                ws.cell(row=row_idx, column=col_idx, value=_flatten_value(obj.get(col_name)))

        # Auto-size columns (rough heuristic)
        for col_idx, col_name in enumerate(columns, start=1):
            max_len = max(len(col_name), 12)
            letter = get_column_letter(col_idx)
            ws.column_dimensions[letter].width = min(max_len + 2, 60)

    wb.save(output_path)
    return output_path
