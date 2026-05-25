"""ADK-compatible tool wrappers around existing Martenweave services.

Each tool returns structured JSON. None mutate canonical files directly.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from modelops_core.change_request.service import create_change_request
from modelops_core.config import resolve_generated_path, resolve_model_path
from modelops_core.index import build_index
from modelops_core.notifications.preview_service import preview_notifications
from modelops_core.patching.patch_proposal_service import (
    build_patch_proposal,
    write_patch_proposal,
)
from modelops_core.repository import parse_file, scan_repository
from modelops_core.trace import trace_object
from modelops_core.validation import validate_objects

_TOOL_DOC_VALIDATE = """Run deterministic validation on a model repository.

Args:
    repo_root: Path to the model repository root.

Returns:
    JSON with is_valid, error_count, warning_count, and results.
"""

_TOOL_DOC_BUILD_INDEX = """Build SQLite index from canonical files.

Args:
    repo_root: Path to the model repository root.
    export_jsonl: Whether to export JSONL files.

Returns:
    JSON with build status and object count.
"""

_TOOL_DOC_TRACE = """Trace upstream and downstream relationships for an object.

Args:
    repo_root: Path to the model repository root.
    object_id: Object ID to trace from.
    direction: upstream, downstream, or both.
    max_depth: Maximum traversal depth.

Returns:
    JSON with nodes and edges.
"""

_TOOL_DOC_PROFILE_DATASET = """Profile a dataset file (CSV or XLSX).

Args:
    file_path: Path to the dataset file.
    dataset_id: Identifier for the dataset.

Returns:
    JSON profile with columns, types, and row counts.
"""

_TOOL_DOC_CREATE_PROPOSAL = """Create a PatchProposal from operations.

Args:
    repo_root: Path to the model repository root.
    proposal_id: Unique proposal ID.
    operations: List of patch operations.
    affected_objects: Optional list of affected object IDs.
    source_evidence: Optional evidence text.

Returns:
    JSON with proposal details and validation status.
"""

_TOOL_DOC_CREATE_CHANGE_REQUEST = """Create a ChangeRequest canonical file.

Args:
    repo_root: Path to the model repository root.
    cr_id: ChangeRequest ID.
    title: ChangeRequest title.
    affected_objects: List of affected object IDs.
    linked_proposals: Optional linked proposal IDs.
    requester: Optional requester ID.
    reason: Optional reason text.

Returns:
    JSON with ChangeRequest details.
"""

_TOOL_DOC_PREVIEW_NOTIFICATIONS = (
    "Preview notification recipients for a ChangeRequest or PatchProposal.\n"
    "\n"
    "Args:\n"
    "    repo_root: Path to the model repository root.\n"
    "    change_request: Optional ChangeRequest ID.\n"
    "    proposal: Optional PatchProposal ID.\n"
    "\n"
    "Returns:\n"
    "    JSON list of recipient entries.\n"
)


def validate_model_tool(repo_root: str) -> dict[str, Any]:
    """Run deterministic validation on a model repository."""
    model_path = resolve_model_path(Path(repo_root))
    files = scan_repository(model_path)
    parsed_objects = [parse_file(f) for f in files]
    summary = validate_objects(parsed_objects)

    return {
        "is_valid": summary.is_valid,
        "error_count": summary.error_count,
        "warning_count": summary.warning_count,
        "info_count": summary.info_count,
        "results": [
            {
                "severity": str(r.severity),
                "code": r.code,
                "object_id": r.object_id,
                "message": r.message,
                "suggested_fix": r.suggested_fix,
            }
            for r in summary.results[:50]
        ],
    }


def build_index_tool(repo_root: str, export_jsonl: bool = False) -> dict[str, Any]:
    """Build SQLite index from canonical files."""
    repo_path = Path(repo_root)
    db_path = resolve_generated_path(repo_path) / "modelops.db"

    summary = build_index(
        repo_root=repo_path,
        db_path=db_path,
        export_jsonl=export_jsonl,
    )

    return {
        "built": True,
        "db_path": str(db_path),
        "is_valid": summary.is_valid,
        "object_count": len(scan_repository(resolve_model_path(repo_path))),
    }


def trace_object_tool(
    repo_root: str,
    object_id: str,
    direction: str = "both",
    max_depth: int = 5,
) -> dict[str, Any]:
    """Trace upstream and downstream relationships for an object."""
    repo_path = Path(repo_root)
    db_path = resolve_generated_path(repo_path) / "modelops.db"

    if not db_path.exists():
        return {
            "error": "Index not found. Run build_index first.",
        }

    result = trace_object(db_path, object_id, max_depth=max_depth, direction=direction)

    return {
        "root_object_id": result.root_object_id,
        "root_object_type": result.root_object_type,
        "root_object_name": result.root_object_name,
        "nodes": [
            {
                "object_id": n.object_id,
                "object_type": n.object_type,
                "object_name": n.object_name,
                "depth": n.depth,
            }
            for n in result.nodes
        ],
        "edges": [
            {
                "from_object_id": e.from_object_id,
                "to_object_id": e.to_object_id,
                "relationship_type": e.relationship_type,
                "direction": e.direction,
            }
            for e in result.edges
        ],
    }


def profile_dataset_tool(file_path: str, dataset_id: str | None = None) -> dict[str, Any]:
    """Profile a dataset file (CSV or XLSX)."""
    from modelops_core.imports import profile_csv, profile_xlsx

    path = Path(file_path)
    if not path.exists():
        return {"error": f"File not found: {file_path}"}

    suffix = path.suffix.lower()
    dataset_id = dataset_id or path.stem

    if suffix == ".csv":
        profile = profile_csv(path, dataset_id=dataset_id)
    elif suffix in {".xlsx", ".xls"}:
        profile = profile_xlsx(path, dataset_id=dataset_id)
    else:
        return {"error": f"Unsupported format: {suffix}"}

    return {
        "dataset_id": dataset_id,
        "file_path": str(path),
        "row_count": getattr(profile, "row_count", None),
        "column_count": getattr(profile, "column_count", None),
        "columns": [
            {
                "name": col.name,
                "inferred_type": col.inferred_type,
                "blank_count": col.blank_count,
                "distinct_count": col.distinct_count,
                "sample_values": col.sample_values,
            }
            for col in getattr(profile, "columns", [])
        ],
    }


def create_patch_proposal_tool(
    repo_root: str,
    proposal_id: str,
    operations: list[dict[str, Any]],
    affected_objects: list[str] | None = None,
    source_evidence: str | None = None,
) -> dict[str, Any]:
    """Create a PatchProposal from operations and write to model/patch-proposals/."""
    from modelops_core.patching.patch_model import PatchOperation

    model_path = resolve_model_path(Path(repo_root))
    ops = [PatchOperation(**op) for op in operations]

    proposal = build_patch_proposal(
        proposal_id=proposal_id,
        operations=ops,
        affected_objects=affected_objects,
        source_evidence=source_evidence,
        created_by="adk-agent",
    )

    from modelops_core.patching.patch_validator import validate_patch_proposal

    validation_results = validate_patch_proposal(proposal)
    proposal["validation_status"] = (
        "valid" if not any(v.severity == "ERROR" for v in validation_results) else "invalid"
    )

    path = write_patch_proposal(proposal, model_path)

    return {
        "proposal_id": proposal_id,
        "path": str(path),
        "operations_count": len(operations),
        "validation_status": proposal["validation_status"],
        "affected_objects": affected_objects or [],
    }


def create_change_request_tool(
    repo_root: str,
    cr_id: str,
    title: str,
    affected_objects: list[str] | None = None,
    linked_proposals: list[str] | None = None,
    requester: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    """Create a ChangeRequest canonical file."""
    model_path = resolve_model_path(Path(repo_root))

    path = create_change_request(
        model_path=model_path,
        cr_id=cr_id,
        title=title,
        affected_objects=affected_objects,
        linked_proposals=linked_proposals,
        requester=requester,
        reason=reason,
    )

    return {
        "cr_id": cr_id,
        "title": title,
        "path": str(path),
        "status": "pending",
        "affected_objects": affected_objects or [],
        "linked_proposals": linked_proposals or [],
    }


def preview_notifications_tool(
    repo_root: str,
    change_request: str | None = None,
    proposal: str | None = None,
) -> dict[str, Any]:
    """Preview notification recipients for a ChangeRequest or PatchProposal."""
    model_path = resolve_model_path(Path(repo_root))

    entries = preview_notifications(
        model_path=model_path,
        cr_id=change_request,
        proposal_id=proposal,
    )

    return {
        "recipient_count": len(entries),
        "recipients": [
            {
                "recipient_id": e.recipient_id,
                "recipient_role": e.recipient_role,
                "reason": e.reason,
                "source_object_id": e.source_object_id,
            }
            for e in entries
        ],
    }


# Registry of all available tools
TOOL_REGISTRY: dict[str, Any] = {
    "validate_model": validate_model_tool,
    "build_index": build_index_tool,
    "trace_object": trace_object_tool,
    "profile_dataset": profile_dataset_tool,
    "create_patch_proposal": create_patch_proposal_tool,
    "create_change_request": create_change_request_tool,
    "preview_notifications": preview_notifications_tool,
}
