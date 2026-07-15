#!/usr/bin/env python3
"""Validate `modelops <command>` snippets in docs against the real CLI.

Scans README.md and docs/**/*.md, extracts command examples, and checks that
each command path exists in the installed Typer application. Snippets can be
marked with <!-- modelops-freshness-ignore --> to skip validation (e.g. for
roadmap/future commands or historical examples).

Usage:
    .venv/bin/python scripts/validate_doc_commands.py
"""

from __future__ import annotations

import re
import sys
from collections.abc import Iterable
from pathlib import Path

import typer

from modelops_core.cli import app

IGNORE_MARKER = "<!-- modelops-freshness-ignore -->"
GLOBAL_IGNORE_MARKER = "<!-- modelops-freshness-ignore: all -->"
TOKEN_RE = re.compile(r"[a-z][a-z0-9-]*")


def _extract_command_path(line: str, start: int, valid_commands: set[str]) -> str | None:
    """Extract the longest valid command path after 'modelops' on a line.

    Stops when the next token does not extend a known command path, so
    positional arguments such as file paths are not treated as subcommands.
    """
    after = line[start + len("modelops") :]
    # Require whitespace then a command token. Exclude references like
    # modelops_core, modelops.config.yaml, modelops.db, modelops://, etc.
    if not re.match(r"\s+[a-z][a-z0-9-]*", after):
        return None

    remaining = after
    tokens: list[str] = []
    for match in TOKEN_RE.finditer(remaining):
        candidate = " ".join(tokens + [match.group(0)])
        # Accept the token if it is itself a valid command or could lead to one.
        if candidate in valid_commands or any(
            cmd.startswith(candidate + " ") for cmd in valid_commands
        ):
            tokens.append(match.group(0))
        elif not tokens:
            # First token after 'modelops' is not a known command at all.
            return match.group(0)
        else:
            break
    return " ".join(tokens) if tokens else None


def _snake_to_kebab(name: str) -> str:
    """Convert a snake_case Python name to a kebab-case CLI command name."""
    return name.replace("_", "-")


def _command_name(command) -> str | None:
    """Return the CLI name for a registered Typer command."""
    if command.name:
        return command.name
    if command.callback:
        return _snake_to_kebab(command.callback.__name__)
    return None


def _collect_commands(typer_app: typer.Typer, prefix: tuple[str, ...] = ()) -> set[str]:
    """Recursively collect all valid command paths from a Typer app."""
    commands: set[str] = set()

    for command in typer_app.registered_commands:
        name = _command_name(command)
        if name:
            path = prefix + (name,)
            commands.add(" ".join(path))

    for group in typer_app.registered_groups:
        if group.name:
            group_prefix = prefix + (group.name,)
            commands.add(" ".join(group_prefix))
            commands.update(_collect_commands(group.typer_instance, group_prefix))

    return commands


def _get_valid_commands() -> set[str]:
    """Return the set of valid command paths for the installed CLI."""
    return _collect_commands(app)


def _is_ignored(lines: list[str], snippet_line_index: int) -> bool:
    """Check whether the snippet line or the previous non-empty line is ignored."""
    if IGNORE_MARKER in lines[snippet_line_index]:
        return True
    for idx in range(snippet_line_index - 1, -1, -1):
        stripped = lines[idx].strip()
        if not stripped:
            continue
        if IGNORE_MARKER in stripped:
            return True
        # Stop searching once we hit non-comment content
        if not stripped.startswith("<!--"):
            break
    return False


def _find_invalid_snippets(file_path: Path, valid_commands: set[str]) -> list[tuple[int, str, str]]:
    """Return list of (line_number, line_text, matched_command) for invalid snippets."""
    invalid: list[tuple[int, str, str]] = []
    text = file_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    globally_ignored = GLOBAL_IGNORE_MARKER in text

    for idx, line in enumerate(lines):
        for match in re.finditer(r"\bmodelops\b", line):
            command_path = _extract_command_path(line, match.start(), valid_commands)
            if command_path is None:
                continue
            if command_path in valid_commands:
                continue
            # Unknown command path
            if globally_ignored or _is_ignored(lines, idx):
                continue
            invalid.append((idx + 1, line.rstrip("\n"), command_path))

    return invalid


def scan_docs(docs_root: Path) -> Iterable[tuple[Path, list[tuple[int, str, str]]]]:
    """Yield (file_path, invalid_snippets) for each doc file."""
    valid_commands = _get_valid_commands()

    files = [docs_root.parent / "README.md"]
    files.extend(sorted((docs_root / ".." / "docs").resolve().rglob("*.md")))

    for file_path in files:
        if not file_path.exists():
            continue
        invalid = _find_invalid_snippets(file_path, valid_commands)
        if invalid:
            yield file_path, invalid


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    exit_code = 0

    for file_path, invalid in scan_docs(repo_root / "docs"):
        exit_code = 1
        print(f"\n{file_path.relative_to(repo_root)}")
        for line_number, line_text, command_path in invalid:
            print(f"  line {line_number}: unknown command 'modelops {command_path}'")
            print(f"    {line_text.strip()}")

    if exit_code == 0:
        print("All documented modelops commands are fresh.")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
