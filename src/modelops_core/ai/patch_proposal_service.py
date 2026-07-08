"""High-level service for building patch proposals from notes."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from modelops_core.ai.provider_adapter import (
    AIContextBundle,
    AIProviderAdapter,
    NoProviderAdapter,
    ProviderOutputValidator,
)
from modelops_core.ai.provider_router import ProviderRouter

_DEFAULT_VALIDATOR = ProviderOutputValidator()


_KNOWN_PROVIDERS = ["no_provider", "kimi", "openai", "ollama"]


def _build_provider_adapter(name: str) -> AIProviderAdapter:
    """Construct a single provider adapter by name."""
    if name == "no_provider":
        return NoProviderAdapter()
    if name == "kimi":
        from modelops_core.ai.kimi_adapter import KimiAdapter

        return KimiAdapter()
    if name == "openai":
        from modelops_core.ai.openai_compatible_adapter import OpenAICompatibleAdapter

        return OpenAICompatibleAdapter()
    if name == "ollama":
        from modelops_core.ai.ollama_adapter import OllamaAdapter

        return OllamaAdapter()
    raise ValueError(
        f"Unknown AI provider '{name}'. "
        f"Known providers: {', '.join(_KNOWN_PROVIDERS)}."
    )


def _get_default_adapter(repo_root: Path | None = None) -> AIProviderAdapter:
    """Resolve the default AI provider adapter from environment or repo config."""
    provider = os.getenv("MARTENWEAVE_AI_PROVIDER")

    if provider is None and repo_root is not None:
        from modelops_core.config import load_repo_config

        config = load_repo_config(repo_root)
        if config is not None and config.ai is not None:
            providers = config.ai.get("providers")
            if isinstance(providers, list):
                provider = ",".join(str(p) for p in providers if p)

    if provider is None:
        provider = "no_provider"

    names = [p.strip() for p in provider.split(",") if p.strip()]
    if len(names) > 1:
        adapters = [_build_provider_adapter(name) for name in names]
        return ProviderRouter(
            primary=adapters[0],
            fallbacks=adapters[1:],
            primary_name=names[0],
            fallback_names=names[1:],
        )

    return _build_provider_adapter(names[0])


_ID_PATTERN = re.compile(r"[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*")


def _extract_object_ids(note: str) -> list[str]:
    """Extract candidate canonical object IDs from a free-text note."""
    return list({m for m in _ID_PATTERN.findall(note) if len(m) >= 3})


def build_patch_proposal_from_note(
    note: str,
    include_raw_samples: bool = False,
    adapter: AIProviderAdapter | None = None,
    repo_root: Path | None = None,
    command: str = "propose-patch",
) -> dict[str, Any]:
    """Build a PatchProposal from a free-text note.

    Uses the configured provider adapter (default: NoProviderAdapter).
    Set MARTENWEAVE_AI_PROVIDER=kimi to use Kimi/Moonshot.

    Args:
        note: Free-text description of the desired model change.
        include_raw_samples: Whether to include raw dataset samples in context.
        adapter: Optional provider adapter to use instead of the default.
        repo_root: Optional repository root. When provided, repository context
            is loaded and telemetry is recorded for the call.
        command: Command name to record in telemetry when repo_root is given.
            Defaults to "propose-patch"; MCP callers should pass the tool name.
    """
    context = AIContextBundle(
        note=note,
        include_raw_samples=include_raw_samples,
    )

    if repo_root is not None:
        from modelops_core.ai.context_builder import build_context_bundle
        from modelops_core.config import resolve_generated_path

        db_path = resolve_generated_path(repo_root) / "modelops.db"
        target_object_ids = _extract_object_ids(note)
        bundle = build_context_bundle(
            db_path=db_path,
            workflow="proposal-review",
            target_object_ids=target_object_ids,
            token_budget=context.max_context_length,
        )
        context.repository_context = {
            "metadata": bundle.to_metadata(),
            "included_objects": bundle.included_objects,
            "relationship_refs": bundle.relationship_refs,
            "validation_summary": bundle.validation_summary,
            "warnings": bundle.warnings,
        }

    if adapter is None:
        adapter = _get_default_adapter(repo_root=repo_root)

    if repo_root is not None:
        from modelops_core.telemetry.ai_usage import wrap_ai_adapter

        adapter = wrap_ai_adapter(adapter, repo_root=repo_root, command=command)

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
