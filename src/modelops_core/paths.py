"""Path traversal guard."""

from __future__ import annotations

from pathlib import Path

from modelops_core.errors import PathTraversalError


def resolve_allowed_path(
    target: str | Path,
    allowed_roots: list[Path] | None = None,
) -> Path:
    """Resolve *target* and ensure it lies within an allowed root.

    Args:
        target: The path to resolve.
        allowed_roots: List of allowed root directories. If None, defaults to
            the current working directory and ``/tmp``.

    Returns:
        The resolved, absolute path.

    Raises:
        PathTraversalError: If the resolved path escapes all allowed roots.
    """
    path = Path(target).resolve()

    if allowed_roots is None:
        allowed_roots = [Path.cwd().resolve(), Path("/tmp").resolve()]

    for root in allowed_roots:
        try:
            path.relative_to(root.resolve())
            return path
        except ValueError:
            continue

    raise PathTraversalError(
        f"Path '{path}' is outside allowed roots: "
        f"{[str(r) for r in allowed_roots]}"
    )
