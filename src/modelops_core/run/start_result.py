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


def _decision_gate(
    generated_root: Path,
    manifest: dict[str, Any],
    report_payload: dict[str, Any],
) -> dict[str, Any]:
    """Summarize whether a start-run proposal has enough human evidence review.

    The gate is intentionally narrower than migration readiness: it only proves
    that every deterministic finding has been classified by a human and that no
    item was explicitly deferred. It does not claim that confirmed gaps are fixed.
    """
    findings_path = generated_root / "readiness" / "findings.json"
    reviews_path = generated_root / "readiness" / "finding-reviews.json"
    findings: list[dict[str, Any]] = []
    if findings_path.is_file():
        try:
            findings = list(
                json.loads(findings_path.read_text(encoding="utf-8")).get("findings") or []
            )
        except (OSError, json.JSONDecodeError):
            findings = []
    if not findings:
        gaps = list(report_payload.get("dataset_gaps") or []) + list(
            report_payload.get("model_gaps") or []
        )
        findings = [gap["finding"] for gap in gaps if isinstance(gap.get("finding"), dict)]

    reviews: dict[str, Any] = {}
    if reviews_path.is_file():
        try:
            reviews = (
                json.loads(reviews_path.read_text(encoding="utf-8")).get("reviews") or {}
            )
        except (OSError, json.JSONDecodeError):
            reviews = {}

    finding_ids = list(
        dict.fromkeys(str(finding.get("id")) for finding in findings if finding.get("id"))
    )
    reviewed_ids = [finding_id for finding_id in finding_ids if finding_id in reviews]
    deferred_ids = [
        finding_id
        for finding_id in reviewed_ids
        if reviews[finding_id].get("disposition") == "deferred"
    ]
    unreviewed_ids = [finding_id for finding_id in finding_ids if finding_id not in reviews]
    ready = not unreviewed_ids and not deferred_ids
    if unreviewed_ids:
        gate_reason = f"Classify {len(unreviewed_ids)} remaining evidence finding(s)."
    elif deferred_ids:
        gate_reason = f"Resolve {len(deferred_ids)} deferred finding(s) before approval."
    else:
        gate_reason = "Every deterministic finding has a recorded human disposition."

    proposal_ref = (manifest.get("generated_outputs") or {}).get("draft_proposal")
    proposal_id = Path(proposal_ref).stem if proposal_ref else None
    return {
        "total": len(finding_ids),
        "reviewed": len(reviewed_ids),
        "remaining": len(unreviewed_ids),
        "deferred": len(deferred_ids),
        "proposal_review_ready": ready,
        "gate_reason": gate_reason,
        "assessment_id": "readiness",
        "proposal_id": proposal_id,
    }


def load_start_decision_gate(
    repo_root: Path, proposal_id: str | None = None
) -> dict[str, Any] | None:
    """Return the human-evidence gate for the persisted start-run proposal."""
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
    gate = _decision_gate(generated_root, manifest, report_payload)
    if proposal_id is not None and gate["proposal_id"] != proposal_id:
        return None
    return gate


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
    findings_by_id = {
        str(gap["finding"].get("id")): gap["finding"]
        for gap in gap_dicts
        if isinstance(gap.get("finding"), dict) and gap["finding"].get("id")
    }
    findings = list(findings_by_id.values())

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
    canonical_model = manifest.get("canonical_model") or {}
    input_path = input_info.get("path")
    decision_gate = _decision_gate(generated_root, manifest, report_payload)
    if decision_gate["remaining"]:
        next_action = decision_gate["gate_reason"]
    elif decision_gate["proposal_review_ready"] and decision_gate["proposal_id"]:
        next_action = "Review the candidate proposal against the recorded human dispositions."
    return {
        "verdict": readiness.get("verdict") or report_payload.get("verdict"),
        "total_findings": len(findings),
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
            "model_context": canonical_model.get("template") or "new workspace seed",
            "context_domain": canonical_model.get("context_domain"),
        },
        "decision_gate": decision_gate,
    }
