"""Shared helpers for building and parsing AI candidate outputs."""

from __future__ import annotations

import json
from typing import Any

from modelops_core.ai.provider_adapter import (
    AICandidateOutput,
    AIContextBundle,
    AIOutputValidationError,
)

_SYSTEM_PROMPT = (
    "You are a data modeling assistant. "
    "Generate structured patch proposals for master data model changes. "
    "Respond with valid JSON only."
)

_CANDIDATE_SCHEMA = {
    "type": "object",
    "properties": {
        "proposal_id": {"type": "string"},
        "title": {"type": "string"},
        "operations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "op": {"type": "string"},
                    "object_id": {"type": "string"},
                    "object_type": {"type": "string"},
                    "target_path": {"type": "string"},
                    "after": {},
                },
                "required": ["op", "object_id"],
            },
        },
        "affected_objects": {
            "type": "array",
            "items": {"type": "string"},
        },
        "assumptions": {
            "type": "array",
            "items": {"type": "string"},
        },
        "human_checks": {
            "type": "array",
            "items": {"type": "string"},
        },
        "source_evidence": {"type": "string"},
    },
    "required": ["proposal_id", "title", "operations"],
}


def _build_prompt(context: AIContextBundle) -> str:
    lines = [
        "Generate a patch proposal based on the following note.",
        "",
        f"Note: {context.note}",
    ]
    if context.domain:
        lines.append(f"Domain: {context.domain}")
    if context.affected_object_ids:
        lines.append(f"Known affected objects: {', '.join(context.affected_object_ids)}")
    if context.dataset_columns:
        lines.append(f"Dataset columns: {', '.join(context.dataset_columns)}")
    if context.dataset_row_count is not None:
        lines.append(f"Dataset rows: {context.dataset_row_count}")
    if context.repository_context:
        lines.append("")
        lines.append("Repository context (canonical objects, relationships, validation summary):")
        lines.append(json.dumps(context.repository_context, indent=2, default=str))
    lines.append("")
    lines.append("Respond with JSON matching this schema:")
    lines.append(json.dumps(_CANDIDATE_SCHEMA, indent=2))
    return "\n".join(lines)


def _parse_candidate(raw: dict[str, Any]) -> AICandidateOutput:
    """Parse a raw dict into AICandidateOutput, raising on schema violations."""
    proposal_id = raw.get("proposal_id")
    title = raw.get("title")
    operations = raw.get("operations")

    if not proposal_id or not isinstance(proposal_id, str):
        raise AIOutputValidationError("Missing or invalid proposal_id")
    if not title or not isinstance(title, str):
        raise AIOutputValidationError("Missing or invalid title")
    if not operations or not isinstance(operations, list):
        raise AIOutputValidationError("Missing or invalid operations")

    return AICandidateOutput(
        proposal_id=proposal_id,
        title=title,
        operations=[dict(op) for op in operations],
        affected_objects=list(raw.get("affected_objects", [])),
        assumptions=list(raw.get("assumptions", [])),
        human_checks=list(raw.get("human_checks", [])),
        source_evidence=raw.get("source_evidence"),
    )
