"""Deterministic source-state classification utilities."""

from __future__ import annotations

from pathlib import Path

from modelops_core.schemas.common import SourceState


def classify_object_type(object_type: str | None) -> str:
    """Classify a canonical object type into a source state."""
    if not object_type:
        return SourceState.CANONICAL.value
    mapping = {
        "PatchProposal": SourceState.PROPOSAL,
        "ChangeRequest": SourceState.PROPOSAL,
        "Evidence": SourceState.EVIDENCE,
    }
    return mapping.get(object_type, SourceState.CANONICAL).value


def classify_file_path(path: Path) -> str:
    """Classify a canonical file by its path under the model directory."""
    parts = {p.lower() for p in path.parts}
    if "patch-proposals" in parts:
        return SourceState.PROPOSAL.value
    if "change-requests" in parts:
        return SourceState.PROPOSAL.value
    if "evidence" in parts:
        return SourceState.EVIDENCE.value
    return SourceState.CANONICAL.value


def classify_artifact(artifact_path: Path | str) -> str:
    """Classify a generated artifact or file path by name/location."""
    path = Path(artifact_path)
    name = path.name.lower()
    parts = {p.lower() for p in path.parts}

    if name in {"source_registry.jsonl"} or "import-sessions" in parts:
        return SourceState.EVIDENCE.value

    if any(
        token in parts or token in name
        for token in {
            "readiness",
            "gap",
            "assessment",
            "high_risk",
            "impact",
            "validation",
        }
    ):
        return SourceState.FINDING.value

    if "patch-proposals" in parts or "change-requests" in parts:
        return SourceState.PROPOSAL.value

    return SourceState.CANONICAL.value


def classify_dataset_gap(gap_code: str) -> str:
    """Dataset gaps are generated findings, never canonical truth."""
    return SourceState.FINDING.value
