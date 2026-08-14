"""Read the persisted first-value result of a ``martenweave start`` workspace.

The start command writes a run-scoped readiness report plus a manifest with the
authoritative verdict and finding count.  This loader surfaces exactly those
persisted artifacts — it never recomputes, samples, or fabricates a result.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from modelops_core.config import resolve_generated_path
from modelops_core.run.dataset_readiness import (
    DatasetReadinessReport,
    _recommended_next_action,
)


def load_start_result(repo_root: Path) -> dict[str, Any] | None:
    """Return the persisted start-run result, or ``None`` when none exists.

    A workspace has a start result only when both ``start_manifest.json`` and
    the run-scoped ``readiness/readiness.json`` are present and parseable.
    Absolute local input paths are reduced to a file name so callers never
    expose unsafe paths.
    """
    generated_root = resolve_generated_path(repo_root)
    manifest_path = generated_root / "start_manifest.json"
    report_path = generated_root / "readiness" / "readiness.json"
    if not manifest_path.is_file() or not report_path.is_file():
        return None
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        report_payload = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    readiness = manifest.get("readiness") or {}
    gap_dicts = list(report_payload.get("dataset_gaps") or []) + list(
        report_payload.get("model_gaps") or []
    )
    findings = [gap["finding"] for gap in gap_dicts if isinstance(gap.get("finding"), dict)]

    next_action: str | None = None
    try:
        report = DatasetReadinessReport(**report_payload)
        next_action = _recommended_next_action(report)
    except (TypeError, KeyError):
        # The persisted report predates the typed contract; fall back to the
        # manifest summary without inventing an action.
        next_action = None

    generated_outputs = manifest.get("generated_outputs") or {}

    def _artifact_id(workspace_relative: str | None) -> str | None:
        """Reduce a workspace-relative output path to a generated-relative artifact id."""
        if not workspace_relative:
            return None
        parts = Path(workspace_relative).parts
        if parts and parts[0] == generated_root.name:
            return Path(*parts[1:]).as_posix()
        return Path(workspace_relative).as_posix()

    input_info = manifest.get("input") or {}
    input_path = input_info.get("path")
    return {
        "verdict": readiness.get("verdict") or report_payload.get("verdict"),
        "total_findings": readiness.get("total_findings", len(findings)),
        "dataset_gaps": readiness.get("dataset_gaps", 0),
        "model_gaps": readiness.get("model_gaps", 0),
        "validation_errors": readiness.get("validation_errors", 0),
        "validation_warnings": readiness.get("validation_warnings", 0),
        "recommended_next_action": next_action,
        "findings": findings,
        "evidence": {
            "readiness_json": _artifact_id(generated_outputs.get("readiness_json")),
            "readiness_markdown": _artifact_id(generated_outputs.get("readiness_markdown")),
            "profile": _artifact_id(generated_outputs.get("profile")),
            # The draft proposal is a canonical PatchProposal object, not a
            # generated artifact; expose its workspace-relative reference only.
            "draft_proposal": generated_outputs.get("draft_proposal"),
        },
        "provenance": {
            "created_at": manifest.get("created_at"),
            "input_name": Path(input_path).name if input_path else None,
            "input_format": input_info.get("format"),
            "input_sha256": input_info.get("sha256"),
            "tool_version": report_payload.get("martenweave_version"),
        },
    }
