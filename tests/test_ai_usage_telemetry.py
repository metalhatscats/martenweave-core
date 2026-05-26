"""Tests for AI usage telemetry (#81)."""

from __future__ import annotations

from pathlib import Path

import pytest

from modelops_core.ai.provider_adapter import AIContextBundle, NoProviderAdapter
from modelops_core.telemetry.ai_usage import (
    AIUsageEvent,
    AIUsageTelemetryService,
    _estimate_cost,
    _estimate_tokens,
    record_ai_call,
    wrap_ai_adapter,
)


class TestAIUsageEvent:
    def test_to_dict_roundtrip(self) -> None:
        event = AIUsageEvent(
            event_id="ai-001",
            timestamp="2026-01-01T00:00:00Z",
            provider="KimiAdapter",
            model="kimi-latest",
            workflow="propose-patch",
            command="propose-patch",
            status="success",
            latency_ms=1200,
            prompt_tokens=150,
            completion_tokens=80,
            total_tokens=230,
            estimated_cost_usd=0.0002,
            error_type=None,
            proposal_id="PP-001",
            change_request_id="CR-001",
            source_id="SRC-001",
            metadata={"extra": 1},
        )
        data = event.to_dict()
        restored = AIUsageEvent.from_dict(data)
        assert restored.event_id == "ai-001"
        assert restored.provider == "KimiAdapter"
        assert restored.model == "kimi-latest"
        assert restored.latency_ms == 1200
        assert restored.prompt_tokens == 150
        assert restored.completion_tokens == 80
        assert restored.total_tokens == 230
        assert restored.estimated_cost_usd == 0.0002
        assert restored.proposal_id == "PP-001"

    def test_no_raw_prompt_or_response_in_event(self) -> None:
        """Ensure sensitive content is not stored in the event."""
        event = AIUsageEvent(
            event_id="ai-002",
            timestamp="2026-01-01T00:00:00Z",
            provider="KimiAdapter",
            model="kimi-latest",
            workflow=None,
            command=None,
            status="success",
            latency_ms=100,
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
            estimated_cost_usd=None,
            error_type=None,
            proposal_id=None,
            change_request_id=None,
            source_id=None,
        )
        data = event.to_dict()
        assert "prompt" not in data
        assert "response" not in data
        assert "api_key" not in data


class TestAIUsageTelemetryService:
    def test_emit_and_read(self, tmp_path: Path) -> None:
        service = AIUsageTelemetryService(repo_root=tmp_path)
        event = AIUsageEvent(
            event_id="e1",
            timestamp="2026-01-01T00:00:00Z",
            provider="NoProviderAdapter",
            model=None,
            workflow=None,
            command=None,
            status="success",
            latency_ms=50,
            prompt_tokens=None,
            completion_tokens=None,
            total_tokens=None,
            estimated_cost_usd=None,
            error_type=None,
            proposal_id=None,
            change_request_id=None,
            source_id=None,
        )
        service.emit(event)
        events = service.read_events()
        assert len(events) == 1
        assert events[0].provider == "NoProviderAdapter"

    def test_emit_failure_is_silent(self, tmp_path: Path) -> None:
        service = AIUsageTelemetryService(repo_root=tmp_path)
        (tmp_path / "generated").write_text("not-a-dir")
        event = AIUsageEvent(
            event_id="e2",
            timestamp="2026-01-01T00:00:00Z",
            provider="X",
            model=None,
            workflow=None,
            command=None,
            status="success",
            latency_ms=1,
            prompt_tokens=None,
            completion_tokens=None,
            total_tokens=None,
            estimated_cost_usd=None,
            error_type=None,
            proposal_id=None,
            change_request_id=None,
            source_id=None,
        )
        event_id = service.emit(event)
        assert event_id == "e2"


class TestTokenAndCostEstimation:
    def test_estimate_tokens_basic(self) -> None:
        assert _estimate_tokens("abcd") == 1
        assert _estimate_tokens("a" * 40) == 10
        assert _estimate_tokens("") == 0
        assert _estimate_tokens(None) == 0

    def test_estimate_cost_known_model(self) -> None:
        cost = _estimate_cost("kimi-latest", 1000, 500)
        assert cost is not None
        expected = (1000 * 0.50 + 500 * 1.50) / 1_000_000
        assert cost == pytest.approx(expected)

    def test_estimate_cost_unknown_model(self) -> None:
        assert _estimate_cost("unknown-model", 1000, 500) is None

    def test_estimate_cost_none_model(self) -> None:
        assert _estimate_cost(None, 1000, 500) is None


class TestRecordAICall:
    def test_records_success(self, tmp_path: Path) -> None:
        event = record_ai_call(
            repo_root=tmp_path,
            provider="KimiAdapter",
            model="kimi-latest",
            workflow="propose-patch",
            command="propose-patch",
            latency_ms=500,
            status="success",
            prompt_tokens=100,
            completion_tokens=50,
            proposal_id="PP-001",
        )
        assert event.provider == "KimiAdapter"
        assert event.status == "success"
        assert event.total_tokens == 150
        assert event.estimated_cost_usd is not None

        service = AIUsageTelemetryService(repo_root=tmp_path)
        events = service.read_events()
        assert len(events) == 1
        assert events[0].proposal_id == "PP-001"

    def test_records_error(self, tmp_path: Path) -> None:
        event = record_ai_call(
            repo_root=tmp_path,
            provider="KimiAdapter",
            model="kimi-latest",
            latency_ms=200,
            status="error",
            error=ValueError("boom"),
        )
        assert event.status == "error"
        assert event.error_type == "ValueError"


class TestWrapAIAdapter:
    def test_wraps_no_provider_adapter(self, tmp_path: Path) -> None:
        adapter = wrap_ai_adapter(
            NoProviderAdapter(),
            repo_root=tmp_path,
            command="propose-patch",
        )
        context = AIContextBundle(note="Update customer group")
        candidates = adapter.generate_candidates(context)
        assert len(candidates) == 1

        service = AIUsageTelemetryService(repo_root=tmp_path)
        events = service.read_events()
        assert len(events) == 1
        assert events[0].provider == "NoProviderAdapter"
        assert events[0].command == "propose-patch"
        assert events[0].status == "success"
        assert events[0].latency_ms >= 0
        # Token estimation should have run
        assert events[0].total_tokens is not None
        assert events[0].total_tokens > 0

    def test_wraps_on_error(self, tmp_path: Path) -> None:
        class FailingAdapter:
            def generate_candidates(self, context: AIContextBundle) -> list:
                raise RuntimeError("always fails")

        adapter = wrap_ai_adapter(
            FailingAdapter(),
            repo_root=tmp_path,
            command="propose-patch",
        )
        with pytest.raises(RuntimeError, match="always fails"):
            adapter.generate_candidates(AIContextBundle(note="test"))

        service = AIUsageTelemetryService(repo_root=tmp_path)
        events = service.read_events()
        assert len(events) == 1
        assert events[0].status == "error"
        assert events[0].error_type == "RuntimeError"

    def test_no_repo_no_crash(self) -> None:
        adapter = wrap_ai_adapter(NoProviderAdapter())
        candidates = adapter.generate_candidates(AIContextBundle(note="test"))
        assert len(candidates) == 1

    def test_exposes_adapter_attributes(self) -> None:
        class DummyAdapter:
            model = "dummy-model"
            api_key = "secret"

            def generate_candidates(self, context: AIContextBundle) -> list:
                return []

        wrapped = wrap_ai_adapter(DummyAdapter())
        assert wrapped.model == "dummy-model"
        assert wrapped.api_key == "secret"
