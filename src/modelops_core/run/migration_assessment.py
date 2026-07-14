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
from modelops_core.assessment.finding_contract import (
    AffectedObject,
    FindingDetectionMode,
    FindingEvidence,
    FindingProvenance,
    FindingSeverity,
    FindingStatus,
    ReadinessFinding,
    ReadinessImpact,
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
from modelops_core.schemas.versioning import CURRENT_SCHEMA_VERSION
from modelops_core.validation import validate_objects
from modelops_core.validation.result import ValidationSummary


@dataclass
class StageStatus:
    """Status for one assessment stage."""

    name: str
    status: str  # success | skipped | failed
    message: str = ""


def _is_field_mapping_sheet(name: str) -> bool:
    """Return True for source-to-target field mapping sheets."""
    lower = name.lower()
    return lower.endswith("_mappings") and "value" not in lower


def _is_decisions_sheet(name: str) -> bool:
    """Return True for decision registers."""
    return "decision" in name.lower()


_SEVERITY_BY_CATEGORY: dict[str, FindingSeverity] = {
    "missing_owner": FindingSeverity.MEDIUM,
    "missing_mapping": FindingSeverity.HIGH,
    "obsolete_field": FindingSeverity.LOW,
    "validation_coverage_gap": FindingSeverity.MEDIUM,
    "unresolved_decision": FindingSeverity.MEDIUM,
    "conflicting_decision": FindingSeverity.HIGH,
    "duplicate_target": FindingSeverity.MEDIUM,
}

_READINESS_IMPACT_BY_SEVERITY: dict[FindingSeverity, ReadinessImpact] = {
    FindingSeverity.HIGH: ReadinessImpact.BLOCKING,
    FindingSeverity.MEDIUM: ReadinessImpact.AT_RISK,
    FindingSeverity.LOW: ReadinessImpact.INFORMATIONAL,
}

_RECOMMENDED_ACTION_BY_CATEGORY: dict[str, str] = {
    "missing_owner": "Assign an owner to the mapping row.",
    "missing_mapping": "Define the target table and field for the source field.",
    "obsolete_field": "Confirm retirement plan and remove or archive the mapping.",
    "validation_coverage_gap": "Add a validation rule or test for the conditional mapping.",
    "unresolved_decision": "Record an accepted decision in the mapping workbook.",
    "conflicting_decision": "Reconcile the conflicting decision topics.",
    "duplicate_target": "Consolidate source mappings that target the same field.",
}


def _stable_id(*parts: str) -> str:
    """Build a deterministic, URL-safe finding ID from parts."""
    cleaned = []
    for part in parts:
        text = str(part).lower().strip().replace(" ", "_")
        text = "".join(c for c in text if c.isalnum() or c in "_-").strip("_-")
        if text:
            cleaned.append(text)
    return ":".join(cleaned)


def _build_findings(
    profile: MappingWorkbookProfile,
    workbook_fingerprint: str = "",
) -> list[dict[str, Any]]:
    """Convert mapping-workbook profile findings into the readiness contract."""
    findings: list[dict[str, Any]] = []
    source_id = workbook_fingerprint or profile.file_hash

    def _make_finding(
        finding_id: str,
        category: str,
        location: dict[str, Any],
        message: str,
    ) -> ReadinessFinding:
        severity = _SEVERITY_BY_CATEGORY.get(category, FindingSeverity.MEDIUM)
        return ReadinessFinding(
            id=finding_id,
            type="readiness_finding",
            category=category,
            severity=severity,
            status=FindingStatus.OPEN,
            source="mapping_profile",
            message=message,
            recommended_action=_RECOMMENDED_ACTION_BY_CATEGORY.get(category, ""),
            readiness_impact=_READINESS_IMPACT_BY_SEVERITY.get(
                severity, ReadinessImpact.INFORMATIONAL
            ),
            location=location,
            affected_objects=[
                AffectedObject(
                    object_id=location.get("source_field", ""),
                    object_type="FieldEndpoint",
                    role="source",
                ),
                AffectedObject(
                    object_id=(
                        f"{location.get('target_table', '')}."
                        f"{location.get('target_field', '')}"
                    ).strip("."),
                    object_type="FieldEndpoint",
                    role="target",
                ),
            ],
            evidence_refs=[
                FindingEvidence(
                    source_type="mapping_workbook",
                    source_id=source_id,
                    location={
                        "sheet": location.get("sheet", ""),
                        "row": location.get("row", ""),
                    },
                    fingerprint=source_id,
                )
            ],
            provenance=FindingProvenance(
                detection_mode=FindingDetectionMode.DETERMINISTIC,
                rule_id=f"mapping_workbook_{category}",
                rule_version=__version__,
                source_module="modelops_core.run.migration_assessment",
            ),
        )

    for row in profile.missing_owner_rows:
        findings.append(
            _make_finding(
                _stable_id("mapping", "missing_owner", row["sheet"], row["row"]),
                "missing_owner",
                row,
                f"Missing owner in '{row['sheet']}' row {row['row']}.",
            ).to_dict()
        )

    for row in profile.missing_mapping_rows:
        findings.append(
            _make_finding(
                _stable_id("mapping", "missing_mapping", row["sheet"], row["row"]),
                "missing_mapping",
                row,
                f"Missing target mapping in '{row['sheet']}' row {row['row']}.",
            ).to_dict()
        )

    for row in profile.obsolete_rows:
        findings.append(
            _make_finding(
                _stable_id("mapping", "obsolete_field", row["sheet"], row["row"]),
                "obsolete_field",
                row,
                f"Obsolete field in '{row['sheet']}' row {row['row']}.",
            ).to_dict()
        )

    for row in profile.validation_coverage_gaps:
        findings.append(
            _make_finding(
                _stable_id("mapping", "validation_coverage_gap", row["sheet"], row["row"]),
                "validation_coverage_gap",
                row,
                (
                    f"Conditional rule without validation coverage in "
                    f"'{row['sheet']}' row {row['row']}."
                ),
            ).to_dict()
        )

    for row in profile.unresolved_decisions:
        findings.append(
            _make_finding(
                _stable_id("decision", "unresolved", row["sheet"], row["row"]),
                "unresolved_decision",
                row,
                f"Unresolved decision in '{row['sheet']}' row {row['row']}.",
            ).to_dict()
        )

    for conflict in profile.conflicting_decisions:
        topic = conflict.get("topic", "unknown")
        findings.append(
            _make_finding(
                _stable_id("decision", "conflict", topic),
                "conflicting_decision",
                conflict,
                f"Conflicting decisions on topic '{topic}'.",
            ).to_dict()
        )

    for row in profile.duplicate_target_rows:
        findings.append(
            _make_finding(
                _stable_id("mapping", "duplicate_target", row["sheet"], row["row"]),
                "duplicate_target",
                row,
                f"Duplicate target representation in '{row['sheet']}' row {row['row']}.",
            ).to_dict()
        )

    return findings


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
    missing_mapping_rows: list[dict[str, Any]] = field(default_factory=list)
    obsolete_rows: list[dict[str, Any]] = field(default_factory=list)
    validation_coverage_gaps: list[dict[str, Any]] = field(default_factory=list)
    unresolved_decisions: list[dict[str, Any]] = field(default_factory=list)
    conflicting_decisions: list[dict[str, Any]] = field(default_factory=list)
    duplicate_target_rows: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class AssessmentRunIdentity:
    """Reproducible identity for a single assessment run."""

    run_id: str
    core_version: str
    schema_version: str
    domain_packs: list[str]
    repo_commit: str | None
    command: str


@dataclass
class InputFingerprints:
    """Content fingerprints for all assessment inputs."""

    mapping: dict[str, Any]
    dataset: dict[str, Any] | None
    evidence: list[dict[str, Any]]
    repo_state: dict[str, Any]
    config: dict[str, Any]


@dataclass
class MigrationAssessmentManifest:
    """Machine-readable manifest for a migration assessment run."""

    run_id: str
    martenweave_version: str
    schema_version: str
    repo_name: str
    repo_path: str
    inputs: dict[str, Any]
    fingerprints: InputFingerprints
    run_identity: AssessmentRunIdentity
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


def _repo_commit(repo_root: Path) -> str | None:
    """Return the current Git commit hash if available."""
    import subprocess

    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:  # pragma: no cover - best effort
        pass
    return None


def _canonical_repo_state_fingerprint(repo_root: Path) -> dict[str, Any]:
    """Return a stable fingerprint of canonical object content.

    Hashes every canonical Markdown/YAML file and sorts by relative path so the
    fingerprint is stable regardless of filesystem traversal order.
    """
    model_path = resolve_model_path(repo_root)
    entries: list[dict[str, Any]] = []
    if model_path.exists():
        for path in sorted(model_path.rglob("*")):
            if path.is_file() and path.suffix in {".md", ".yaml", ".yml"}:
                rel = path.relative_to(model_path).as_posix()
                entries.append({"path": rel, "sha256": _file_hash(path)})
    return {
        "model_path": str(model_path.relative_to(repo_root).as_posix()),
        "object_count": len(entries),
        "objects": entries,
        "fingerprint": _hash_json_object(entries),
    }


def _hash_json_object(obj: Any) -> str:
    """Return a deterministic SHA-256 hash of a JSON-serializable object."""
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _normalized_workbook_fingerprint(
    mapping_path: Path,
    profile: MappingWorkbookProfile,
) -> dict[str, Any]:
    """Return a content fingerprint that ignores irrelevant file metadata.

    Uses the raw file hash plus a normalized logical hash built from sheet
    names, headers, and data rows so that irrelevant timestamp changes do not
    alter the logical identity of the workbook.
    """
    logical_rows: list[dict[str, Any]] = []
    try:
        from openpyxl import load_workbook

        wb = load_workbook(mapping_path, data_only=True, read_only=True)
        for sheet_name in sorted(wb.sheetnames):
            ws = wb[sheet_name]
            rows = list(ws.iter_rows(values_only=True))
            if not rows:
                continue
            headers = [str(cell).strip() if cell is not None else "" for cell in rows[0]]
            data_rows = rows[1:]
            logical_rows.append(
                {
                    "sheet": sheet_name,
                    "headers": headers,
                    "rows": [
                        [str(cell) if cell is not None else "" for cell in row]
                        for row in data_rows
                    ],
                }
            )
        wb.close()
    except Exception:  # pragma: no cover - best effort
        pass

    logical_fingerprint = _hash_json_object(logical_rows)
    return {
        "file_path": str(mapping_path),
        "file_name": mapping_path.name,
        "file_hash": profile.file_hash,
        "logical_fingerprint": logical_fingerprint,
        "sheet_count": len(profile.sheet_names),
        "total_rows": profile.total_rows,
    }


def _dataset_fingerprint(dataset_path: Path | None) -> dict[str, Any] | None:
    """Return a fingerprint for an optional dataset file."""
    if dataset_path is None:
        return None
    return {
        "file_path": str(dataset_path),
        "file_name": dataset_path.name,
        "file_hash": _file_hash(dataset_path),
    }


def _evidence_fingerprints(evidence_paths: list[Path]) -> list[dict[str, Any]]:
    """Return fingerprints for evidence files."""
    return [
        {
            "file_path": str(path),
            "file_name": path.name,
            "file_hash": _file_hash(path),
        }
        for path in evidence_paths
        if path.exists()
    ]


def _config_fingerprint(config: RepoConfig | None) -> dict[str, Any]:
    """Return a fingerprint for repository configuration."""
    if config is None:
        return {"schema_version": CURRENT_SCHEMA_VERSION, "fingerprint": ""}
    payload = {
        "schema_version": config.schema_version,
        "enabled_domain_packs": sorted(config.enabled_domain_packs),
        "version": config.version,
    }
    return {
        **payload,
        "fingerprint": _hash_json_object(payload),
    }


def _profile_mapping_workbook(mapping_path: Path) -> MappingWorkbookProfile:
    """Read a mapping workbook and report metadata + simple row-level checks."""
    try:
        from openpyxl import load_workbook
    except ImportError as exc:
        raise RuntimeError("openpyxl is required for mapping workbook profiling.") from exc

    file_hash = _file_hash(mapping_path)

    # Metadata pass
    wb = load_workbook(mapping_path, data_only=True, read_only=True)
    sheet_names = list(wb.sheetnames)
    hidden_sheets = [name for name in sheet_names if wb[name].sheet_state != "visible"]

    column_names: list[str] = []
    total_rows = 0
    missing_owner_rows: list[dict[str, Any]] = []
    duplicate_rows: list[dict[str, Any]] = []
    missing_mapping_rows: list[dict[str, Any]] = []
    obsolete_rows: list[dict[str, Any]] = []
    validation_coverage_gaps: list[dict[str, Any]] = []
    unresolved_decisions: list[dict[str, Any]] = []
    conflicting_decisions: list[dict[str, Any]] = []
    duplicate_target_rows: list[dict[str, Any]] = []

    owner_col: str | None = None
    row_tuples: list[tuple] = []
    target_seen: dict[str, dict[tuple[str, str], tuple[str, int]]] = {}
    decision_topics: dict[str, list[dict[str, Any]]] = {}

    def _find_col(*candidates: str) -> str | None:
        for header in headers:
            if header.lower() in candidates:
                return header
        return None

    for sheet_name in sheet_names:
        ws = wb[sheet_name]
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            continue
        headers = [str(cell).strip() if cell is not None else "" for cell in rows[0]]
        if not column_names:
            column_names = headers
            for h in headers:
                if "owner" in h.lower():
                    owner_col = h
                    break

        is_mapping = _is_field_mapping_sheet(sheet_name)
        is_decisions = _is_decisions_sheet(sheet_name)

        source_field_col = _find_col("source_field")
        source_system_col = _find_col("source_system")
        source_table_col = _find_col("source_table")
        target_table_col = _find_col("target_table")
        target_field_col = _find_col("target_field")
        status_col = _find_col("status")
        condition_col = _find_col("condition")
        validation_rule_col = _find_col("validation_rule")
        topic_col = _find_col("topic")
        decision_id_col = _find_col("decision_id")

        if is_mapping:
            target_seen.setdefault(sheet_name, {})

        data_rows = rows[1:]
        total_rows += len(data_rows)

        for idx, row in enumerate(data_rows, start=2):
            row_dict = {
                h: (str(v) if v is not None else "") for h, v in zip(headers, row, strict=False)
            }
            status = row_dict.get(status_col, "").strip().lower() if status_col else ""

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

            # Field-mapping-specific checks
            if is_mapping:
                source_field = (
                    row_dict.get(source_field_col, "").strip() if source_field_col else ""
                )
                target_table = (
                    row_dict.get(target_table_col, "").strip() if target_table_col else ""
                )
                target_field = (
                    row_dict.get(target_field_col, "").strip() if target_field_col else ""
                )

                if status != "obsolete" and (not target_table or not target_field):
                    missing_mapping_rows.append(
                        {
                            "sheet": sheet_name,
                            "row": idx,
                            "source_field": source_field,
                            "source_system": (
                                row_dict.get(source_system_col, "") if source_system_col else ""
                            ),
                            "source_table": (
                                row_dict.get(source_table_col, "") if source_table_col else ""
                            ),
                            "target_table": target_table,
                            "target_field": target_field,
                        }
                    )

                if status == "obsolete":
                    obsolete_rows.append(
                        {
                            "sheet": sheet_name,
                            "row": idx,
                            "source_field": source_field,
                            "target_table": target_table,
                            "target_field": target_field,
                            "reviewer_comment": row_dict.get(_find_col("reviewer_comment"), ""),
                        }
                    )

                condition = row_dict.get(condition_col, "").strip() if condition_col else ""
                validation_rule = (
                    row_dict.get(validation_rule_col, "").strip() if validation_rule_col else ""
                )
                if status != "obsolete" and condition and not validation_rule:
                    validation_coverage_gaps.append(
                        {
                            "sheet": sheet_name,
                            "row": idx,
                            "source_field": source_field,
                            "condition": condition,
                        }
                    )

                # Exact duplicate detection: source + target identity
                key_parts = [
                    row_dict.get(h, "").strip()
                    for h in headers
                    if any(
                        term in h.lower() for term in ("source", "target", "legacy", "sap", "field")
                    )
                ]
                key = tuple(p for p in key_parts if p)
                if key:
                    row_tuples.append((sheet_name, idx, key, row_dict))

                # Duplicate target representation: same target, different source
                tkey = (target_table, target_field)
                if tkey[0] or tkey[1]:
                    sheet_target_seen = target_seen[sheet_name]
                    if tkey in sheet_target_seen:
                        prev_sheet, prev_idx = sheet_target_seen[tkey]
                        duplicate_target_rows.append(
                            {
                                "sheet": sheet_name,
                                "row": idx,
                                "duplicate_of": {
                                    "sheet": prev_sheet,
                                    "row": prev_idx,
                                },
                                "target_table": target_table,
                                "target_field": target_field,
                            }
                        )
                    else:
                        sheet_target_seen[tkey] = (sheet_name, idx)

            # Pending status is treated as an unresolved decision anywhere it appears.
            if status == "pending":
                unresolved_decisions.append(
                    {
                        "sheet": sheet_name,
                        "row": idx,
                        "decision_id": (
                            row_dict.get(decision_id_col, "") if decision_id_col else ""
                        ),
                        "topic": row_dict.get(topic_col, "") if topic_col else "",
                    }
                )

            # Collect decision topics for conflict detection.
            if is_decisions and topic_col:
                topic = row_dict.get(topic_col, "").strip().lower()
                if topic:
                    decision_topics.setdefault(topic, []).append(
                        {
                            "sheet": sheet_name,
                            "row": idx,
                            "topic": row_dict.get(topic_col, ""),
                            "decision_id": (
                                row_dict.get(decision_id_col, "") if decision_id_col else ""
                            ),
                            "status": row_dict.get(status_col, "") if status_col else "",
                        }
                    )

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

    # Exact-duplicate reporting (limit to first 50 for sanity)
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

    # Conflicting decisions: the same topic appears more than once in the Decisions sheet.
    for topic, topic_rows in decision_topics.items():
        if len(topic_rows) > 1:
            conflicting_decisions.append(
                {"topic": topic, "rows": topic_rows, "count": len(topic_rows)}
            )

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
        missing_mapping_rows=missing_mapping_rows,
        obsolete_rows=obsolete_rows,
        validation_coverage_gaps=validation_coverage_gaps,
        unresolved_decisions=unresolved_decisions,
        conflicting_decisions=conflicting_decisions,
        duplicate_target_rows=duplicate_target_rows,
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
    data: dict[str, Any] = {
        "run_id": manifest.run_id,
        "martenweave_version": manifest.martenweave_version,
        "schema_version": manifest.schema_version,
        "repo_name": manifest.repo_name,
        "repo_path": manifest.repo_path,
        "generated_at": manifest.generated_at,
        "inputs": manifest.inputs,
        "fingerprints": {
            "mapping": manifest.fingerprints.mapping,
            "dataset": manifest.fingerprints.dataset,
            "evidence": manifest.fingerprints.evidence,
            "repo_state": manifest.fingerprints.repo_state,
            "config": manifest.fingerprints.config,
        },
        "run_identity": {
            "run_id": manifest.run_identity.run_id,
            "core_version": manifest.run_identity.core_version,
            "schema_version": manifest.run_identity.schema_version,
            "domain_packs": manifest.run_identity.domain_packs,
            "repo_commit": manifest.run_identity.repo_commit,
            "command": manifest.run_identity.command,
        },
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
    run_id: str | None = None,
    command: str = "modelops run migration-assessment",
) -> MigrationAssessmentManifest:
    """Generate a complete migration assessment output package and manifest.

    Args:
        repo_root: Path to the model repository.
        mapping_path: Path to the XLSX mapping workbook.
        dataset_path: Optional path to a CSV/XLSX sample dataset.
        evidence_paths: Optional list of evidence file paths.
        out_dir: Directory where all outputs will be written.
        run_id: Optional stable run identifier. Generated deterministically when
            omitted based on input fingerprints.
        command: The command that produced this run.

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
    domain_packs = config.enabled_domain_packs if config else []
    schema_version = config.schema_version if config else CURRENT_SCHEMA_VERSION

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
    mapping_fingerprint: dict[str, Any] = {}
    try:
        mapping_profile = _profile_mapping_workbook(mapping_path)
        _stage("mapping_profile", statuses, "success")
    except Exception as exc:
        _stage("mapping_profile", statuses, "failed", message=str(exc))

    if mapping_profile is not None:
        mapping_fingerprint = _normalized_workbook_fingerprint(mapping_path, mapping_profile)
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
                    "missing_mapping_rows": mapping_profile.missing_mapping_rows,
                    "obsolete_rows": mapping_profile.obsolete_rows,
                    "validation_coverage_gaps": mapping_profile.validation_coverage_gaps,
                    "unresolved_decisions": mapping_profile.unresolved_decisions,
                    "conflicting_decisions": mapping_profile.conflicting_decisions,
                    "duplicate_target_rows": mapping_profile.duplicate_target_rows,
                },
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

        # Stable findings derived from the mapping workbook profile.
        findings = _build_findings(
            mapping_profile,
            workbook_fingerprint=mapping_fingerprint["logical_fingerprint"],
        )
        findings_path = out_dir / "findings.json"
        findings_path.write_text(
            json.dumps(
                {
                    "generated_at": generated_at,
                    "finding_count": len(findings),
                    "findings": findings,
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

    # Build stable input fingerprints and run identity
    fingerprints = InputFingerprints(
        mapping=mapping_fingerprint if mapping_profile is not None else {},
        dataset=_dataset_fingerprint(dataset_path),
        evidence=_evidence_fingerprints(evidence_paths),
        repo_state=_canonical_repo_state_fingerprint(repo_root),
        config=_config_fingerprint(config),
    )
    run_identity = AssessmentRunIdentity(
        run_id=run_id or "",
        core_version=__version__,
        schema_version=schema_version,
        domain_packs=domain_packs,
        repo_commit=_repo_commit(repo_root),
        command=command,
    )

    # Generate a deterministic run ID from input fingerprints when not supplied.
    if not run_identity.run_id:
        run_identity.run_id = _hash_json_object(
            {
                "core_version": run_identity.core_version,
                "schema_version": run_identity.schema_version,
                "domain_packs": sorted(run_identity.domain_packs),
                "fingerprints": {
                    "mapping": fingerprints.mapping.get("logical_fingerprint", ""),
                    "dataset": (
                        fingerprints.dataset.get("file_hash", "")
                        if fingerprints.dataset
                        else ""
                    ),
                    "evidence": [e.get("file_hash", "") for e in fingerprints.evidence],
                    "repo_state": fingerprints.repo_state.get("fingerprint", ""),
                    "config": fingerprints.config.get("fingerprint", ""),
                },
            }
        )

    # Collect artifacts and write manifest (including the manifest itself)
    artifacts = _collect_artifacts(out_dir)
    manifest_path_placeholder = {
        "path": "manifest.json",
        "size": 0,
        "sha256": "",
    }
    artifacts.append(manifest_path_placeholder)
    manifest = MigrationAssessmentManifest(
        run_id=run_identity.run_id,
        martenweave_version=__version__,
        schema_version=schema_version,
        repo_name=repo_name,
        repo_path=str(repo_root),
        inputs=inputs,
        fingerprints=fingerprints,
        run_identity=run_identity,
        stage_statuses=statuses,
        generated_artifacts=artifacts,
        generated_at=generated_at,
    )
    manifest_path = _write_manifest(manifest, out_dir)
    manifest_path_placeholder["size"] = manifest_path.stat().st_size
    manifest_path_placeholder["sha256"] = _file_hash(manifest_path)
    _write_manifest(manifest, out_dir)

    return manifest
