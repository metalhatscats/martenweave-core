"""Pilot input privacy preflight checks.

Inspects mapping workbooks, datasets, evidence notes, and validation reports
before they are used in a pilot assessment. The default mode is metadata-only:
raw row values are not written to the report unless explicitly requested.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from modelops_core.guardrails.secrets import scan_file, scan_text
from modelops_core.imports.dataset_profiler import profile_csv, profile_xlsx

MAX_SCAN_CELLS = 5_000

SENSITIVE_COLUMN_TERMS = {
    "account",
    "address",
    "card",
    "credential",
    "email",
    "iban",
    "name",
    "password",
    "phone",
    "secret",
    "ssn",
    "token",
}


def _sensitive_column_warnings(columns: list[str]) -> list[str]:
    warnings: list[str] = []
    seen: set[str] = set()
    for col in columns:
        low = col.lower()
        for term in SENSITIVE_COLUMN_TERMS:
            if term in low and col not in seen:
                warnings.append(f"Column '{col}' may contain sensitive data ('{term}').")
                seen.add(col)
                break
    return warnings


def _inspect_text(path: Path) -> dict[str, Any]:
    size = path.stat().st_size
    findings = scan_file(path)
    warnings: list[str] = []
    if findings:
        warnings.append(f"{len(findings)} potential secret/pattern match(es).")
    return {
        "path": str(path),
        "file_type": path.suffix.lstrip(".").lower() or "text",
        "size_bytes": size,
        "status": "warning" if warnings else "allowed",
        "warnings": warnings,
        "secret_findings_count": len(findings),
    }


def _inspect_csv(path: Path) -> dict[str, Any]:
    profile = profile_csv(path, dataset_id=path.name)
    size = profile.status.file_size_bytes or path.stat().st_size
    columns = [c.name for c in profile.columns]
    warnings = _sensitive_column_warnings(columns)
    findings = scan_file(path)
    if findings:
        warnings.append(f"{len(findings)} potential secret/pattern match(es).")

    status = "blocked"
    if profile.status.success:
        status = "warning" if warnings else "allowed"

    result: dict[str, Any] = {
        "path": str(path),
        "file_type": "csv",
        "size_bytes": size,
        "status": status,
        "warnings": warnings,
        "secret_findings_count": len(findings),
        "row_count": profile.row_count,
        "column_count": profile.column_count,
        "columns": columns,
    }
    if not profile.status.success:
        result["reason"] = profile.status.reason
    return result


def _inspect_xlsx(path: Path) -> dict[str, Any]:
    try:
        from openpyxl import load_workbook
    except ImportError as exc:
        raise RuntimeError("openpyxl is required for XLSX preflight.") from exc

    profile = profile_xlsx(path, dataset_id=path.name)
    if not profile.status.success:
        return {
            "path": str(path),
            "file_type": "xlsx",
            "size_bytes": profile.status.file_size_bytes or path.stat().st_size,
            "status": "blocked",
            "warnings": [],
            "secret_findings_count": 0,
            "reason": profile.status.reason,
        }

    wb_meta = load_workbook(path, data_only=True, read_only=True)
    sheet_names = list(wb_meta.sheetnames)
    hidden_sheets = [name for name in sheet_names if wb_meta[name].sheet_state != "visible"]
    external_links: list[str] = []
    for link in getattr(wb_meta, "external_links", []) or []:
        target = getattr(link, "Target", None) or str(link)
        if target:
            external_links.append(target)
    wb_meta.close()

    warnings: list[str] = []
    if hidden_sheets:
        warnings.append(f"Hidden sheet(s): {', '.join(hidden_sheets)}.")
    if external_links:
        warnings.append(f"External link(s): {', '.join(external_links)}.")

    all_columns: list[str] = []
    sheet_metadata: list[dict[str, Any]] = []
    for sheet in profile.sheets:
        cols = [c.name for c in sheet.columns]
        all_columns.extend(cols)
        sheet_metadata.append(
            {
                "name": sheet.sheet_name,
                "row_count": sheet.row_count,
                "column_count": sheet.column_count,
                "columns": cols,
            }
        )
    warnings.extend(_sensitive_column_warnings(all_columns))

    formula_count = 0
    try:
        wb_formula = load_workbook(path, data_only=False, read_only=True)
        for sheet_name in wb_formula.sheetnames:
            ws = wb_formula[sheet_name]
            for row in ws.iter_rows(min_row=1):
                for cell in row:
                    if isinstance(cell.value, str) and cell.value.startswith("="):
                        formula_count += 1
        wb_formula.close()
    except Exception:  # pragma: no cover - best effort
        pass
    if formula_count:
        warnings.append(f"{formula_count} formula cell(s) present.")

    secret_findings: list[Any] = []
    cells_scanned = 0
    try:
        wb_values = load_workbook(path, data_only=True, read_only=True)
        value_lines: list[str] = []
        for sheet_name in wb_values.sheetnames:
            ws = wb_values[sheet_name]
            for row in ws.iter_rows(values_only=True):
                for value in row:
                    if value is None:
                        continue
                    text = str(value).strip()
                    if text:
                        value_lines.append(text)
                        cells_scanned += 1
                    if cells_scanned >= MAX_SCAN_CELLS:
                        break
                if cells_scanned >= MAX_SCAN_CELLS:
                    break
            if cells_scanned >= MAX_SCAN_CELLS:
                break
        wb_values.close()
        if value_lines:
            secret_findings = scan_text("\n".join(value_lines))
    except Exception:  # pragma: no cover - best effort
        pass
    if secret_findings:
        warnings.append(f"{len(secret_findings)} potential secret/pattern match(es).")

    status = "warning" if warnings else "allowed"
    return {
        "path": str(path),
        "file_type": "xlsx",
        "size_bytes": profile.status.file_size_bytes or path.stat().st_size,
        "status": status,
        "warnings": warnings,
        "secret_findings_count": len(secret_findings),
        "sheet_names": sheet_names,
        "sheets": sheet_metadata,
        "hidden_sheets": hidden_sheets,
        "external_links": external_links,
        "formula_count": formula_count,
    }


def inspect_file(path: Path) -> dict[str, Any]:
    """Inspect a single pilot input file and return a metadata result."""
    suffix = path.suffix.lower()
    if suffix == ".xlsx":
        return _inspect_xlsx(path)
    if suffix == ".csv":
        return _inspect_csv(path)
    if suffix in {".md", ".txt"}:
        return _inspect_text(path)
    return {
        "path": str(path),
        "file_type": suffix.lstrip(".") or "unknown",
        "size_bytes": path.stat().st_size,
        "status": "blocked",
        "warnings": [],
        "secret_findings_count": 0,
        "reason": "Unsupported file type for pilot preflight.",
    }


@dataclass
class PreflightReport:
    """Container for a completed preflight run."""

    generated_at: str
    overall_status: str
    files: list[dict[str, Any]]
    include_raw_samples: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "overall_status": self.overall_status,
            "include_raw_samples": self.include_raw_samples,
            "files": self.files,
        }


def run_preflight(
    mapping_path: Path,
    dataset_paths: list[Path],
    evidence_paths: list[Path],
    validation_report_paths: list[Path],
    out_dir: Path,
    include_raw_samples: bool = False,
) -> PreflightReport:
    """Inspect all pilot inputs and write JSON/Markdown preflight reports."""
    out_dir.mkdir(parents=True, exist_ok=True)

    files: list[dict[str, Any]] = []
    files.append(inspect_file(mapping_path))
    for p in dataset_paths:
        files.append(inspect_file(p))
    for p in evidence_paths:
        files.append(inspect_file(p))
    for p in validation_report_paths:
        files.append(inspect_file(p))

    if any(f["status"] == "blocked" for f in files):
        overall = "blocked"
    elif any(f["status"] == "warning" for f in files):
        overall = "warning"
    else:
        overall = "allowed"

    report = PreflightReport(
        generated_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        overall_status=overall,
        files=files,
        include_raw_samples=include_raw_samples,
    )

    json_path = out_dir / "preflight_report.json"
    json_path.write_text(
        json.dumps(report.to_dict(), indent=2, default=str),
        encoding="utf-8",
    )
    md_path = out_dir / "preflight_report.md"
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    return report


def _render_markdown(report: PreflightReport) -> str:
    lines = [
        "# Pilot Input Preflight Report",
        "",
        f"Generated: {report.generated_at}",
        f"Overall status: **{report.overall_status.upper()}**",
        "",
        "## Files",
        "",
        "| File | Type | Size | Status | Warnings |",
        "|---|---|---|---|---|",
    ]
    for f in report.files:
        warnings = "; ".join(f.get("warnings", [])) or "-"
        lines.append(
            f"| `{Path(f['path']).name}` | {f['file_type']} | "
            f"{f['size_bytes']} | {f['status']} | {warnings} |"
        )
    lines.append("")
    lines.append("## Details")
    lines.append("")
    for f in report.files:
        lines.append(f"### {Path(f['path']).name}")
        lines.append("")
        lines.append(f"- **Path**: {f['path']}")
        lines.append(f"- **Status**: {f['status']}")
        if f.get("reason"):
            lines.append(f"- **Reason**: {f['reason']}")
        if f.get("sheet_names"):
            lines.append(f"- **Sheets**: {', '.join(f['sheet_names'])}")
        if f.get("row_count") is not None:
            lines.append(f"- **Rows**: {f['row_count']}")
        if f.get("column_count") is not None:
            lines.append(f"- **Columns**: {f['column_count']}")
        if f.get("columns"):
            lines.append(f"- **Column names**: {', '.join(f['columns'])}")
        if f.get("warnings"):
            lines.append("- **Warnings**:")
            for w in f["warnings"]:
                lines.append(f"  - {w}")
        lines.append("")
    return "\n".join(lines)
