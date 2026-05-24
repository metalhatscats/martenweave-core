"""High-level service for building patch proposals from notes."""

from __future__ import annotations

from typing import Any

from modelops_core.ai.provider_adapter import (
    AIContextBundle,
    NoProviderAdapter,
    ProviderOutputValidator,
)

_DEFAULT_ADAPTER = NoProviderAdapter()
_DEFAULT_VALIDATOR = ProviderOutputValidator()


def build_patch_proposal_from_note(
    note: str,
    include_raw_samples: bool = False,
) -> dict[str, Any]:
    """Build a PatchProposal from a free-text note.

    Uses the default NoProviderAdapter if no external AI provider is configured.
    """
    context = AIContextBundle(
        note=note,
        include_raw_samples=include_raw_samples,
    )

    candidates = _DEFAULT_ADAPTER.generate_candidates(context)
    if not candidates:
        return {
            "is_safe": False,
            "proposal": None,
            "validation": [],
            "markdown": "",
            "assumptions": ["No candidates generated."],
            "human_checks": ["Please refine the note and try again."],
        }

    candidate = candidates[0]
    validated = _DEFAULT_VALIDATOR.validate(candidate)
    result = _DEFAULT_VALIDATOR.to_patch_proposal(validated["candidate"])
    return result
