"""Resolve synthetic assets shipped with the installed distribution."""

from __future__ import annotations

from pathlib import Path


def bundled_asset_path(*parts: str) -> Path:
    """Return a shipped asset path, with a source-tree fallback for development.

    Wheels keep these files next to this module.  The fallback keeps editable
    source checkouts usable without making installed commands depend on a
    sibling repository, tests directory, or examples tree.
    """
    installed = Path(__file__).parent / "assets"
    candidate = installed.joinpath(*parts)
    if candidate.exists():
        return candidate
    return Path(__file__).resolve().parents[2].joinpath(*parts)
