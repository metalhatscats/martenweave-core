"""Atomic patch apply with rollback, audit, and index rebuild."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from modelops_core.approval.risk_service import compute_proposal_risk
from modelops_core.config import load_repo_config, resolve_generated_path
from modelops_core.index import build_index
from modelops_core.repository import ParsedObject, parse_file, scan_repository
from modelops_core.validation import validate_objects
from modelops_core.validation.result import ValidationSeverity, ValidationSummary


@dataclass
class ApplyResult:
    """Result of applying a PatchProposal."""

    proposal_id: str
    proposal_status: str = "accepted"
    application_status: str | None = None
    changed_files: list[str] = field(default_factory=list)
    validation: dict[str, Any] = field(default_factory=dict)
    audit_event_written: bool = False
    index_rebuilt: bool = False
    db_path: str | None = None
    error: str | None = None
    risk_level: str | None = None
    risk_assessment: dict[str, Any] = field(default_factory=dict)
    approved_change_request_id: str | None = None
    pre_write_warnings: list[str] = field(default_factory=list)


@dataclass
class DryRunResult:
    """Result of a dry-run apply."""

    proposal_id: str
    would_change: bool
    operations_preview: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None


_OBJECT_TYPE_SUBFOLDER: dict[str, str] = {
    "Attribute": "attributes",
    "FieldEndpoint": "field-endpoints",
    "ValidationRule": "validations",
    "EntityContext": "entity-contexts",
    "Mapping": "mappings",
    "ValueMapping": "value-mappings",
    "ValueList": "value-lists",
    "Issue": "issues",
    "Decision": "decisions",
    "ChangeRequest": "change-requests",
    "PatchProposal": "patch-proposals",
    "MasterDataDomain": "domains",
    "MigrationObject": "migration-objects",
    "BusinessEntity": "entities",
    "System": "systems",
    "SystemEnvironment": "system-environments",
    "SAPObject": "sap-objects",
    "Dataset": "datasets",
    "MappingSet": "mapping-sets",
    "BusinessRule": "rules",
    "TransformationLogic": "logic",
    "DataQualityCheck": "quality-checks",
    "OwnershipRole": "owners",
    "Person": "people",
    "Team": "teams",
    "Risk": "risks",
    "Evidence": "evidence",
    "Interface": "interfaces",
}

_BLOCKED_PATH_SEGMENTS: frozenset[str] = frozenset(
    {"generated", "data", "imports", "schemas", "apps", "docs", ".env"}
)

_GOVERNANCE_FOLDERS: frozenset[str] = frozenset({"patch-proposals", "change-requests"})

_SUPPORTED_OPERATIONS: frozenset[str] = frozenset(
    {"update_object", "create_object", "add_object", "create_issue"}
)


def _normalize_operation_name(op: str) -> str:
    """Map legacy/alias operation names to their canonical implementation."""
    if op in {"add_object", "create_issue"}:
        return "create_object"
    return op


def _now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _find_object_file(repo_model_path: Path, object_id: str) -> Path | None:
    for file_path in scan_repository(repo_model_path):
        parsed = parse_file(file_path)
        if parsed.frontmatter and parsed.frontmatter.get("id") == object_id:
            return Path(file_path)
    return None


def _resolve_subfolder(repo_model_path: Path, object_type: str | None) -> Path:
    subfolder = _OBJECT_TYPE_SUBFOLDER.get(object_type, "")
    target_dir = repo_model_path / subfolder if subfolder else repo_model_path
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir


def _is_safe_path(
    target_path: Path,
    repo_model_path: Path,
    allow_governance: bool = False,
) -> bool:
    try:
        target_path.resolve().relative_to(repo_model_path.resolve())
    except ValueError:
        return False

    parts = {p.lower() for p in target_path.parts}
    if parts & _BLOCKED_PATH_SEGMENTS:
        return False

    if not allow_governance:
        for part in target_path.parts:
            if part.lower() in {g.lower() for g in _GOVERNANCE_FOLDERS}:
                return False

    return True


def _render_markdown(frontmatter: dict[str, Any], body: str | None = None) -> str:
    yaml_text = yaml.safe_dump(
        frontmatter, default_flow_style=False, sort_keys=False, allow_unicode=True
    )
    lines = ["---", yaml_text.rstrip(), "---"]
    if body:
        lines.append("")
        lines.append(body.strip())
    else:
        name = frontmatter.get("name") or frontmatter.get("title") or ""
        obj_id = frontmatter.get("id", "")
        lines.append("")
        lines.append(f"# {name or obj_id}")
        lines.append("")
    return "\n".join(lines) + "\n"


def _build_candidate_update_object(op: Any, repo_model_path: Path) -> ParsedObject:
    object_id = op.object_id
    if not object_id:
        raise ValueError("update_object requires object_id")

    target_path = _find_object_file(repo_model_path, object_id)
    if target_path is None:
        raise ValueError(f"Object '{object_id}' not found in repository")

    if not _is_safe_path(target_path, repo_model_path):
        raise ValueError(f"Unsafe path for update_object: {target_path}")

    parsed = parse_file(target_path)
    if parsed.frontmatter is None:
        raise ValueError(f"File for '{object_id}' has no frontmatter")

    frontmatter = dict(parsed.frontmatter)
    target_field = op.target_path or ""
    if not target_field:
        raise ValueError("update_object requires target_path")

    if "." in target_field:
        parts = target_field.split(".")
        if len(parts) != 2:
            raise ValueError(
                f"Nested target_path deeper than one level not supported: {target_field}"
            )
        parent, child = parts
        if parent not in frontmatter:
            frontmatter[parent] = {}
        if not isinstance(frontmatter[parent], dict):
            raise ValueError(f"Cannot set nested key on non-dict: {parent}")
        frontmatter[parent][child] = op.after
    else:
        frontmatter[target_field] = op.after

    new_content = _render_markdown(frontmatter, parsed.body)
    content_hash = hashlib.sha256(new_content.encode("utf-8")).hexdigest()
    return ParsedObject(
        source_path=str(target_path),
        content_hash=content_hash,
        frontmatter=frontmatter,
        body=parsed.body,
        parser_error=None,
    )


def _build_candidate_create_object(op: Any, repo_model_path: Path) -> ParsedObject:
    object_id = op.object_id
    object_type = op.object_type
    if not object_id:
        raise ValueError("create_object requires object_id")
    if not object_type:
        raise ValueError("create_object requires object_type")

    target_dir = _resolve_subfolder(repo_model_path, object_type)
    target_path = target_dir / f"{object_id}.md"

    if not _is_safe_path(target_path, repo_model_path):
        raise ValueError(f"Unsafe path for create_object: {target_path}")

    if isinstance(op.after, dict):
        frontmatter = dict(op.after)
    else:
        frontmatter = {"id": object_id, "type": object_type, "status": "draft"}

    frontmatter.setdefault("id", object_id)
    frontmatter.setdefault("type", object_type)
    frontmatter.setdefault("status", "draft")

    new_content = _render_markdown(frontmatter, None)
    content_hash = hashlib.sha256(new_content.encode("utf-8")).hexdigest()
    return ParsedObject(
        source_path=str(target_path),
        content_hash=content_hash,
        frontmatter=frontmatter,
        body=None,
        parser_error=None,
    )


def _integrate_candidate(
    current_objects: list[ParsedObject], candidate: ParsedObject
) -> list[ParsedObject]:
    result: list[ParsedObject] = []
    replaced = False
    for obj in current_objects:
        if obj.source_path == candidate.source_path:
            result.append(candidate)
            replaced = True
        else:
            result.append(obj)
    if not replaced:
        result.append(candidate)
    return result


def _apply_update_object(
    op: Any, repo_model_path: Path, backup_state: dict[Path, str | None]
) -> Path:
    object_id = op.object_id
    if not object_id:
        raise ValueError("update_object requires object_id")

    target_path = _find_object_file(repo_model_path, object_id)
    if target_path is None:
        raise ValueError(f"Object '{object_id}' not found in repository")

    if not _is_safe_path(target_path, repo_model_path):
        raise ValueError(f"Unsafe path for update_object: {target_path}")

    parsed = parse_file(target_path)
    if parsed.frontmatter is None:
        raise ValueError(f"File for '{object_id}' has no frontmatter")

    if target_path not in backup_state:
        backup_state[target_path] = target_path.read_text(encoding="utf-8")

    frontmatter = dict(parsed.frontmatter)
    target_field = op.target_path or ""
    if not target_field:
        raise ValueError("update_object requires target_path")

    if "." in target_field:
        parts = target_field.split(".")
        if len(parts) != 2:
            raise ValueError(
                f"Nested target_path deeper than one level not supported: {target_field}"
            )
        parent, child = parts
        if parent not in frontmatter:
            frontmatter[parent] = {}
        if not isinstance(frontmatter[parent], dict):
            raise ValueError(f"Cannot set nested key on non-dict: {parent}")
        frontmatter[parent][child] = op.after
    else:
        frontmatter[target_field] = op.after

    new_content = _render_markdown(frontmatter, parsed.body)
    target_path.write_text(new_content, encoding="utf-8")
    return target_path


def _apply_create_object(
    op: Any, repo_model_path: Path, backup_state: dict[Path, str | None]
) -> Path:
    object_id = op.object_id
    object_type = op.object_type
    if not object_id:
        raise ValueError("create_object requires object_id")
    if not object_type:
        raise ValueError("create_object requires object_type")

    target_dir = _resolve_subfolder(repo_model_path, object_type)
    target_path = target_dir / f"{object_id}.md"

    if not _is_safe_path(target_path, repo_model_path):
        raise ValueError(f"Unsafe path for create_object: {target_path}")

    if target_path.exists():
        raise FileExistsError(f"Cannot create_object: file already exists {target_path}")

    backup_state[target_path] = None

    if isinstance(op.after, dict):
        frontmatter = dict(op.after)
    else:
        frontmatter = {"id": object_id, "type": object_type, "status": "draft"}

    frontmatter.setdefault("id", object_id)
    frontmatter.setdefault("type", object_type)
    frontmatter.setdefault("status", "draft")

    new_content = _render_markdown(frontmatter, None)
    target_path.write_text(new_content, encoding="utf-8")
    return target_path


def _write_audit_event(
    repo_root: Path,
    proposal_id: str,
    changed_files: list[str],
    validation_summary: ValidationSummary,
    event_type: str = "patch_apply",
    status: str | None = None,
    risk_level: str | None = None,
    risk_assessment: dict[str, Any] | None = None,
    approved_change_request_id: str | None = None,
) -> str:
    from modelops_core.reports.audit_service import AuditEventService, create_audit_event

    service = AuditEventService(repo_root)
    outputs: dict[str, Any] = {
        "changed_files": changed_files,
        "validation": {
            "is_valid": validation_summary.is_valid,
            "error_count": validation_summary.error_count,
            "warning_count": validation_summary.warning_count,
            "info_count": validation_summary.info_count,
        },
    }
    if risk_level is not None:
        outputs["risk_level"] = risk_level
    if risk_assessment is not None:
        outputs["risk_assessment"] = risk_assessment
    if approved_change_request_id is not None:
        outputs["approved_change_request_id"] = approved_change_request_id
    event = create_audit_event(
        event_type=event_type,
        actor="system",
        status=status or ("success" if validation_summary.is_valid else "failed"),
        command=f"proposal {event_type.replace('patch_', '')}",
        proposal_id=proposal_id,
        changed_files=changed_files,
        validation_status="valid" if validation_summary.is_valid else "invalid",
        outputs=outputs,
    )
    return service.emit(event)


def _update_proposal_metadata(
    proposal_path: Path, changed_files: list[str], audit_event_id: str
) -> None:
    parsed = parse_file(proposal_path)
    if parsed.frontmatter is None:
        raise ValueError("PatchProposal file has no frontmatter")

    frontmatter = dict(parsed.frontmatter)
    frontmatter["application_status"] = "applied"
    frontmatter["applied_at"] = _now_iso()
    frontmatter["applied_by"] = "system"
    frontmatter["applied_changed_files"] = changed_files
    frontmatter["applied_audit_event_id"] = audit_event_id

    new_content = _render_markdown(frontmatter, parsed.body)
    proposal_path.write_text(new_content, encoding="utf-8")


def _rollback(backup_state: dict[Path, str | None]) -> None:
    for path, original in backup_state.items():
        if original is None:
            if path.exists():
                path.unlink()
        else:
            path.write_text(original, encoding="utf-8")


def _write_dry_run_audit_event(
    repo_root: Path,
    proposal_id: str,
    result: DryRunResult,
) -> None:
    from modelops_core.reports.audit_service import AuditEventService, create_audit_event

    service = AuditEventService(repo_root)
    changed_object_ids = [
        p.get("object_id", "") for p in result.operations_preview if p.get("object_id")
    ]
    event = create_audit_event(
        event_type="patch_dry_run",
        actor="system",
        status="success" if not result.error else "failed",
        command="proposal apply --dry-run",
        proposal_id=proposal_id,
        changed_object_ids=changed_object_ids,
        outputs={
            "would_change": result.would_change,
            "operations_count": len(result.operations_preview),
            "error": result.error,
        },
    )
    service.emit(event)


def dry_run_patch_proposal(repo_model_path: Path, proposal_id: str) -> DryRunResult:
    """Preview what apply_patch_proposal would do without writing any files."""
    proposal_path = repo_model_path / "patch-proposals" / f"{proposal_id}.md"
    if not proposal_path.exists():
        return DryRunResult(
            proposal_id=proposal_id,
            would_change=False,
            error=f"PatchProposal not found: {proposal_path}",
        )

    parsed_proposal = parse_file(proposal_path)
    fm = parsed_proposal.frontmatter or {}

    if fm.get("status") != "accepted":
        return DryRunResult(
            proposal_id=proposal_id,
            would_change=False,
            error=(
                f"PatchProposal '{proposal_id}' has status '{fm.get('status')}'. "
                "Only 'accepted' proposals can be applied."
            ),
        )

    operations_raw = fm.get("operations", [])
    if not isinstance(operations_raw, list):
        return DryRunResult(
            proposal_id=proposal_id,
            would_change=False,
            error="PatchProposal operations must be a list",
        )

    class _Op:
        def __init__(self, data: dict[str, Any]) -> None:
            self.op: str = data.get("op", "")
            self.object_id: str | None = data.get("object_id")
            self.object_type: str | None = data.get("object_type")
            self.target_path: str | None = data.get("target_path")
            self.after: Any = data.get("after")
            self.before: Any = data.get("before")
            self.reason: str | None = data.get("reason")

    operations = [_Op(op) for op in operations_raw if isinstance(op, dict)]
    preview: list[dict[str, Any]] = []

    current_objects = [parse_file(f) for f in scan_repository(repo_model_path)]
    config = load_repo_config(repo_model_path.parent)
    enabled_packs = config.enabled_domain_packs if config else None

    for op in operations:
        if op.op not in _SUPPORTED_OPERATIONS:
            preview.append(
                {
                    "op": op.op,
                    "status": "skipped",
                    "reason": f"Operation '{op.op}' is not supported.",
                }
            )
            continue

        canonical_op = _normalize_operation_name(op.op)
        if canonical_op == "create_object" and op.op == "create_issue" and not op.object_type:
            op.object_type = "Issue"

        if canonical_op == "update_object":
            target_path = _find_object_file(repo_model_path, op.object_id or "")
            if target_path is None:
                preview.append(
                    {
                        "op": "update_object",
                        "object_id": op.object_id,
                        "status": "error",
                        "reason": f"Object '{op.object_id}' not found",
                    }
                )
                continue
        elif canonical_op == "create_object":
            target_dir = _resolve_subfolder(repo_model_path, op.object_type)
            target_path = target_dir / f"{op.object_id}.md"

        # Run pre-write validation for this operation
        try:
            if canonical_op == "update_object":
                candidate = _build_candidate_update_object(op, repo_model_path)
            else:
                candidate = _build_candidate_create_object(op, repo_model_path)
        except ValueError as exc:
            preview.append(
                {
                    "op": op.op,
                    "object_id": op.object_id,
                    "status": "error",
                    "reason": str(exc),
                }
            )
            continue

        candidate_objects = _integrate_candidate(current_objects, candidate)
        pre_summary = validate_objects(candidate_objects, enabled_packs)

        validation_preview: dict[str, Any] = {
            "is_valid": pre_summary.is_valid,
            "error_count": pre_summary.error_count,
            "warning_count": pre_summary.warning_count,
        }

        if not pre_summary.is_valid:
            error_details = "; ".join(
                f"{r.code}: {r.message}"
                for r in pre_summary.results
                if r.severity == ValidationSeverity.ERROR
            )
            preview.append(
                {
                    "op": op.op,
                    "object_id": op.object_id,
                    "status": "validation_error",
                    "reason": error_details,
                    "validation": validation_preview,
                    "file": str(target_path),
                }
            )
            continue

        if canonical_op == "update_object":
            preview.append(
                {
                    "op": "update_object",
                    "object_id": op.object_id,
                    "status": "would_update",
                    "file": str(target_path),
                    "field": op.target_path,
                    "after": op.after,
                    "validation": validation_preview,
                }
            )
        elif canonical_op == "create_object":
            preview.append(
                {
                    "op": "create_object",
                    "object_id": op.object_id,
                    "object_type": op.object_type,
                    "status": "would_create",
                    "file": str(target_path),
                    "validation": validation_preview,
                }
            )

        current_objects = candidate_objects

    result = DryRunResult(
        proposal_id=proposal_id,
        would_change=any(p["status"] in {"would_update", "would_create"} for p in preview),
        operations_preview=preview,
    )

    _write_dry_run_audit_event(repo_model_path.parent, proposal_id, result)
    return result


def apply_patch_proposal(
    repo_model_path: Path,
    proposal_id: str,
    skip_risk_check: bool = False,
    approved_change_request_id: str | None = None,
) -> ApplyResult:
    """Apply an accepted PatchProposal to canonical model files."""
    if not repo_model_path.exists():
        raise FileNotFoundError(f"Repository path not found: {repo_model_path}")

    proposal_path = repo_model_path / "patch-proposals" / f"{proposal_id}.md"
    if not proposal_path.exists():
        raise FileNotFoundError(f"PatchProposal not found: {proposal_path}")

    parsed_proposal = parse_file(proposal_path)
    fm = parsed_proposal.frontmatter or {}

    if fm.get("status") != "accepted":
        raise ValueError(
            f"PatchProposal '{proposal_id}' has status '{fm.get('status')}'. "
            "Only 'accepted' proposals can be applied."
        )

    if fm.get("application_status") == "applied" or fm.get("applied_at"):
        raise ValueError(
            f"PatchProposal '{proposal_id}' has already been applied at {fm.get('applied_at')}."
        )

    operations_raw = fm.get("operations", [])
    if not isinstance(operations_raw, list):
        raise ValueError("PatchProposal operations must be a list")

    # Pre-apply proposal validation
    from modelops_core.patching.patch_validator import validate_patch_proposal

    proposal_dict = dict(fm)
    proposal_dict.setdefault("id", proposal_id)
    proposal_dict.setdefault("type", "PatchProposal")
    validation_results = validate_patch_proposal(proposal_dict)
    proposal_errors = [r for r in validation_results if r.severity == ValidationSeverity.ERROR]
    if proposal_errors:
        error_details = "; ".join(f"{r.code}: {r.message}" for r in proposal_errors)
        raise ValueError(f"Proposal validation failed for '{proposal_id}'. Errors: {error_details}")

    class _Op:
        def __init__(self, data: dict[str, Any]) -> None:
            self.op: str = data.get("op", "")
            self.object_id: str | None = data.get("object_id")
            self.object_type: str | None = data.get("object_type")
            self.target_path: str | None = data.get("target_path")
            self.after: Any = data.get("after")
            self.before: Any = data.get("before")
            self.reason: str | None = data.get("reason")

    operations = [_Op(op) for op in operations_raw if isinstance(op, dict)]

    # Risk assessment
    risk = compute_proposal_risk([op.__dict__ for op in operations], repo_model_path)
    if risk.risk_level == "high" and not skip_risk_check:
        raise ValueError(
            f"High-risk proposal blocked (level: {risk.risk_level}). "
            f"Reasons: {'; '.join(risk.risk_reasons)}. "
            "Use --skip-risk-check to override."
        )

    backup_state: dict[Path, str | None] = {}
    changed_files: list[str] = []
    pre_write_warnings: list[str] = []

    current_objects = [parse_file(f) for f in scan_repository(repo_model_path)]
    config = load_repo_config(repo_model_path.parent)
    enabled_packs = config.enabled_domain_packs if config else None

    try:
        for op in operations:
            if op.op not in _SUPPORTED_OPERATIONS:
                raise ValueError(
                    f"Operation '{op.op}' is not supported."
                    f" Supported: {', '.join(sorted(_SUPPORTED_OPERATIONS))}."
                )

            canonical_op = _normalize_operation_name(op.op)
            if canonical_op == "create_object" and op.op == "create_issue" and not op.object_type:
                op.object_type = "Issue"

            if canonical_op == "update_object":
                candidate = _build_candidate_update_object(op, repo_model_path)
            elif canonical_op == "create_object":
                candidate = _build_candidate_create_object(op, repo_model_path)
            else:
                continue  # unreachable due to check above

            candidate_objects = _integrate_candidate(current_objects, candidate)
            pre_summary = validate_objects(candidate_objects, enabled_packs)

            if not pre_summary.is_valid:
                error_details = "; ".join(
                    f"{r.code}: {r.message}"
                    for r in pre_summary.results
                    if r.severity == ValidationSeverity.ERROR
                )
                raise ValueError(
                    f"Pre-write validation failed for operation '{op.op}' on "
                    f"'{op.object_id}': {pre_summary.error_count} error(s). {error_details}"
                )

            if pre_summary.warning_count > 0:
                pre_write_warnings.extend(
                    f"{r.code}: {r.message}"
                    for r in pre_summary.results
                    if r.severity == ValidationSeverity.WARNING
                )

            if canonical_op == "update_object":
                modified_path = _apply_update_object(op, repo_model_path, backup_state)
                changed_files.append(str(modified_path.resolve()))
            elif canonical_op == "create_object":
                created_path = _apply_create_object(op, repo_model_path, backup_state)
                changed_files.append(str(created_path.resolve()))

            current_objects = candidate_objects

        files = scan_repository(repo_model_path)
        parsed_objects = [parse_file(f) for f in files]
        validation_summary = validate_objects(parsed_objects, enabled_packs)

        if not validation_summary.is_valid:
            _rollback(backup_state)
            raise ValueError(
                f"Post-apply validation failed with {validation_summary.error_count} error(s). "
                "All changes have been rolled back."
            )

        repo_root = repo_model_path.parent
        audit_event_id = _write_audit_event(
            repo_root,
            proposal_id,
            changed_files,
            validation_summary,
            risk_level=risk.risk_level,
            risk_assessment={
                "requires_approval": risk.requires_approval,
                "risk_level": risk.risk_level,
                "risk_reasons": risk.risk_reasons,
                "triggering_rules": risk.triggering_rules,
                "affected_object_count": risk.affected_object_count,
                "max_impact_depth": risk.max_impact_depth,
            },
            approved_change_request_id=approved_change_request_id,
        )

        _update_proposal_metadata(proposal_path, changed_files, audit_event_id)

        db_path = resolve_generated_path(repo_root) / "modelops.db"
        index_rebuilt = False
        try:
            build_index(repo_root=repo_root, db_path=db_path, allow_invalid=False)
            index_rebuilt = True
        except Exception:
            pass

        return ApplyResult(
            proposal_id=proposal_id,
            proposal_status="accepted",
            application_status="applied",
            changed_files=changed_files,
            validation={
                "is_valid": validation_summary.is_valid,
                "error_count": validation_summary.error_count,
                "warning_count": validation_summary.warning_count,
                "info_count": validation_summary.info_count,
            },
            audit_event_written=True,
            index_rebuilt=index_rebuilt,
            db_path=str(db_path.resolve()) if index_rebuilt else None,
            risk_level=risk.risk_level,
            approved_change_request_id=approved_change_request_id,
            pre_write_warnings=pre_write_warnings,
            risk_assessment={
                "requires_approval": risk.requires_approval,
                "risk_level": risk.risk_level,
                "risk_reasons": risk.risk_reasons,
                "triggering_rules": risk.triggering_rules,
                "affected_object_count": risk.affected_object_count,
                "max_impact_depth": risk.max_impact_depth,
            },
        )

    except ValueError:
        _rollback(backup_state)
        raise
