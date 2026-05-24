"""High-level service for building patch proposals from notes."""

from __future__ import annotations

import os
from typing import Any

from modelops_core.ai.provider_adapter import (
    AIContextBundle,
    AIProviderAdapter,
    NoProviderAdapter,
    ProviderOutputValidator,
)

_DEFAULT_VALIDATOR = ProviderOutputValidator()


def _get_default_adapter() -> AIProviderAdapter:
    """Resolve the default AI provider adapter from environment."""
    provider = os.getenv("MARTENWEAVE_AI_PROVIDER", "no_provider")
    if provider == "kimi":
        from modelops_core.ai.kimi_adapter import KimiAdapter

        return KimiAdapter()
    return NoProviderAdapter()


def build_patch_proposal_from_note(
    note: str,
    include_raw_samples: bool = False,
    adapter: AIProviderAdapter | None = None,
) -> dict[str, Any]:
    """Build a PatchProposal from a free-text note.

    Uses the configured provider adapter (default: NoProviderAdapter).
    Set MARTENWEAVE_AI_PROVIDER=kimi to use Kimi/Moonshot.
    """
    context = AIContextBundle(
        note=note,
        include_raw_samples=include_raw_samples,
    )

    if adapter is None:
        adapter = _get_default_adapter()

    candidates = adapter.generate_candidates(context)
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
