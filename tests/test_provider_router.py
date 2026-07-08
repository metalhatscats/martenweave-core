"""Tests for the multi-provider AI router with fallback."""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from modelops_core.ai.patch_proposal_service import _get_default_adapter
from modelops_core.ai.provider_adapter import (
    AICandidateOutput,
    AIContextBundle,
    AIOutputValidationError,
    AIRateLimitError,
    AITimeoutError,
)
from modelops_core.ai.provider_router import ProviderRouter


@dataclass
class MockAdapter:
    """Stub adapter for router testing."""

    name: str
    result: list[AICandidateOutput] | None = None
    exc: Exception | None = None
    calls: list[AIContextBundle] = field(default_factory=list)

    def generate_candidates(self, context: AIContextBundle) -> list[AICandidateOutput]:
        self.calls.append(context)
        if self.exc is not None:
            raise self.exc
        if self.result is None:
            return []
        return self.result


def _candidate(provider: str) -> AICandidateOutput:
    return AICandidateOutput(
        proposal_id=f"PP-{provider.upper()}-001",
        title=f"Proposal from {provider}",
        operations=[{"op": "update_object", "object_id": "DOMAIN-TEST"}],
        affected_objects=["DOMAIN-TEST"],
        assumptions=["Assumption from primary."],
        human_checks=["Check from primary."],
        source_evidence="note",
    )


class TestProviderRouter:
    def test_router_uses_primary_on_success(self) -> None:
        primary = MockAdapter(name="primary", result=[_candidate("primary")])
        fallback = MockAdapter(name="fallback", result=[_candidate("fallback")])
        router = ProviderRouter(primary=primary, fallbacks=[fallback])
        context = AIContextBundle(note="test")

        results = router.generate_candidates(context)

        assert len(results) == 1
        assert results[0].proposal_id == "PP-PRIMARY-001"
        assert len(primary.calls) == 1
        assert len(fallback.calls) == 0
        assert any("Provider attempts: primary (success)" in a for a in results[0].assumptions)
        assert context.repository_context is not None
        assert context.repository_context["provider_attempts"] == [
            {"provider": "primary", "status": "success"}
        ]

    def test_router_falls_back_on_timeout(self) -> None:
        primary = MockAdapter(name="primary", exc=AITimeoutError("primary timed out"))
        fallback = MockAdapter(name="fallback", result=[_candidate("fallback")])
        router = ProviderRouter(primary=primary, fallbacks=[fallback])
        context = AIContextBundle(note="test")

        results = router.generate_candidates(context)

        assert len(results) == 1
        assert results[0].proposal_id == "PP-FALLBACK-001"
        assert len(primary.calls) == 1
        assert len(fallback.calls) == 1
        assert any(
            "Provider attempts: primary (timeout), fallback (success)" in a
            for a in results[0].assumptions
        )
        assert context.repository_context is not None
        assert context.repository_context["provider_attempts"] == [
            {"provider": "primary", "status": "timeout"},
            {"provider": "fallback", "status": "success"},
        ]

    def test_router_falls_back_on_rate_limit(self) -> None:
        primary = MockAdapter(name="primary", exc=AIRateLimitError("primary rate limited"))
        fallback = MockAdapter(name="fallback", result=[_candidate("fallback")])
        router = ProviderRouter(primary=primary, fallbacks=[fallback])
        context = AIContextBundle(note="test")

        results = router.generate_candidates(context)

        assert len(results) == 1
        assert results[0].proposal_id == "PP-FALLBACK-001"
        assert len(fallback.calls) == 1
        assert any(
            "Provider attempts: primary (rate_limit), fallback (success)" in a
            for a in results[0].assumptions
        )

    def test_router_falls_back_on_invalid_output(self) -> None:
        primary = MockAdapter(
            name="primary", exc=AIOutputValidationError("primary bad output")
        )
        fallback = MockAdapter(name="fallback", result=[_candidate("fallback")])
        router = ProviderRouter(primary=primary, fallbacks=[fallback])
        context = AIContextBundle(note="test")

        results = router.generate_candidates(context)

        assert len(results) == 1
        assert results[0].proposal_id == "PP-FALLBACK-001"
        assert len(fallback.calls) == 1
        assert any(
            "Provider attempts: primary (invalid_output), fallback (success)" in a
            for a in results[0].assumptions
        )

    def test_router_raises_last_error_when_all_fail(self) -> None:
        primary = MockAdapter(name="primary", exc=AITimeoutError("primary timed out"))
        fallback1 = MockAdapter(name="fallback1", exc=AIRateLimitError("fallback1 limited"))
        fallback2 = MockAdapter(
            name="fallback2", exc=AIOutputValidationError("fallback2 bad output")
        )
        router = ProviderRouter(primary=primary, fallbacks=[fallback1, fallback2])
        context = AIContextBundle(note="test")

        with pytest.raises(AIOutputValidationError, match="fallback2 bad output"):
            router.generate_candidates(context)

        assert len(primary.calls) == 1
        assert len(fallback1.calls) == 1
        assert len(fallback2.calls) == 1
        assert context.repository_context is None

    def test_router_does_not_fallback_on_unexpected_exception(self) -> None:
        primary = MockAdapter(name="primary", exc=RuntimeError("primary exploded"))
        fallback = MockAdapter(name="fallback", result=[_candidate("fallback")])
        router = ProviderRouter(primary=primary, fallbacks=[fallback])
        context = AIContextBundle(note="test")

        with pytest.raises(RuntimeError, match="primary exploded"):
            router.generate_candidates(context)

        assert len(fallback.calls) == 0
        assert context.repository_context is None


class TestGetDefaultAdapterCommaSeparated:
    def test_get_default_adapter_comma_separated(self, monkeypatch) -> None:
        monkeypatch.setenv("MARTENWEAVE_AI_PROVIDER", "openai,kimi,ollama")
        adapter = _get_default_adapter()

        assert isinstance(adapter, ProviderRouter)
        assert type(adapter.primary).__name__ == "OpenAICompatibleAdapter"
        assert len(adapter.fallbacks) == 2
        assert type(adapter.fallbacks[0]).__name__ == "KimiAdapter"
        assert type(adapter.fallbacks[1]).__name__ == "OllamaAdapter"

    def test_unknown_provider_raises_value_error(self, monkeypatch) -> None:
        monkeypatch.setenv("MARTENWEAVE_AI_PROVIDER", "unknown")
        with pytest.raises(ValueError, match="Unknown AI provider 'unknown'"):
            _get_default_adapter()
