"""Tests for Kimi/Moonshot provider adapter (issue #35)."""

from __future__ import annotations

import json
import urllib.error
from unittest import mock

import pytest

from modelops_core.ai.kimi_adapter import KimiAdapter, _parse_candidate
from modelops_core.ai.provider_adapter import (
    AIContextBundle,
    AIOutputValidationError,
    AIRateLimitError,
    AITimeoutError,
)


def _minimal_valid_response() -> dict:
    return {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "proposal_id": "PP-TEST-001",
                            "title": "Test Proposal",
                            "operations": [
                                {
                                    "op": "update_object",
                                    "object_id": "DOMAIN-TEST",
                                    "target_path": "name",
                                    "after": "Updated",
                                }
                            ],
                        }
                    )
                }
            }
        ]
    }


def test_kimi_adapter_missing_key_raises() -> None:
    adapter = KimiAdapter(api_key="")
    with pytest.raises(AIOutputValidationError, match="MOONSHOT_API_KEY"):
        adapter.generate_candidates(AIContextBundle(note="test"))


def test_kimi_adapter_successful_response() -> None:
    adapter = KimiAdapter(api_key="fake-key")

    mock_response = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "proposal_id": "PP-KIMI-001",
                            "title": "Test Proposal",
                            "operations": [
                                {
                                    "op": "update_object",
                                    "object_id": "DOMAIN-TEST",
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
        "modelops_core.ai.kimi_adapter._post_chat_completion",
        return_value=mock_response,
    ):
        candidates = adapter.generate_candidates(AIContextBundle(note="update name"))

    assert len(candidates) == 1
    c = candidates[0]
    assert c.proposal_id == "PP-KIMI-001"
    assert c.title == "Test Proposal"
    assert len(c.operations) == 1
    assert c.operations[0]["object_id"] == "DOMAIN-TEST"


def test_kimi_adapter_uses_registry_prompt() -> None:
    adapter = KimiAdapter(api_key="fake-key")

    mock_registry = mock.Mock()
    mock_registry.render_for_workflow.return_value = (
        "Registry system prompt",
        "Registry user prompt",
    )

    with mock.patch(
        "modelops_core.ai._candidate_common.PromptRegistry",
        return_value=mock_registry,
    ):
        with mock.patch(
            "modelops_core.ai.kimi_adapter._post_chat_completion",
            return_value=_minimal_valid_response(),
        ) as mock_post:
            adapter.generate_candidates(AIContextBundle(note="update name"))

    messages = mock_post.call_args.kwargs["messages"]
    assert messages[0]["content"] == "Registry system prompt"
    assert messages[1]["content"] == "Registry user prompt"


def test_kimi_adapter_fallback_when_registry_missing() -> None:
    adapter = KimiAdapter(api_key="fake-key")

    mock_registry = mock.Mock()
    mock_registry.render_for_workflow.side_effect = KeyError("no prompt")

    with mock.patch(
        "modelops_core.ai._candidate_common.PromptRegistry",
        return_value=mock_registry,
    ):
        with mock.patch(
            "modelops_core.ai.kimi_adapter._post_chat_completion",
            return_value=_minimal_valid_response(),
        ) as mock_post:
            adapter.generate_candidates(AIContextBundle(note="update name"))

    messages = mock_post.call_args.kwargs["messages"]
    assert "data modeling assistant" in messages[0]["content"]
    assert "Generate a patch proposal" in messages[1]["content"]


def test_kimi_adapter_empty_choices_raises() -> None:
    adapter = KimiAdapter(api_key="fake-key")

    with mock.patch(
        "modelops_core.ai.kimi_adapter._post_chat_completion",
        return_value={"choices": []},
    ):
        with pytest.raises(AIOutputValidationError, match="No choices"):
            adapter.generate_candidates(AIContextBundle(note="test"))


def test_kimi_adapter_invalid_json_in_content_raises() -> None:
    adapter = KimiAdapter(api_key="fake-key")

    with mock.patch(
        "modelops_core.ai.kimi_adapter._post_chat_completion",
        return_value={"choices": [{"message": {"content": "not valid json"}}]},
    ):
        with pytest.raises(AIOutputValidationError, match="not valid JSON"):
            adapter.generate_candidates(AIContextBundle(note="test"))


def test_kimi_adapter_rate_limit_error() -> None:

    adapter = KimiAdapter(api_key="fake-key")

    with mock.patch(
        "modelops_core.ai.kimi_adapter._post_chat_completion",
        side_effect=AIRateLimitError("rate limited"),
    ):
        with pytest.raises(AIRateLimitError):
            adapter.generate_candidates(AIContextBundle(note="test"))


def test_kimi_adapter_timeout_error() -> None:
    adapter = KimiAdapter(api_key="fake-key")

    with mock.patch(
        "modelops_core.ai.kimi_adapter._post_chat_completion",
        side_effect=AITimeoutError("timed out"),
    ):
        with pytest.raises(AITimeoutError):
            adapter.generate_candidates(AIContextBundle(note="test"))


def test_kimi_adapter_uses_env_vars(monkeypatch) -> None:
    monkeypatch.setenv("MOONSHOT_API_KEY", "env-key")
    monkeypatch.setenv("MOONSHOT_BASE_URL", "https://custom.example.com/v1")
    monkeypatch.setenv("MOONSHOT_MODEL", "custom-model")
    monkeypatch.setenv("MARTENWEAVE_AI_TIMEOUT", "60")

    adapter = KimiAdapter()
    assert adapter.api_key == "env-key"
    assert adapter.base_url == "https://custom.example.com/v1"
    assert adapter.model == "custom-model"
    assert adapter.timeout == 60


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
    from modelops_core.ai.kimi_adapter import _post_chat_completion

    http_error = urllib.error.HTTPError(
        url="https://api.moonshot.cn/v1/chat/completions",
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
                model="kimi-latest",
                base_url="https://api.moonshot.cn/v1",
                timeout=30,
            )


def test_post_chat_completion_timeout() -> None:
    from modelops_core.ai.kimi_adapter import _post_chat_completion

    url_error = urllib.error.URLError(TimeoutError("Connection timed out"))

    with mock.patch("urllib.request.urlopen", side_effect=url_error):
        with pytest.raises(AITimeoutError, match="timed out"):
            _post_chat_completion(
                api_key="fake-key",
                messages=[{"role": "user", "content": "test"}],
                model="kimi-latest",
                base_url="https://api.moonshot.cn/v1",
                timeout=30,
            )


def test_patch_proposal_service_uses_kimi_when_configured(monkeypatch) -> None:
    from modelops_core.ai.patch_proposal_service import build_patch_proposal_from_note

    monkeypatch.setenv("MARTENWEAVE_AI_PROVIDER", "kimi")
    monkeypatch.setenv("MOONSHOT_API_KEY", "fake-key")

    mock_response = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "proposal_id": "PP-ENV-001",
                            "title": "Env Test",
                            "operations": [
                                {
                                    "op": "update_object",
                                    "object_id": "DOMAIN-TEST",
                                    "target_path": "name",
                                    "after": "X",
                                }
                            ],
                        }
                    )
                }
            }
        ]
    }

    with mock.patch(
        "modelops_core.ai.kimi_adapter._post_chat_completion",
        return_value=mock_response,
    ):
        result = build_patch_proposal_from_note("update name")

    assert result["proposal"] is not None
    assert result["proposal"]["id"] == "PP-ENV-001"
