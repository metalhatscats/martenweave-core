"""Workspace boundary for the Martenweave local API.

A workspace binds a single repository root to a FastAPI application instance.
All filesystem access is restricted to the workspace roots, mutation endpoints
require a session token, and absolute paths are redacted from responses.
"""

from __future__ import annotations

import secrets
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from fastapi import Header, HTTPException

from modelops_core.config import load_repo_config, resolve_generated_path, resolve_model_path

_BLOCKED_SEGMENTS = frozenset({".git", ".env", ".ssh", ".gnupg"})


@dataclass(frozen=True)
class WorkspaceContext:
    """Bound context for a single API workspace."""

    repo_root: Path
    model_path: Path
    generated_path: Path
    read_only: bool
    session_token: str
    allowed_origins: list[str]

    @property
    def allowed_roots(self) -> tuple[Path, ...]:
        """Roots that user-supplied paths may resolve into."""
        return (self.repo_root, self.model_path, self.generated_path, self.repo_root / "data")


def _is_safe_path(path: Path, allowed_roots: tuple[Path, ...]) -> bool:
    """Return True when ``path`` is contained within an allowed root.

    Rejects:
        - Paths that escape the workspace via ``..`` or symlinks.
        - Paths containing blocked segments such as ``.git``.
        - Non-existent paths whose resolved location cannot be determined.
    """
    try:
        resolved = path.resolve(strict=False)
    except (OSError, RuntimeError):
        return False

    # Reject blocked segments anywhere in the path.
    for part in resolved.parts:
        if part in _BLOCKED_SEGMENTS:
            return False

    # Reject traversal that escapes allowed roots.
    for root in allowed_roots:
        try:
            resolved.relative_to(root.resolve())
            return True
        except ValueError:
            continue

    return False


def _redact_path(path: Path, repo_root: Path) -> str:
    """Return a workspace-relative path string, or a safe label if outside."""
    try:
        rel = Path(path).resolve().relative_to(repo_root.resolve())
        return str(rel).replace("\\", "/")
    except (ValueError, OSError):
        return "<outside-workspace>"


def create_workspace(
    repo_root: Path,
    read_only: bool = False,
    allowed_origins: list[str] | None = None,
) -> WorkspaceContext:
    """Create and validate a workspace context.

    Raises:
        ValueError: if the repository layout is missing required directories.
    """
    repo_root = Path(repo_root).resolve()
    model_path = resolve_model_path(repo_root)
    generated_path = resolve_generated_path(repo_root)

    if not model_path.exists():
        raise ValueError(f"model directory not found: {model_path}")

    session_token = secrets.token_hex(32)

    return WorkspaceContext(
        repo_root=repo_root,
        model_path=model_path,
        generated_path=generated_path,
        read_only=read_only,
        session_token=session_token,
        allowed_origins=list(allowed_origins or ["http://localhost", "http://127.0.0.1"]),
    )


def get_workspace(workspace: WorkspaceContext) -> Callable[[], WorkspaceContext]:
    """Return a FastAPI dependency that yields the bound workspace."""

    def _get_workspace() -> WorkspaceContext:
        return workspace

    return _get_workspace


def require_write_access(
    workspace: WorkspaceContext,
) -> Callable[[str | None], WorkspaceContext]:
    """Return a FastAPI dependency that enforces a writable workspace and token."""

    def _require_write_access(
        token: str | None = Header(None, alias="X-Martenweave-Session-Token"),
    ) -> WorkspaceContext:
        if workspace.read_only:
            raise HTTPException(
                status_code=403,
                detail="Workspace is read-only; mutations are disabled.",
            )
        if token is None or not secrets.compare_digest(token, workspace.session_token):
            raise HTTPException(
                status_code=403,
                detail="Invalid or missing X-Martenweave-Session-Token header.",
            )
        return workspace

    return _require_write_access


def workspace_name(workspace: WorkspaceContext) -> str:
    """Return the configured workspace name or a fallback label."""
    config = load_repo_config(workspace.repo_root)
    if config and config.workspace_name:
        return config.workspace_name
    return workspace.repo_root.name
