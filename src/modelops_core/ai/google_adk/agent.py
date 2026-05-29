"""ADK agent construction — only importable when google-adk is installed."""

from __future__ import annotations

from typing import Any

from modelops_core.ai.google_adk.tools import TOOL_REGISTRY


def _build_agent(repo_root: str | None = None) -> Any:
    """Build an ADK agent with Martenweave tools.

    Requires google-adk to be installed. Raises ImportError otherwise.
    """
    try:
        from google.adk.agents import Agent  # type: ignore[import-untyped,import-not-found]
    except ImportError as exc:
        raise ImportError(
            "google-adk is not installed. Install with: pip install martenweave-core[google_adk]"
        ) from exc

    # Wrap each tool in a callable that ADK can use
    tools: list[Any] = []
    for name, func in TOOL_REGISTRY.items():
        tools.append(_wrap_tool(name, func))

    return Agent(
        model="gemini-2.5-flash",
        name="martenweave-agent",
        description=(
            "An agent that helps manage master data models using Martenweave. "
            "It can validate models, trace impacts, create proposals, "
            "and preview notifications. It never bypasses validators or approval gates."
        ),
        instruction=(
            "You are a Martenweave modeling assistant. "
            "Use the available tools to help users understand and evolve their data models. "
            "Always validate before proposing changes. "
            "High-risk proposals require approval via ChangeRequest. "
            "Never mutate canonical files directly without a validated PatchProposal."
        ),
        tools=tools,
    )


def _wrap_tool(name: str, func: Any) -> Any:
    """Wrap a plain Python function for ADK tool registration."""
    try:
        from google.adk.tools import FunctionTool  # type: ignore[import-untyped,import-not-found]

        return FunctionTool(func, name=name)
    except ImportError:
        # Fallback: return a simple callable wrapper
        def _tool(**kwargs: Any) -> Any:
            return func(**kwargs)

        _tool.__name__ = name
        return _tool
