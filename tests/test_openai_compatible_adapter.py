"""Tests for OpenAI-compatible provider adapter."""

from __future__ import annotations

import json
import urllib.error
from unittest import mock

import pytest

from modelops_core.ai.openai_compatible_adapter import (
    OpenAICompatibleAdapter,
    _parse_candidate,
)
from modelops_core.ai.provider_adapter import (
    AIContextBundle,
    AIOutputValidationError,
    AIRateLimitError,
    AITimeoutError,
)


def test_openai_adapter_missing_key_raises() -> None:
    adapter = OpenAICompatibleAdapter(api_key="")
    with pytest.raises(AIOutputValidationError, match="OPENAI_API_KEY"):
        adapter.generate_candidates(AIContextBundle(note="test"))


def test_openai_adapter_successful_response() -> None:
    adapter = OpenAICompatibleAdapter(api_key="fake-key")

    mock_response = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "proposal_id": "PP-OPENAI-001",
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
        ]
    }

    with mock.patch(
        "modelops_core.ai.openai_compatible_adapter._post_chat_completion",
        return_value=mock_response,
    ):
        candidates = adapter.generate_candidates(AIContextBundle(note="update name"))

    assert len(candidates) == 1
    c = candidates[0]
    assert c.proposal_id == "PP-OPENAI-001"
    assert c.title == "Test Proposal"
    assert len(c.operations) == 1
    assert c.operations[0]["object_id"] == "DOMAIN-TEST"


def test_openai_adapter_empty_choices_raises() -> None:
    adapter = OpenAICompatibleAdapter(api_key="fake-key")

    with mock.patch(
        "modelops_core.ai.openai_compatible_adapter._post_chat_completion",
        return_value={"choices": []},
    ):
        with pytest.raises(AIOutputValidationError, match="No choices"):
            adapter.generate_candidates(AIContextBundle(note="test"))


def test_openai_adapter_invalid_json_in_content_raises() -> None:
    adapter = OpenAICompatibleAdapter(api_key="fake-key")

    with mock.patch(
        "modelops_core.ai.openai_compatible_adapter._post_chat_completion",
        return_value={"choices": [{"message": {"content": "not valid json"}}]},
    ):
        with pytest.raises(AIOutputValidationError, match="not valid JSON"):
            adapter.generate_candidates(AIContextBundle(note="test"))


def test_openai_adapter_rate_limit_error() -> None:
    adapter = OpenAICompatibleAdapter(api_key="fake-key")

    with mock.patch(
        "modelops_core.ai.openai_compatible_adapter._post_chat_completion",
        side_effect=AIRateLimitError("rate limited"),
    ):
        with pytest.raises(AIRateLimitError):
            adapter.generate_candidates(AIContextBundle(note="test"))


def test_openai_adapter_timeout_error() -> None:
    adapter = OpenAICompatibleAdapter(api_key="fake-key")

    with mock.patch(
        "modelops_core.ai.openai_compatible_adapter._post_chat_completion",
        side_effect=AITimeoutError("timed out"),
    ):
        with pytest.raises(AITimeoutError):
            adapter.generate_candidates(AIContextBundle(note="test"))


def test_openai_adapter_uses_env_vars(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "env-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://custom.openai.com/v1")
    monkeypatch.setenv("OPENAI_MODEL", "custom-model")
    monkeypatch.setenv("MARTENWEAVE_AI_TIMEOUT", "60")
    monkeypatch.setenv("MARTENWEAVE_AI_MAX_RETRIES", "5")

    adapter = OpenAICompatibleAdapter()
    assert adapter.api_key == "env-key"
    assert adapter.base_url == "https://custom.openai.com/v1"
    assert adapter.model == "custom-model"
    assert adapter.timeout == 60
    assert adapter.max_retries == 5


def test_openai_adapter_default_max_retries() -> None:
    adapter = OpenAICompatibleAdapter(api_key="fake-key")
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


def test_post_chat_completion_http_error_rate_limit() -> None:
    from modelops_core.ai.openai_compatible_adapter import _post_chat_completion

    http_error = urllib.error.HTTPError(
        url="https://api.openai.com/v1/chat/completions",
        code=429,
        msg="Too Many Requests",
        hdrs={},
        fp=None,
    )

    with mock.patch("urllib.request.urlopen", side_effect=http_error):
        with pytest.raises(AIRateLimitError, match="rate limited"):
            _post_chat_completion(
                api_key="fake-key",
                messages=[{"role": "user", "content": "test"}],
                model="gpt-4o-mini",
                base_url="https://api.openai.com/v1",
                timeout=30,
            )


def test_post_chat_completion_timeout() -> None:
    from modelops_core.ai.openai_compatible_adapter import _post_chat_completion

    url_error = urllib.error.URLError(TimeoutError("Connection timed out"))

    with mock.patch("urllib.request.urlopen", side_effect=url_error):
        with pytest.raises(AITimeoutError, match="timed out"):
            _post_chat_completion(
                api_key="fake-key",
                messages=[{"role": "user", "content": "test"}],
                model="gpt-4o-mini",
                base_url="https://api.openai.com/v1",
                timeout=30,
            )


def test_post_chat_completion_retries_on_transient_error() -> None:
    from modelops_core.ai.openai_compatible_adapter import _post_chat_completion

    http_error = urllib.error.HTTPError(
        url="https://api.openai.com/v1/chat/completions",
        code=500,
        msg="Internal Server Error",
        hdrs={},
        fp=None,
    )

    with mock.patch("urllib.request.urlopen", side_effect=http_error):
        with pytest.raises(AIOutputValidationError, match="API error"):
            _post_chat_completion(
                api_key="fake-key",
                messages=[{"role": "user", "content": "test"}],
                model="gpt-4o-mini",
                base_url="https://api.openai.com/v1",
                timeout=30,
                max_retries=2,
            )
