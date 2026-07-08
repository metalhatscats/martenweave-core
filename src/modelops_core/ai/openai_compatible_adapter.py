"""OpenAI-compatible AI provider adapter using JSON-mode chat completions."""

from __future__ import annotations

import json
import os
import time
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
    AIProviderRequestError,
    AIRateLimitError,
    AITimeoutError,
)

_DEFAULT_BASE_URL = "https://api.openai.com/v1"
_DEFAULT_MODEL = "gpt-4o-mini"
_DEFAULT_TIMEOUT = 30
_DEFAULT_MAX_RETRIES = 3


def _post_chat_completion(
    api_key: str,
    messages: list[dict[str, str]],
    model: str,
    base_url: str,
    timeout: int,
    max_retries: int = _DEFAULT_MAX_RETRIES,
) -> dict[str, Any]:
    """Make a chat completion request to an OpenAI-compatible API with retries."""
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

    last_error: Exception | None = None
    for attempt in range(max(1, max_retries + 1)):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code == 429:
                raise AIRateLimitError("OpenAI-compatible API rate limited") from exc
            if exc.code >= 500:
                if attempt < max_retries:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                # Retries exhausted; fall through to raise below.
                continue
            raise AIProviderRequestError(
                f"OpenAI-compatible API error: {exc.code} {exc.reason}"
            ) from exc
        except urllib.error.URLError as exc:
            last_error = exc
            if isinstance(exc.reason, TimeoutError):
                raise AITimeoutError("OpenAI-compatible API timed out") from exc
            raise AIProviderRequestError(
                f"OpenAI-compatible API request failed: {exc.reason}"
            ) from exc
        except TimeoutError as exc:
            raise AITimeoutError("OpenAI-compatible API timed out") from exc
        except json.JSONDecodeError as exc:
            raise AIOutputValidationError("Invalid JSON in OpenAI-compatible API response") from exc

    if last_error is not None:
        raise AIProviderRequestError(
            f"OpenAI-compatible API request failed after {max_retries} retries"
        ) from last_error

    raise AIProviderRequestError("OpenAI-compatible API request failed")


class OpenAICompatibleAdapter:
    """Generic OpenAI-compatible provider adapter using JSON-mode completions."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: int | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", _DEFAULT_BASE_URL)
        self.model = model or os.getenv("OPENAI_MODEL", _DEFAULT_MODEL)
        self.timeout = timeout or int(os.getenv("MARTENWEAVE_AI_TIMEOUT", str(_DEFAULT_TIMEOUT)))
        self.max_retries = int(
            os.getenv("MARTENWEAVE_AI_MAX_RETRIES", str(_DEFAULT_MAX_RETRIES))
        )

    def generate_candidates(self, context: AIContextBundle) -> list[AICandidateOutput]:
        """Generate candidate patch proposals from context."""
        if not self.api_key:
            raise AIOutputValidationError(
                "OPENAI_API_KEY is not set. Configure it in your environment or .env file."
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
            max_retries=self.max_retries,
        )

        choices = response.get("choices", [])
        if not choices:
            raise AIOutputValidationError("No choices in OpenAI-compatible API response")

        content = choices[0].get("message", {}).get("content", "")
        if not content:
            raise AIOutputValidationError("Empty content in OpenAI-compatible API response")

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise AIOutputValidationError("OpenAI-compatible response is not valid JSON") from exc

        candidate = _parse_candidate(parsed)
        return [candidate]
