"""Multi-provider AI adapter with fallback routing."""

from __future__ import annotations

from dataclasses import dataclass, field

from modelops_core.ai.provider_adapter import (
    AICandidateOutput,
    AIContextBundle,
    AIOutputValidationError,
    AIProviderAdapter,
    AIRateLimitError,
    AITimeoutError,
)


def _default_adapter_name(adapter: AIProviderAdapter) -> str:
    """Return a human-readable name for an adapter."""
    return getattr(adapter, "name", type(adapter).__name__)


def _error_kind(error: Exception) -> str:
    """Map an eligible fallback error to a short status label."""
    if isinstance(error, AITimeoutError):
        return "timeout"
    if isinstance(error, AIRateLimitError):
        return "rate_limit"
    if isinstance(error, AIOutputValidationError):
        return "invalid_output"
    return type(error).__name__


@dataclass
class ProviderRouter:
    """Routes ``generate_candidates`` through a primary adapter and fallbacks.

    On ``AITimeoutError``, ``AIRateLimitError``, or ``AIOutputValidationError``
    from the primary adapter, each fallback is tried in order. If all adapters
    fail, the last error encountered is re-raised.

    Successful candidates are annotated with an assumption describing the
    provider attempts, and the attempt history is recorded in
    ``context.repository_context`` when present.
    """

    primary: AIProviderAdapter
    fallbacks: list[AIProviderAdapter] = field(default_factory=list)
    primary_name: str | None = None
    fallback_names: list[str] | None = None

    def __post_init__(self) -> None:
        self._primary_name = self.primary_name or _default_adapter_name(self.primary)
        self._fallback_names = self.fallback_names or [
            _default_adapter_name(adapter) for adapter in self.fallbacks
        ]
        if len(self._fallback_names) != len(self.fallbacks):
            raise ValueError("fallback_names must have the same length as fallbacks when provided.")

    def generate_candidates(self, context: AIContextBundle) -> list[AICandidateOutput]:
        """Generate candidates from the primary, falling back on eligible errors."""
        allowed_errors: tuple[type[Exception], ...] = (
            AITimeoutError,
            AIRateLimitError,
            AIOutputValidationError,
        )
        attempts: list[tuple[str, str]] = []
        last_error: Exception | None = None

        adapters = [(self._primary_name, self.primary)] + list(
            zip(self._fallback_names, self.fallbacks, strict=True)
        )

        for name, adapter in adapters:
            try:
                candidates = adapter.generate_candidates(context)
            except allowed_errors as exc:
                last_error = exc
                attempts.append((name, _error_kind(exc)))
                continue

            self._record_attempts(context, attempts, name, "success")
            return self._annotate_candidates(candidates, attempts, name)

        if last_error is not None:
            raise last_error
        return []

    def _record_attempts(
        self,
        context: AIContextBundle,
        attempts: list[tuple[str, str]],
        final_name: str,
        final_status: str,
    ) -> None:
        """Store the provider attempt history in the context."""
        if context.repository_context is None:
            context.repository_context = {}
        context.repository_context["provider_attempts"] = [
            {"provider": name, "status": status}
            for name, status in attempts + [(final_name, final_status)]
        ]

    def _annotate_candidates(
        self,
        candidates: list[AICandidateOutput],
        attempts: list[tuple[str, str]],
        success_name: str,
    ) -> list[AICandidateOutput]:
        """Add an assumption summarising provider attempts to each candidate."""
        if not candidates:
            return candidates

        attempt_summary = ", ".join(
            f"{name} ({status})" for name, status in attempts + [(success_name, "success")]
        )
        assumption = f"Provider attempts: {attempt_summary}"

        annotated: list[AICandidateOutput] = []
        for candidate in candidates:
            annotated.append(
                AICandidateOutput(
                    proposal_id=candidate.proposal_id,
                    title=candidate.title,
                    operations=list(candidate.operations),
                    affected_objects=list(candidate.affected_objects),
                    assumptions=list(candidate.assumptions) + [assumption],
                    human_checks=list(candidate.human_checks),
                    source_evidence=candidate.source_evidence,
                )
            )
        return annotated
