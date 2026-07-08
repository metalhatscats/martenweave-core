"""Kimi/Moonshot AI provider adapter using OpenAI-compatible chat completions."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from modelops_core.ai._candidate_common import (
    _parse_candidate,
    build_prompt_messages,
)
from modelops_core.ai.provider_adapter import (
    AICandidateOutput,
    AIContextBundle,
    AIOutputValidationError,
    AIRateLimitError,
    AITimeoutError,
)

_DEFAULT_BASE_URL = "https://api.moonshot.cn/v1"
_DEFAULT_MODEL = "kimi-latest"
_DEFAULT_TIMEOUT = 30


def _post_chat_completion(
    api_key: str,
    messages: list[dict[str, str]],
    model: str,
    base_url: str,
    timeout: int,
) -> dict[str, Any]:
    """Make a chat completion request to the Moonshot API."""
    url = f"{base_url}/chat/completions"
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }
    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            raise AIRateLimitError("Moonshot API rate limited") from exc
        raise AIOutputValidationError(f"Moonshot API error: {exc.code} {exc.reason}") from exc
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, TimeoutError):
            raise AITimeoutError("Moonshot API timed out") from exc
        raise AIOutputValidationError(f"Moonshot API request failed: {exc.reason}") from exc
    except TimeoutError as exc:
        raise AITimeoutError("Moonshot API timed out") from exc
    except json.JSONDecodeError as exc:
        raise AIOutputValidationError("Invalid JSON in Moonshot API response") from exc


class KimiAdapter:
    """Kimi/Moonshot provider adapter using OpenAI-compatible completions."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: int | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("MOONSHOT_API_KEY", "")
        self.base_url = base_url or os.getenv("MOONSHOT_BASE_URL", _DEFAULT_BASE_URL)
        self.model = model or os.getenv("MOONSHOT_MODEL", _DEFAULT_MODEL)
        self.timeout = timeout or int(os.getenv("MARTENWEAVE_AI_TIMEOUT", str(_DEFAULT_TIMEOUT)))

    def generate_candidates(self, context: AIContextBundle) -> list[AICandidateOutput]:
        """Generate candidate patch proposals from context."""
        if not self.api_key:
            raise AIOutputValidationError(
                "MOONSHOT_API_KEY is not set. Configure it in your environment or .env file."
            )

        system_prompt, user_prompt = build_prompt_messages(context)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        response = _post_chat_completion(
            api_key=self.api_key,
            messages=messages,
            model=self.model,
            base_url=self.base_url,
            timeout=self.timeout,
        )

        choices = response.get("choices", [])
        if not choices:
            raise AIOutputValidationError("No choices in Moonshot API response")

        content = choices[0].get("message", {}).get("content", "")
        if not content:
            raise AIOutputValidationError("Empty content in Moonshot API response")

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise AIOutputValidationError("Moonshot response is not valid JSON") from exc

        candidate = _parse_candidate(parsed)
        return [candidate]
