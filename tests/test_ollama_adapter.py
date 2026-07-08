"""Tests for Ollama provider adapter."""

from __future__ import annotations

import json
import urllib.error
from unittest import mock

import pytest

from modelops_core.ai.ollama_adapter import OllamaAdapter, _parse_candidate
from modelops_core.ai.provider_adapter import (
    AIContextBundle,
    AIOutputValidationError,
    AITimeoutError,
)


def test_ollama_adapter_successful_response() -> None:
    adapter = OllamaAdapter()

    mock_response = {
        "message": {
            "content": json.dumps(
                {
                    "proposal_id": "PP-OLLAMA-001",
                    "title": "Test Proposal",
                    "operations": [
                        {
                            "op": "update_object",
                            "object_id": "DOMAIN-TEST",
                            "object_type": "MasterDataDomain",
                            "target_path": "name",
                            "after": "Updated",
                        }
                    ],
                    "affected_objects": ["DOMAIN-TEST"],
                    "assumptions": ["Assume test"],
                    "human_checks": ["Check test"],
                }
            )
        }
    }

    with mock.patch(
        "modelops_core.ai.ollama_adapter._post_chat",
        return_value=mock_response,
    ):
        candidates = adapter.generate_candidates(AIContextBundle(note="update name"))

    assert len(candidates) == 1
    c = candidates[0]
    assert c.proposal_id == "PP-OLLAMA-001"
    assert c.title == "Test Proposal"
    assert len(c.operations) == 1
    assert c.operations[0]["object_id"] == "DOMAIN-TEST"


def test_ollama_adapter_missing_message_raises() -> None:
    adapter = OllamaAdapter()

    with mock.patch(
        "modelops_core.ai.ollama_adapter._post_chat",
        return_value={},
    ):
        with pytest.raises(AIOutputValidationError, match="message"):
            adapter.generate_candidates(AIContextBundle(note="test"))


def test_ollama_adapter_invalid_json_in_content_raises() -> None:
    adapter = OllamaAdapter()

    with mock.patch(
        "modelops_core.ai.ollama_adapter._post_chat",
        return_value={"message": {"content": "not valid json"}},
    ):
        with pytest.raises(AIOutputValidationError, match="not valid JSON"):
            adapter.generate_candidates(AIContextBundle(note="test"))


def test_ollama_adapter_timeout_error() -> None:
    adapter = OllamaAdapter()

    with mock.patch(
        "modelops_core.ai.ollama_adapter._post_chat",
        side_effect=AITimeoutError("timed out"),
    ):
        with pytest.raises(AITimeoutError):
            adapter.generate_candidates(AIContextBundle(note="test"))


def test_ollama_adapter_uses_env_vars(monkeypatch) -> None:
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://custom.ollama:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "custom-model")
    monkeypatch.setenv("MARTENWEAVE_AI_TIMEOUT", "120")
    monkeypatch.setenv("MARTENWEAVE_AI_MAX_RETRIES", "5")

    adapter = OllamaAdapter()
    assert adapter.base_url == "http://custom.ollama:11434"
    assert adapter.model == "custom-model"
    assert adapter.timeout == 120
    assert adapter.max_retries == 5


def test_ollama_adapter_default_max_retries() -> None:
    adapter = OllamaAdapter()
    assert adapter.max_retries == 3


def test_parse_candidate_missing_proposal_id() -> None:
    with pytest.raises(AIOutputValidationError, match="proposal_id"):
        _parse_candidate({"title": "Test", "operations": []})


def test_parse_candidate_missing_title() -> None:
    with pytest.raises(AIOutputValidationError, match="title"):
        _parse_candidate({"proposal_id": "PP-001", "operations": []})


def test_parse_candidate_missing_operations() -> None:
    with pytest.raises(AIOutputValidationError, match="operations"):
        _parse_candidate({"proposal_id": "PP-001", "title": "Test"})


def test_post_chat_timeout() -> None:
    from modelops_core.ai.ollama_adapter import _post_chat

    url_error = urllib.error.URLError(TimeoutError("Connection timed out"))

    with mock.patch("urllib.request.urlopen", side_effect=url_error):
        with pytest.raises(AITimeoutError, match="timed out"):
            _post_chat(
                messages=[{"role": "user", "content": "test"}],
                model="llama3.1",
                base_url="http://localhost:11434",
                timeout=30,
            )


def test_post_chat_parses_json_response() -> None:
    from modelops_core.ai.ollama_adapter import _post_chat

    mock_response_bytes = json.dumps({"message": {"content": "hello"}}).encode("utf-8")

    class MockResponse:
        def read(self) -> bytes:
            return mock_response_bytes

        def __enter__(self) -> MockResponse:
            return self

        def __exit__(self, *args: object) -> None:
            return None

    with mock.patch("urllib.request.urlopen", return_value=MockResponse()):
        response = _post_chat(
            messages=[{"role": "user", "content": "test"}],
            model="llama3.1",
            base_url="http://localhost:11434",
            timeout=30,
        )

    assert response == {"message": {"content": "hello"}}
