"""Tests for AI provider adapter stub."""

from __future__ import annotations

import pytest

from modelops_core.ai.patch_proposal_service import _get_default_adapter
from modelops_core.ai.provider_adapter import (
    AICandidateOutput,
    AIContextBundle,
    AIOutputValidationError,
    NoProviderAdapter,
    ProviderOutputValidator,
)


class TestNoProviderAdapter:
    def test_customer_group_note_returns_operations(self) -> None:
        adapter = NoProviderAdapter()
        ctx = AIContextBundle(note="Update the customer group description")
        results = adapter.generate_candidates(ctx)
        assert len(results) == 1
        assert results[0].proposal_id == "PP-SCAFFOLD-001"
        assert len(results[0].operations) == 1
        assert results[0].affected_objects == [
            "ATTR-CUST-SALES-CUSTOMER-GROUP",
            "FEP-S4-KNVV-KDGRP",
        ]

    def test_knvv_kdgrp_note_returns_operations(self) -> None:
        adapter = NoProviderAdapter()
        ctx = AIContextBundle(note="Something about KNVV-KDGRP")
        results = adapter.generate_candidates(ctx)
        assert len(results) == 1
        assert len(results[0].operations) == 1

    def test_unrelated_note_returns_empty_operations(self) -> None:
        adapter = NoProviderAdapter()
        ctx = AIContextBundle(note="Just a random note about products")
        results = adapter.generate_candidates(ctx)
        assert len(results) == 1
        assert results[0].proposal_id == "PP-SCAFFOLD-001"
        assert results[0].operations == []
        assert results[0].affected_objects == []

    def test_source_evidence_truncated_to_500_chars(self) -> None:
        adapter = NoProviderAdapter()
        long_note = "x" * 1000
        ctx = AIContextBundle(note=long_note)
        results = adapter.generate_candidates(ctx)
        assert len(results[0].source_evidence) == 500

    def test_empty_note_returns_scaffold(self) -> None:
        adapter = NoProviderAdapter()
        ctx = AIContextBundle(note="")
        results = adapter.generate_candidates(ctx)
        assert len(results) == 1
        assert results[0].proposal_id == "PP-SCAFFOLD-001"


class TestProviderOutputValidator:
    def test_validate_raises_on_missing_proposal_id(self) -> None:
        validator = ProviderOutputValidator()
        candidate = AICandidateOutput(
            proposal_id="", title="T", operations=[{"op": "update_object"}]
        )
        with pytest.raises(AIOutputValidationError):
            validator.validate(candidate)

    def test_validate_raises_on_missing_title(self) -> None:
        validator = ProviderOutputValidator()
        candidate = AICandidateOutput(
            proposal_id="P", title="", operations=[{"op": "update_object"}]
        )
        with pytest.raises(AIOutputValidationError):
            validator.validate(candidate)

    def test_validate_raises_on_empty_operations(self) -> None:
        validator = ProviderOutputValidator()
        candidate = AICandidateOutput(proposal_id="P", title="T", operations=[])
        with pytest.raises(AIOutputValidationError):
            validator.validate(candidate)

    def test_validate_raises_on_disallowed_operation(self) -> None:
        validator = ProviderOutputValidator()
        candidate = AICandidateOutput(
            proposal_id="P", title="T", operations=[{"op": "delete_object"}]
        )
        with pytest.raises(AIOutputValidationError):
            validator.validate(candidate)

    def test_validate_passes_with_allowed_operation(self) -> None:
        validator = ProviderOutputValidator()
        candidate = AICandidateOutput(
            proposal_id="P",
            title="T",
            operations=[{"op": "update_object", "object_id": "DOMAIN-TEST"}],
        )
        result = validator.validate(candidate)
        assert result["valid"] is True


class TestAIContextBundle:
    def test_scrub_clears_raw_samples(self) -> None:
        ctx = AIContextBundle(note="n", include_raw_samples=True)
        scrubbed = ctx.scrub()
        assert scrubbed.include_raw_samples is False
        assert scrubbed.note == "n"


class TestProviderOutputValidatorHardened:
    def test_validates_object_id_format(self) -> None:
        validator = ProviderOutputValidator()
        candidate = AICandidateOutput(
            proposal_id="P",
            title="T",
            operations=[
                {
                    "op": "update_object",
                    "object_id": "ATTR-TEST-001",
                    "object_type": "Attribute",
                }
            ],
        )
        result = validator.validate(candidate)
        assert result["valid"] is True

    def test_rejects_invalid_object_id_format(self) -> None:
        validator = ProviderOutputValidator()
        candidate = AICandidateOutput(
            proposal_id="P",
            title="T",
            operations=[
                {"op": "update_object", "object_id": "attr-test-001", "object_type": "Attribute"}
            ],
        )
        with pytest.raises(AIOutputValidationError, match="object_id"):
            validator.validate(candidate)

    def test_rejects_missing_object_id(self) -> None:
        validator = ProviderOutputValidator()
        candidate = AICandidateOutput(
            proposal_id="P", title="T", operations=[{"op": "update_object"}]
        )
        with pytest.raises(AIOutputValidationError, match="object_id"):
            validator.validate(candidate)

    def test_validates_object_type_registered(self) -> None:
        validator = ProviderOutputValidator()
        candidate = AICandidateOutput(
            proposal_id="P",
            title="T",
            operations=[
                {"op": "update_object", "object_id": "DOMAIN-TEST", "object_type": "Attribute"}
            ],
        )
        result = validator.validate(candidate)
        assert result["valid"] is True

    def test_rejects_unregistered_object_type(self) -> None:
        validator = ProviderOutputValidator()
        candidate = AICandidateOutput(
            proposal_id="P",
            title="T",
            operations=[
                {
                    "op": "update_object",
                    "object_id": "DOMAIN-TEST",
                    "object_type": "UnknownType",
                }
            ],
        )
        with pytest.raises(AIOutputValidationError, match="object_type"):
            validator.validate(candidate)

    def test_rejects_invalid_object_id_in_affected_objects(self) -> None:
        validator = ProviderOutputValidator()
        candidate = AICandidateOutput(
            proposal_id="P",
            title="T",
            operations=[{"op": "update_object", "object_id": "DOMAIN-TEST"}],
            affected_objects=["invalid-id"],
        )
        with pytest.raises(AIOutputValidationError, match="affected_objects"):
            validator.validate(candidate)


class TestGetDefaultAdapter:
    def test_no_provider_returns_no_provider_adapter(self, monkeypatch) -> None:
        monkeypatch.delenv("MARTENWEAVE_AI_PROVIDER", raising=False)
        adapter = _get_default_adapter()
        assert type(adapter).__name__ == "NoProviderAdapter"

    def test_kimi_returns_kimi_adapter(self, monkeypatch) -> None:
        monkeypatch.setenv("MARTENWEAVE_AI_PROVIDER", "kimi")
        monkeypatch.setenv("MOONSHOT_API_KEY", "fake-key")
        adapter = _get_default_adapter()
        assert type(adapter).__name__ == "KimiAdapter"

    def test_openai_returns_openai_compatible_adapter(self, monkeypatch) -> None:
        monkeypatch.setenv("MARTENWEAVE_AI_PROVIDER", "openai")
        monkeypatch.setenv("OPENAI_API_KEY", "fake-key")
        adapter = _get_default_adapter()
        assert type(adapter).__name__ == "OpenAICompatibleAdapter"

    def test_ollama_returns_ollama_adapter(self, monkeypatch) -> None:
        monkeypatch.setenv("MARTENWEAVE_AI_PROVIDER", "ollama")
        adapter = _get_default_adapter()
        assert type(adapter).__name__ == "OllamaAdapter"
