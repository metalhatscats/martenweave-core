"""AI usage telemetry for provider calls.

Records privacy-safe metadata about AI provider invocations:
provider, model, token usage, latency, status, and linked workflow IDs.
No raw prompts, raw responses, API keys, or sensitive data are stored.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class AIUsageEvent:
    """A single AI provider usage event."""

    event_id: str
    timestamp: str
    provider: str
    model: str | None
    workflow: str | None
    command: str | None
    status: str
    latency_ms: int
    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None
    estimated_cost_usd: float | None
    error_type: str | None
    proposal_id: str | None
    change_request_id: str | None
    source_id: str | None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "provider": self.provider,
            "model": self.model,
            "workflow": self.workflow,
            "command": self.command,
            "status": self.status,
            "latency_ms": self.latency_ms,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "estimated_cost_usd": self.estimated_cost_usd,
            "error_type": self.error_type,
            "proposal_id": self.proposal_id,
            "change_request_id": self.change_request_id,
            "source_id": self.source_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AIUsageEvent:
        return cls(
            event_id=data.get("event_id", ""),
            timestamp=data.get("timestamp", ""),
            provider=data.get("provider", ""),
            model=data.get("model"),
            workflow=data.get("workflow"),
            command=data.get("command"),
            status=data.get("status", ""),
            latency_ms=int(data.get("latency_ms", 0)),
            prompt_tokens=data.get("prompt_tokens"),
            completion_tokens=data.get("completion_tokens"),
            total_tokens=data.get("total_tokens"),
            estimated_cost_usd=data.get("estimated_cost_usd"),
            error_type=data.get("error_type"),
            proposal_id=data.get("proposal_id"),
            change_request_id=data.get("change_request_id"),
            source_id=data.get("source_id"),
            metadata=dict(data.get("metadata", {})),
        )


# Approximate pricing per 1M tokens (USD) for cost estimation.
# These are placeholders; actual pricing should be updated from provider docs.
_PRICING: dict[str, dict[str, float]] = {
    "kimi-latest": {"prompt": 0.50, "completion": 1.50},
    "moonshot-v1-8k": {"prompt": 0.50, "completion": 1.50},
    "gpt-4o": {"prompt": 5.00, "completion": 15.00},
    "gpt-4o-mini": {"prompt": 0.15, "completion": 0.60},
}


def _estimate_tokens(text: str | None) -> int:
    """Rough token estimate: ~4 characters per token."""
    if not text:
        return 0
    return max(1, len(text) // 4)


def _estimate_cost(
    model: str | None,
    prompt_tokens: int | None,
    completion_tokens: int | None,
) -> float | None:
    """Estimate cost in USD from token counts and model pricing."""
    if model is None or model not in _PRICING:
        return None
    p = prompt_tokens or 0
    c = completion_tokens or 0
    rates = _PRICING[model]
    return (p * rates["prompt"] + c * rates["completion"]) / 1_000_000


def _now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _generate_event_id() -> str:
    return f"ai-usage-{uuid.uuid4().hex[:12]}"


class AIUsageTelemetryService:
    """Append-only AI usage telemetry logger.

    Writes newline-delimited JSON to ``generated/ai_usage_events.jsonl``.
    All write operations are wrapped in ``try/except`` so telemetry
    failures never propagate to callers.
    """

    def __init__(self, repo_root: Path | None = None) -> None:
        self.repo_root = repo_root
        self.log_path: Path | None = None
        if repo_root is not None:
            self.log_path = repo_root / "generated" / "ai_usage_events.jsonl"

    def emit(self, event: AIUsageEvent) -> str:
        """Append an event to the log. Returns the event ID."""
        if self.log_path is None:
            return event.event_id
        try:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with self.log_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(event.to_dict(), default=str) + "\n")
            return event.event_id
        except Exception:
            return event.event_id

    def read_events(self) -> list[AIUsageEvent]:
        """Read all AI usage events from the log."""
        events: list[AIUsageEvent] = []
        if self.log_path is None or not self.log_path.exists():
            return events
        try:
            with self.log_path.open("r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        events.append(AIUsageEvent.from_dict(json.loads(line)))
                    except Exception:
                        continue
        except Exception:
            pass
        return events


def record_ai_call(
    repo_root: Path | None,
    provider: str,
    model: str | None,
    workflow: str | None = None,
    command: str | None = None,
    latency_ms: int = 0,
    status: str = "success",
    error: BaseException | None = None,
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
    total_tokens: int | None = None,
    proposal_id: str | None = None,
    change_request_id: str | None = None,
    source_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> AIUsageEvent:
    """Record a single AI usage event.

    This is a convenience function for manual recording.  For wrapping
    adapter methods, use :func:`wrap_ai_adapter`.
    """
    error_type = type(error).__name__ if error else None

    # If total_tokens is missing but prompt/completion are available, sum them.
    if total_tokens is None and prompt_tokens is not None and completion_tokens is not None:
        total_tokens = prompt_tokens + completion_tokens

    estimated_cost = _estimate_cost(model, prompt_tokens, completion_tokens)

    event = AIUsageEvent(
        event_id=_generate_event_id(),
        timestamp=_now_iso(),
        provider=provider,
        model=model,
        workflow=workflow,
        command=command,
        status=status,
        latency_ms=latency_ms,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        estimated_cost_usd=estimated_cost,
        error_type=error_type,
        proposal_id=proposal_id,
        change_request_id=change_request_id,
        source_id=source_id,
        metadata=metadata or {},
    )
    AIUsageTelemetryService(repo_root).emit(event)
    return event


class _AIAdapterWrapper:
    """Wraps an AI provider adapter to emit telemetry on generate_candidates."""

    def __init__(
        self,
        adapter: Any,
        repo_root: Path | None = None,
        workflow: str | None = None,
        command: str | None = None,
        proposal_id: str | None = None,
    ) -> None:
        self._adapter = adapter
        self._repo_root = repo_root
        self._workflow = workflow
        self._command = command
        self._proposal_id = proposal_id
        self._provider_name = type(adapter).__name__
        self._model: str | None = getattr(adapter, "model", None)

    def generate_candidates(self, context: Any) -> list[Any]:
        start = datetime.now(UTC)
        status = "success"
        error: BaseException | None = None
        candidates: list[Any] = []
        try:
            candidates = self._adapter.generate_candidates(context)
            return candidates
        except BaseException as exc:
            status = "error"
            error = exc
            raise
        finally:
            latency_ms = int((datetime.now(UTC) - start).total_seconds() * 1000)
            # Estimate tokens from context when provider doesn't return them.
            prompt_text = getattr(context, "note", None)
            prompt_toks = _estimate_tokens(prompt_text)
            completion_text = ""
            if candidates and hasattr(candidates[0], "operations"):
                try:
                    completion_text = json.dumps(candidates[0].operations)
                except Exception:
                    pass
            completion_toks = _estimate_tokens(completion_text)
            total_toks = prompt_toks + completion_toks

            record_ai_call(
                repo_root=self._repo_root,
                provider=self._provider_name,
                model=self._model,
                workflow=self._workflow,
                command=self._command,
                latency_ms=latency_ms,
                status=status,
                error=error,
                prompt_tokens=prompt_toks,
                completion_tokens=completion_toks,
                total_tokens=total_toks,
                proposal_id=self._proposal_id,
            )


def wrap_ai_adapter(
    adapter: Any,
    repo_root: Path | None = None,
    workflow: str | None = None,
    command: str | None = None,
    proposal_id: str | None = None,
) -> Any:
    """Return a telemetry-wrapped adapter.

    Usage::

        adapter = wrap_ai_adapter(KimiAdapter(), repo_root=repo_root)
        candidates = adapter.generate_candidates(context)
    """
    wrapper = _AIAdapterWrapper(
        adapter=adapter,
        repo_root=repo_root,
        workflow=workflow,
        command=command,
        proposal_id=proposal_id,
    )
    # Expose other public attributes transparently.
    for attr in ("api_key", "base_url", "model"):
        if hasattr(adapter, attr):
            setattr(wrapper, attr, getattr(adapter, attr))
    return wrapper
