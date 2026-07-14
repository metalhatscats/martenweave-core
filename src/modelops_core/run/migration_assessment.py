"""One-command SAP migration assessment workflow.

Orchestrates validation, indexing, mapping workbook profiling, optional dataset
readiness, assessment package generation, review pack generation, and a machine-
readable manifest. Canonical files are never mutated.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from modelops_core import __version__
from modelops_core.assessment.assessment_service import (
    generate_assessment_package,
    generate_review_pack,
)
from modelops_core.config import (
    RepoConfig,
    load_repo_config,
    resolve_generated_path,
    resolve_model_path,
)
from modelops_core.index import build_index as _build_index
from modelops_core.repository import parse_file, scan_repository
from modelops_core.run.dataset_readiness import (
    generate_dataset_readiness_report,
    write_readiness_report,
)
from modelops_core.validation import validate_objects
from modelops_core.validation.result import ValidationSummary


@dataclass
class StageStatus:
    """Status for one assessment stage."""

    name: str
    status: str  # success | skipped | failed
    message: str = ""


@dataclass
class MappingWorkbookProfile:
    """Metadata profile for a mapping workbook input."""

    file_path: str
    file_hash: str
    sheet_names: list[str] = field(default_factory=list)
    total_rows: int = 0
    column_names: list[str] = field(default_factory=list)
    hidden_sheets: list[str] = field(default_factory=list)
    formula_warnings: list[str] = field(default_factory=list)
    missing_owner_rows: list[dict[str, Any]] = field(default_factory=list)
    duplicate_rows: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class MigrationAssessmentManifest:
    """Machine-readable manifest for a migration assessment run."""

    martenweave_version: str
    repo_name: str
    repo_path: str
    inputs: dict[str, Any]
    stage_statuses: list[StageStatus]
    generated_artifacts: list[dict[str, Any]]
    generated_at: str


def _file_hash(path: Path) -> str:
    """Return SHA-256 hex digest for a file."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _profile_mapping_workbook(mapping_path: Path) -> MappingWorkbookProfile:
    """Read a mapping workbook and report metadata + simple row-level checks."""
    try:
        from openpyxl import load_workbook
    except ImportError as exc:
        raise RuntimeError(
            "openpyxl is required for mapping workbook profiling."
        ) from exc

    file_hash = _file_hash(mapping_path)

    # Metadata pass
    wb = load_workbook(mapping_path, data_only=True, read_only=True)
    sheet_names = list(wb.sheetnames)
    hidden_sheets = [name for name in sheet_names if wb[name].sheet_state != "visible"]

    column_names: list[str] = []
    total_rows = 0
    missing_owner_rows: list[dict[str, Any]] = []
    duplicate_rows: list[dict[str, Any]] = []

    owner_col: str | None = None
    row_tuples: list[tuple] = []

    for sheet_name in sheet_names:
        ws = wb[sheet_name]
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            continue
        headers = [str(cell).strip() if cell is not None else "" for cell in rows[0]]
        if not column_names:
            column_names = headers
            # Find owner-ish column on first sheet
            for h in headers:
                if "owner" in h.lower():
                    owner_col = h
                    break

        data_rows = rows[1:]
        total_rows += len(data_rows)

        for idx, row in enumerate(data_rows, start=2):
            row_dict = {
                h: (str(v) if v is not None else "")
                for h, v in zip(headers, row, strict=False)
            }
            # Missing owner detection
            if owner_col and not row_dict.get(owner_col, "").strip():
                missing_owner_rows.append(
                    {
                        "sheet": sheet_name,
                        "row": idx,
                        "key_columns": {
                            h: row_dict[h]
                            for h in headers
                            if h.lower() in {"source_field", "target_table", "target_field"}
                            and row_dict.get(h)
                        },
                    }
                )

            # Duplicate detection: use source/target-ish columns as key
            key_parts = [
                row_dict.get(h, "").strip()
                for h in headers
                if any(
                    term in h.lower()
                    for term in ("source", "target", "legacy", "sap", "field")
                )
            ]
            key = tuple(p for p in key_parts if p)
            if key:
                row_tuples.append((sheet_name, idx, key, row_dict))

    wb.close()

    # Formula pass
    formula_warnings: list[str] = []
    try:
        wb_formula = load_workbook(mapping_path, data_only=False, read_only=True)
        for sheet_name in wb_formula.sheetnames:
            ws = wb_formula[sheet_name]
            for row in ws.iter_rows(min_row=2):
                for cell in row:
                    if (
                        cell.value is not None
                        and isinstance(cell.value, str)
                        and cell.value.startswith("=")
                    ):
                        formula_warnings.append(
                            f"Formula in sheet '{sheet_name}' cell {cell.coordinate}"
                        )
        wb_formula.close()
    except Exception:  # pragma: no cover - best effort
        pass

    # Duplicate reporting (limit to first 50 for sanity)
    seen: dict[tuple, tuple[str, int]] = {}
    for sheet_name, idx, key, _row_dict in row_tuples:
        if key in seen:
            prev_sheet, prev_idx = seen[key]
            duplicate_rows.append(
                {
                    "sheet": sheet_name,
                    "row": idx,
                    "duplicate_of": {"sheet": prev_sheet, "row": prev_idx},
                    "key": key,
                }
            )
        else:
            seen[key] = (sheet_name, idx)
        if len(duplicate_rows) >= 50:
            break

    return MappingWorkbookProfile(
        file_path=str(mapping_path),
        file_hash=file_hash,
        sheet_names=sheet_names,
        total_rows=total_rows,
        column_names=column_names,
        hidden_sheets=hidden_sheets,
        formula_warnings=formula_warnings,
        missing_owner_rows=missing_owner_rows,
        duplicate_rows=duplicate_rows,
    )


def _validate_repo(repo_root: Path) -> tuple[ValidationSummary, RepoConfig | None]:
    """Validate canonical objects in the repository."""
    model_path = resolve_model_path(repo_root)
    files = scan_repository(model_path)
    parsed_objects = [parse_file(f) for f in files]
    config = load_repo_config(repo_root)
    enabled_packs = config.enabled_domain_packs if config else None
    summary = validate_objects(parsed_objects, enabled_packs)
    return summary, config


def _ensure_index(repo_root: Path) -> Path:
    """Build the SQLite index if missing or refresh it."""
    db_path = resolve_generated_path(repo_root) / "modelops.db"
    _build_index(repo_root, db_path=db_path, allow_invalid=True, export_jsonl=False)
    return db_path


def _write_manifest(
    manifest: MigrationAssessmentManifest,
    out_dir: Path,
) -> Path:
    """Write the manifest as JSON."""
    manifest_path = out_dir / "manifest.json"
    data = {
        "martenweave_version": manifest.martenweave_version,
        "repo_name": manifest.repo_name,
        "repo_path": manifest.repo_path,
        "generated_at": manifest.generated_at,
        "inputs": manifest.inputs,
        "stage_statuses": [
            {"name": s.name, "status": s.status, "message": s.message}
            for s in manifest.stage_statuses
        ],
        "generated_artifacts": manifest.generated_artifacts,
    }
    manifest_path.write_text(
        json.dumps(data, indent=2, default=str, sort_keys=True),
        encoding="utf-8",
    )
    return manifest_path


def _collect_artifacts(out_dir: Path) -> list[dict[str, Any]]:
    """Collect all files under out_dir and compute hashes."""
    artifacts: list[dict[str, Any]] = []
    for path in sorted(out_dir.rglob("*")):
        if path.is_file():
            rel = path.relative_to(out_dir).as_posix()
            artifacts.append(
                {
                    "path": rel,
                    "size": path.stat().st_size,
                    "sha256": _file_hash(path),
                }
            )
    return artifacts


def _stage(name: str, statuses: list[StageStatus], status: str, message: str = "") -> None:
    statuses.append(StageStatus(name=name, status=status, message=message))


def generate_migration_assessment(
    repo_root: Path,
    mapping_path: Path,
    dataset_path: Path | None,
    evidence_paths: list[Path],
    out_dir: Path,
) -> MigrationAssessmentManifest:
    """Generate a complete migration assessment output package and manifest.

    Args:
        repo_root: Path to the model repository.
        mapping_path: Path to the XLSX mapping workbook.
        dataset_path: Optional path to a CSV/XLSX sample dataset.
        evidence_paths: Optional list of evidence file paths.
        out_dir: Directory where all outputs will be written.

    Returns:
        MigrationAssessmentManifest describing inputs, stage statuses, and artifacts.

    Raises:
        RuntimeError: if a required stage fails and the manifest cannot be written.
        ValueError: if required inputs are missing or invalid.
    """
    repo_root = repo_root.resolve()
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    config = load_repo_config(repo_root)
    repo_name = config.name if config else repo_root.name

    statuses: list[StageStatus] = []
    generated_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")

    inputs: dict[str, Any] = {
        "mapping": str(mapping_path),
        "dataset": str(dataset_path) if dataset_path else None,
        "evidence": [str(p) for p in evidence_paths],
    }

    # Stage: validation
    try:
        summary, _ = _validate_repo(repo_root)
        _stage(
            "validation",
            statuses,
            "success" if summary.is_valid else "success",
            message=f"{summary.error_count} errors, {summary.warning_count} warnings",
        )
    except Exception as exc:  # pragma: no cover - defensive
        _stage("validation", statuses, "failed", message=str(exc))
        # Continue so the manifest can still be written

    # Stage: index
    try:
        _ensure_index(repo_root)
        _stage("index", statuses, "success")
    except Exception as exc:  # pragma: no cover - defensive
        _stage("index", statuses, "failed", message=str(exc))

    # Stage: mapping workbook profile
    mapping_profile: MappingWorkbookProfile | None = None
    try:
        mapping_profile = _profile_mapping_workbook(mapping_path)
        _stage("mapping_profile", statuses, "success")
    except Exception as exc:
        _stage("mapping_profile", statuses, "failed", message=str(exc))

    if mapping_profile is not None:
        profile_path = out_dir / "mapping_profile.json"
        profile_path.write_text(
            json.dumps(
                {
                    "file_path": mapping_profile.file_path,
                    "file_hash": mapping_profile.file_hash,
                    "sheet_names": mapping_profile.sheet_names,
                    "total_rows": mapping_profile.total_rows,
                    "column_names": mapping_profile.column_names,
                    "hidden_sheets": mapping_profile.hidden_sheets,
                    "formula_warnings": mapping_profile.formula_warnings,
                    "missing_owner_rows": mapping_profile.missing_owner_rows,
                    "duplicate_rows": mapping_profile.duplicate_rows,
                },
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

    # Stage: dataset readiness (optional)
    readiness_dir = out_dir / "dataset_readiness"
    if dataset_path is not None:
        try:
            readiness_report = generate_dataset_readiness_report(
                repo_root=repo_root,
                dataset_path=dataset_path,
                check_model=True,
                dry_run=False,
                promote_to_proposal=False,
                issue_draft=False,
            )
            readiness_dir.mkdir(parents=True, exist_ok=True)
            write_readiness_report(readiness_report, readiness_dir)
            _stage("dataset_readiness", statuses, "success")
        except Exception as exc:
            _stage("dataset_readiness", statuses, "failed", message=str(exc))
    else:
        _stage("dataset_readiness", statuses, "skipped", message="No dataset provided")

    # Stage: assessment package
    try:
        generate_assessment_package(repo_root, out_dir)
        _stage("assessment_package", statuses, "success")
    except Exception as exc:
        _stage("assessment_package", statuses, "failed", message=str(exc))

    # Stage: review pack
    try:
        review_pack_dir = out_dir / "review_pack"
        review_pack_dir.mkdir(parents=True, exist_ok=True)
        generate_review_pack(repo_root, review_pack_dir)
        _stage("review_pack", statuses, "success")
    except Exception as exc:
        _stage("review_pack", statuses, "failed", message=str(exc))

    # Collect artifacts and write manifest (including the manifest itself)
    artifacts = _collect_artifacts(out_dir)
    manifest_path_placeholder = {
        "path": "manifest.json",
        "size": 0,
        "sha256": "",
    }
    artifacts.append(manifest_path_placeholder)
    manifest = MigrationAssessmentManifest(
        martenweave_version=__version__,
        repo_name=repo_name,
        repo_path=str(repo_root),
        inputs=inputs,
        stage_statuses=statuses,
        generated_artifacts=artifacts,
        generated_at=generated_at,
    )
    manifest_path = _write_manifest(manifest, out_dir)
    manifest_path_placeholder["size"] = manifest_path.stat().st_size
    manifest_path_placeholder["sha256"] = _file_hash(manifest_path)
    _write_manifest(manifest, out_dir)

    return manifest
