"""Bound local-workspace policy shared by every API route."""

from __future__ import annotations

import secrets
from pathlib import Path

from fastapi import Header, HTTPException

_workspace_root: Path | None = None
_mutation_token: str | None = None


def configure_workspace(repo_root: Path, mutation_token: str | None = None) -> None:
    """Bind this process to one repository; never trust request path parameters."""
    global _workspace_root, _mutation_token
    _workspace_root = repo_root.resolve()
    _mutation_token = mutation_token


def clear_workspace() -> None:
    """Clear process-local binding for isolated in-process tests."""
    global _workspace_root, _mutation_token
    _workspace_root = None
    _mutation_token = None


def resolve_workspace(requested_repo: str | None) -> Path:
    """Resolve the bound workspace and reject attempts to switch it."""
    if _workspace_root is None:
        # Compatibility for in-process library/test use. `martenweave serve`
        # always configures a bound workspace before accepting requests.
        return Path(requested_repo).resolve() if requested_repo else Path.cwd().resolve()
    if requested_repo is not None and Path(requested_repo).resolve() != _workspace_root:
        raise HTTPException(status_code=403, detail="API is bound to its configured workspace.")
    return _workspace_root


def resolve_workspace_input(path_value: str, repo_root: Path) -> Path:
    """Allow file inputs only inside the bound workspace, including real symlink targets."""
    candidate = Path(path_value).resolve()
    if _workspace_root is None:
        return candidate
    try:
        candidate.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise HTTPException(
            status_code=403, detail="Input file must be inside the bound workspace."
        ) from exc
    return candidate


def workspace_label() -> str:
    return "." if _workspace_root is not None else str(Path.cwd().resolve())


def workspace_is_bound() -> bool:
    return _workspace_root is not None


def mutation_enabled() -> bool:
    return _workspace_root is None or _mutation_token is not None


def require_mutation_token(x_martenweave_token: str | None = Header(None)) -> None:
    """Protect writes; an unconfigured server is intentionally read-only."""
    if _workspace_root is None:
        return
    if _mutation_token is None:
        raise HTTPException(
            status_code=403, detail="API mutations are disabled for this workspace."
        )
    if x_martenweave_token is None or not secrets.compare_digest(
        x_martenweave_token, _mutation_token
    ):
        raise HTTPException(
            status_code=401, detail="Valid X-Martenweave-Token required for mutations."
        )
