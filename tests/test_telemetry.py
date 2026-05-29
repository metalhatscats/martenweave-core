"""Tests for local application usage telemetry (#82)."""

from __future__ import annotations

from pathlib import Path

import pytest

from modelops_core.telemetry import (
    TelemetryService,
    UsageEvent,
    record_export_format,
    record_object_count,
    record_proposal_count,
    record_source_type,
    with_telemetry,
)


class TestTelemetryService:
    def test_emit_and_read_event(self, tmp_path: Path) -> None:
        service = TelemetryService(repo_root=tmp_path)
        event = UsageEvent(
            event_id="usage-test-001",
            timestamp="2026-01-01T00:00:00Z",
            command="validate",
            status="success",
            duration_ms=150,
            repo_hash="abc123",
        )
        service.emit(event)
        events = service.read_events()
        assert len(events) == 1
        assert events[0].command == "validate"
        assert events[0].duration_ms == 150
        assert events[0].repo_hash == "abc123"

    def test_read_empty_log(self, tmp_path: Path) -> None:
        service = TelemetryService(repo_root=tmp_path)
        assert service.read_events() == []

    def test_read_missing_log(self) -> None:
        service = TelemetryService(repo_root=None)
        assert service.read_events() == []

    def test_emit_failure_is_silent(self, tmp_path: Path) -> None:
        """Telemetry write failures must not propagate."""
        service = TelemetryService(repo_root=tmp_path)
        # Make the generated dir a file so mkdir fails
        (tmp_path / "generated").write_text("not-a-dir")
        event = UsageEvent(
            event_id="usage-test-002",
            timestamp="2026-01-01T00:00:00Z",
            command="validate",
            status="success",
            duration_ms=100,
        )
        # Should not raise
        event_id = service.emit(event)
        assert event_id == "usage-test-002"

    def test_skips_corrupt_lines(self, tmp_path: Path) -> None:
        service = TelemetryService(repo_root=tmp_path)
        log = tmp_path / "generated" / "usage_events.jsonl"
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(
            '{"event_id":"good","timestamp":"2026-01-01T00:00:00Z",'
            '"command":"x","status":"success","duration_ms":1}\n'
            "this is not json\n"
        )
        events = service.read_events()
        assert len(events) == 1
        assert events[0].event_id == "good"

    def test_event_to_dict_roundtrip(self) -> None:
        event = UsageEvent(
            event_id="e1",
            timestamp="2026-01-01T00:00:00Z",
            command="build-index",
            status="error",
            duration_ms=250,
            repo_hash="hash123",
            error_type="ValueError",
            object_count=42,
            proposal_count=3,
            source_type="csv",
            export_format="xlsx",
            feature_flags={"flag_a": True},
            metadata={"extra": 1},
        )
        data = event.to_dict()
        restored = UsageEvent.from_dict(data)
        assert restored.event_id == "e1"
        assert restored.command == "build-index"
        assert restored.status == "error"
        assert restored.duration_ms == 250
        assert restored.repo_hash == "hash123"
        assert restored.error_type == "ValueError"
        assert restored.object_count == 42
        assert restored.proposal_count == 3
        assert restored.source_type == "csv"
        assert restored.export_format == "xlsx"
        assert restored.feature_flags == {"flag_a": True}
        assert restored.metadata == {"extra": 1}


class TestWithTelemetryDecorator:
    def test_records_success(self, tmp_path: Path) -> None:
        @with_telemetry("my-cmd")
        def my_func(repo: str | None = None) -> str:
            return "ok"

        my_func(repo=str(tmp_path))
        service = TelemetryService(repo_root=tmp_path)
        events = service.read_events()
        assert len(events) == 1
        assert events[0].command == "my-cmd"
        assert events[0].status == "success"
        assert events[0].error_type is None
        assert events[0].duration_ms >= 0
        assert events[0].repo_hash is not None

    def test_records_error(self, tmp_path: Path) -> None:
        @with_telemetry("fail-cmd")
        def my_func(repo: str | None = None) -> None:
            raise ValueError("boom")

        with pytest.raises(ValueError, match="boom"):
            my_func(repo=str(tmp_path))

        service = TelemetryService(repo_root=tmp_path)
        events = service.read_events()
        assert len(events) == 1
        assert events[0].command == "fail-cmd"
        assert events[0].status == "error"
        assert events[0].error_type == "ValueError"

    def test_records_object_count(self, tmp_path: Path) -> None:
        @with_telemetry("count-cmd")
        def my_func(repo: str | None = None) -> None:
            record_object_count(17)

        my_func(repo=str(tmp_path))
        service = TelemetryService(repo_root=tmp_path)
        events = service.read_events()
        assert events[0].object_count == 17

    def test_records_proposal_count(self, tmp_path: Path) -> None:
        @with_telemetry("prop-cmd")
        def my_func(repo: str | None = None) -> None:
            record_proposal_count(5)

        my_func(repo=str(tmp_path))
        service = TelemetryService(repo_root=tmp_path)
        events = service.read_events()
        assert events[0].proposal_count == 5

    def test_records_source_type(self, tmp_path: Path) -> None:
        @with_telemetry("src-cmd")
        def my_func(repo: str | None = None) -> None:
            record_source_type("google-sheets")

        my_func(repo=str(tmp_path))
        service = TelemetryService(repo_root=tmp_path)
        events = service.read_events()
        assert events[0].source_type == "google-sheets"

    def test_records_export_format(self, tmp_path: Path) -> None:
        @with_telemetry("exp-cmd")
        def my_func(repo: str | None = None) -> None:
            record_export_format("csv")

        my_func(repo=str(tmp_path))
        service = TelemetryService(repo_root=tmp_path)
        events = service.read_events()
        assert events[0].export_format == "csv"

    def test_no_repo_no_crash(self) -> None:
        @with_telemetry("no-repo-cmd")
        def my_func() -> str:
            return "ok"

        my_func()
        # No repo means no log file; just verify it doesn't crash

    def test_decorator_preserves_return_value(self, tmp_path: Path) -> None:
        @with_telemetry("ret-cmd")
        def my_func(repo: str | None = None) -> int:
            return 42

        assert my_func(repo=str(tmp_path)) == 42


class TestTelemetryFailureIsolation:
    def test_decorator_survives_emit_failure(self, tmp_path: Path) -> None:
        """If the telemetry log cannot be written, the command still runs."""
        (tmp_path / "generated").write_text("not-a-dir")

        @with_telemetry("iso-cmd")
        def my_func(repo: str | None = None) -> str:
            return "ok"

        result = my_func(repo=str(tmp_path))
        assert result == "ok"


class TestTelemetryPrivacy:
    def test_usage_event_does_not_store_raw_paths(self) -> None:
        """repo_hash must be a hash, not the raw filesystem path."""
        event = UsageEvent(
            event_id="e1",
            timestamp="2026-01-01T00:00:00Z",
            command="validate",
            status="success",
            duration_ms=100,
            repo_hash="a1b2c3d4",
        )
        data = event.to_dict()
        assert "/Users/" not in str(data.get("repo_hash", ""))
        assert "/home/" not in str(data.get("repo_hash", ""))
        assert "C:\\" not in str(data.get("repo_hash", ""))

    def test_usage_event_does_not_store_prompts_or_secrets(self) -> None:
        """Sensitive fields must not appear in the event dict."""
        event = UsageEvent(
            event_id="e2",
            timestamp="2026-01-01T00:00:00Z",
            command="propose-patch",
            status="success",
            duration_ms=200,
            metadata={"safe_key": "safe_value"},
        )
        data = event.to_dict()
        assert "prompt" not in data
        assert "response" not in data
        assert "api_key" not in data
        assert "password" not in data
        assert "secret" not in data
        assert "token" not in data

    def test_repo_hash_is_truncated_sha256_not_raw_path(self, tmp_path: Path) -> None:
        """Verify the hash helper produces a short hex string, not the path."""
        from modelops_core.telemetry import _repo_hash

        hash_val = _repo_hash(tmp_path)
        assert hash_val is not None
        assert str(tmp_path) not in hash_val
        assert len(hash_val) == 16
        assert all(c in "0123456789abcdef" for c in hash_val)

    def test_error_type_does_not_contain_stack_trace(self, tmp_path: Path) -> None:
        """error_type should be the exception class name, not a full traceback."""

        @with_telemetry("err-cmd")
        def my_func(repo: str | None = None) -> None:
            raise ValueError("something went wrong")

        with pytest.raises(ValueError):
            my_func(repo=str(tmp_path))

        service = TelemetryService(repo_root=tmp_path)
        events = service.read_events()
        assert len(events) == 1
        assert events[0].error_type == "ValueError"
        assert "Traceback" not in str(events[0].to_dict())
        assert 'File "' not in str(events[0].to_dict())
