"""Release preflight guard.

Ensures that a Git release tag matches the package version declared in
``pyproject.toml`` before build artifacts are produced or published. This
prevents accidental stable-version publishes from pre-release tags such as
``v0.4.1a1`` when the package still declares ``0.4.1``.
"""

from __future__ import annotations

import argparse
import os
import sys
import tomllib
from pathlib import Path


def get_package_version(pyproject_path: Path) -> str:
    """Read ``project.version`` from *pyproject_path*."""
    if not pyproject_path.exists():
        raise FileNotFoundError(f"pyproject.toml not found at {pyproject_path}")

    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)

    version = data.get("project", {}).get("version")
    if not version:
        raise ValueError("project.version is missing or empty in pyproject.toml")

    return version


def normalize_tag(tag: str | None) -> str:
    """Normalize a Git tag by stripping ``refs/tags/`` and a leading ``v``."""
    if not tag:
        raise ValueError("tag is empty")

    tag = tag.strip()
    if tag.startswith("refs/tags/"):
        tag = tag[len("refs/tags/") :]
    if tag.startswith("v"):
        tag = tag[1:]
    if not tag:
        raise ValueError("tag is empty after normalizing")

    return tag


def check(tag: str | None, pyproject_path: Path) -> tuple[bool, str]:
    """Return (ok, message) comparing *tag* version to package version."""
    try:
        package_version = get_package_version(pyproject_path)
    except (FileNotFoundError, ValueError) as exc:
        return False, f"ERROR: {exc}"

    try:
        normalized_tag = normalize_tag(tag)
    except ValueError as exc:
        return False, f"ERROR: invalid tag {tag!r}: {exc}"

    if normalized_tag != package_version:
        return (
            False,
            f"ERROR: tag version '{normalized_tag}' does not match package version "
            f"'{package_version}'",
        )

    return True, f"OK: tag version '{normalized_tag}' matches package version '{package_version}'"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify the release tag matches the package version in pyproject.toml"
    )
    parser.add_argument(
        "--tag",
        default=os.environ.get("GITHUB_REF_NAME"),
        help="Git tag to validate (defaults to GITHUB_REF_NAME)",
    )
    parser.add_argument(
        "--pyproject",
        type=Path,
        default=Path("pyproject.toml"),
        help="Path to pyproject.toml",
    )
    args = parser.parse_args(argv)

    ok, message = check(args.tag, args.pyproject)
    stream = sys.stdout if ok else sys.stderr
    print(message, file=stream)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
