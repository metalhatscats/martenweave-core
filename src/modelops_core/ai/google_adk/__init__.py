"""Optional Google ADK agent scaffold for Martenweave.

This module is only functional when the `google-adk` optional dependency
is installed. Importing without it raises a clear setup error.
"""

from __future__ import annotations

import os
from typing import Any

from modelops_core.ai.google_adk.tools import (  # noqa: E402
    TOOL_REGISTRY,
    build_index_tool,
    create_change_request_tool,
    create_patch_proposal_tool,
    preview_notifications_tool,
    profile_dataset_tool,
    trace_object_tool,
    validate_model_tool,
)

_HAS_ADK = False

try:
    import google.adk  # type: ignore[import-untyped,import-not-found]  # noqa: F401

    _HAS_ADK = True
except ImportError:
    pass


def _require_adk() -> None:
    if not _HAS_ADK:
        raise ImportError(
            "Google ADK is not installed. Install with: pip install martenweave-core[google_adk]"
        )


__all__ = [
    "TOOL_REGISTRY",
    "_HAS_ADK",
    "_require_adk",
    "build_index_tool",
    "create_change_request_tool",
    "create_patch_proposal_tool",
    "preview_notifications_tool",
    "profile_dataset_tool",
    "trace_object_tool",
    "validate_model_tool",
    "get_agent_config",
    "build_agent",
]


def get_agent_config() -> dict[str, Any]:
    """Return ADK agent configuration from environment."""
    _require_adk()
    return {
        "provider": os.getenv("MARTENWEAVE_AI_PROVIDER", "google_adk"),
        "api_key": os.getenv("GOOGLE_API_KEY", ""),
        "model": os.getenv("GOOGLE_ADK_MODEL", "gemini-2.5-flash"),
    }


def build_agent(
    repo_root: str | None = None,
) -> Any:
    """Build an ADK agent with Martenweave tools.

    Returns the agent instance if ADK is installed, otherwise raises ImportError.
    """
    _require_adk()
    # The actual ADK agent construction is deferred to the agent module
    # to keep this file importable without ADK installed.
    from modelops_core.ai.google_adk.agent import _build_agent

    return _build_agent(repo_root=repo_root)
