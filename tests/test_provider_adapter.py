"""Tests for AI provider adapter stub."""

from __future__ import annotations

import pytest

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
            proposal_id="P", title="T", operations=[{"op": "update_object"}]
        )
        result = validator.validate(candidate)
        assert result["valid"] is True


class TestAIContextBundle:
    def test_scrub_clears_raw_samples(self) -> None:
        ctx = AIContextBundle(note="n", include_raw_samples=True)
        scrubbed = ctx.scrub()
        assert scrubbed.include_raw_samples is False
        assert scrubbed.note == "n"
