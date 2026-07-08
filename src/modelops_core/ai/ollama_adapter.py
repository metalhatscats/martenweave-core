"""Ollama AI provider adapter using /api/chat with structured JSON output."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any

from modelops_core.ai.provider_adapter import (
    AICandidateOutput,
    AIContextBundle,
    AIOutputValidationError,
    AITimeoutError,
)

_DEFAULT_BASE_URL = "http://localhost:11434"
_DEFAULT_MODEL = "llama3.1"
_DEFAULT_TIMEOUT = 30
_DEFAULT_MAX_RETRIES = 3

_SYSTEM_PROMPT = (
    "You are a data modeling assistant. "
    "Generate structured patch proposals for master data model changes. "
    "Respond with valid JSON only."
)

_CANDIDATE_SCHEMA = {
    "type": "object",
    "properties": {
        "proposal_id": {"type": "string"},
        "title": {"type": "string"},
        "operations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "op": {"type": "string"},
                    "object_id": {"type": "string"},
                    "object_type": {"type": "string"},
                    "target_path": {"type": "string"},
                    "after": {},
                },
                "required": ["op", "object_id"],
            },
        },
        "affected_objects": {
            "type": "array",
            "items": {"type": "string"},
        },
        "assumptions": {
            "type": "array",
            "items": {"type": "string"},
        },
        "human_checks": {
            "type": "array",
            "items": {"type": "string"},
        },
        "source_evidence": {"type": "string"},
    },
    "required": ["proposal_id", "title", "operations"],
}


def _build_prompt(context: AIContextBundle) -> str:
    lines = [
        "Generate a patch proposal based on the following note.",
        "",
        f"Note: {context.note}",
    ]
    if context.domain:
        lines.append(f"Domain: {context.domain}")
    if context.affected_object_ids:
        lines.append(f"Known affected objects: {', '.join(context.affected_object_ids)}")
    if context.dataset_columns:
        lines.append(f"Dataset columns: {', '.join(context.dataset_columns)}")
    if context.dataset_row_count is not None:
        lines.append(f"Dataset rows: {context.dataset_row_count}")
    if context.repository_context:
        lines.append("")
        lines.append("Repository context (canonical objects, relationships, validation summary):")
        lines.append(json.dumps(context.repository_context, indent=2, default=str))
    lines.append("")
    lines.append("Respond with JSON matching this schema:")
    lines.append(json.dumps(_CANDIDATE_SCHEMA, indent=2))
    return "\n".join(lines)


def _parse_candidate(raw: dict[str, Any]) -> AICandidateOutput:
    """Parse a raw dict into AICandidateOutput, raising on schema violations."""
    proposal_id = raw.get("proposal_id")
    title = raw.get("title")
    operations = raw.get("operations")

    if not proposal_id or not isinstance(proposal_id, str):
        raise AIOutputValidationError("Missing or invalid proposal_id")
    if not title or not isinstance(title, str):
        raise AIOutputValidationError("Missing or invalid title")
    if not operations or not isinstance(operations, list):
        raise AIOutputValidationError("Missing or invalid operations")

    return AICandidateOutput(
        proposal_id=proposal_id,
        title=title,
        operations=[dict(op) for op in operations],
        affected_objects=list(raw.get("affected_objects", [])),
        assumptions=list(raw.get("assumptions", [])),
        human_checks=list(raw.get("human_checks", [])),
        source_evidence=raw.get("source_evidence"),
    )


def _post_chat(
    messages: list[dict[str, str]],
    model: str,
    base_url: str,
    timeout: int,
    max_retries: int = _DEFAULT_MAX_RETRIES,
) -> dict[str, Any]:
    """Make a non-streaming chat request to the Ollama API with retries."""
    url = f"{base_url}/api/chat"
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.2},
    }
    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    last_error: Exception | None = None
    for attempt in range(max(1, max_retries + 1)):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code >= 500:
                if attempt < max_retries:
                    time.sleep(0.5 * (attempt + 1))
                    continue
            raise AIOutputValidationError(
                f"Ollama API error: {exc.code} {exc.reason}"
            ) from exc
        except urllib.error.URLError as exc:
            last_error = exc
            if isinstance(exc.reason, TimeoutError):
                raise AITimeoutError("Ollama API timed out") from exc
            raise AIOutputValidationError(
                f"Ollama API request failed: {exc.reason}"
            ) from exc
        except TimeoutError as exc:
            raise AITimeoutError("Ollama API timed out") from exc
        except json.JSONDecodeError as exc:
            raise AIOutputValidationError("Invalid JSON in Ollama API response") from exc

    if last_error is not None:
        raise AIOutputValidationError(
            f"Ollama API request failed after {max_retries} retries"
        ) from last_error

    raise AIOutputValidationError("Ollama API request failed")


class OllamaAdapter:
    """Ollama provider adapter using /api/chat non-streaming completions."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: int | None = None,
    ) -> None:
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", _DEFAULT_BASE_URL)
        self.model = model or os.getenv("OLLAMA_MODEL", _DEFAULT_MODEL)
        self.timeout = timeout or int(os.getenv("MARTENWEAVE_AI_TIMEOUT", str(_DEFAULT_TIMEOUT)))
        self.max_retries = int(
            os.getenv("MARTENWEAVE_AI_MAX_RETRIES", str(_DEFAULT_MAX_RETRIES))
        )

    def generate_candidates(self, context: AIContextBundle) -> list[AICandidateOutput]:
        """Generate candidate patch proposals from context."""
        prompt = _build_prompt(context)
        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        response = _post_chat(
            messages=messages,
            model=self.model,
            base_url=self.base_url,
            timeout=self.timeout,
            max_retries=self.max_retries,
        )

        message = response.get("message")
        if not message:
            raise AIOutputValidationError("No message in Ollama API response")

        content = message.get("content", "")
        if not content:
            raise AIOutputValidationError("Empty content in Ollama API response")

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise AIOutputValidationError("Ollama response is not valid JSON") from exc

        candidate = _parse_candidate(parsed)
        return [candidate]
