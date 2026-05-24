"""AI adapter and patch proposal generation services."""

from modelops_core.ai.context_builder import ContextBundle, build_context_bundle
from modelops_core.ai.patch_proposal_service import build_patch_proposal_from_note
from modelops_core.ai.prompt_registry import PromptRegistry, PromptTemplate
from modelops_core.ai.provider_adapter import (
    AICandidateOutput,
    AIContextBundle,
    AIProviderAdapter,
    NoProviderAdapter,
    ProviderOutputValidator,
)

__all__ = [
    "AIContextBundle",
    "AIProviderAdapter",
    "AICandidateOutput",
    "ContextBundle",
    "PromptRegistry",
    "PromptTemplate",
    "build_context_bundle",
    "build_patch_proposal_from_note",
    "NoProviderAdapter",
    "ProviderOutputValidator",
]
