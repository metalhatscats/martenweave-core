"""Schema migration helpers for canonical model objects.

Migrations are registered as callables that transform a frontmatter dict
from one schema version to the next. They are applied in order until the
dict reaches the current schema version.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from modelops_core.schemas.versioning import CURRENT_SCHEMA_VERSION


@dataclass
class Migration:
    """A single schema migration step.

    Attributes:
        from_version: The schema version this migration starts from.
        to_version: The schema version this migration produces.
        description: Human-readable description of the migration.
        transform: Callable that mutates a frontmatter dict in place.
    """

    from_version: str
    to_version: str
    description: str
    transform: Callable[[dict[str, Any]], None]


# Registered migrations (ordered by from_version).
MIGRATIONS: list[Migration] = []

# Read compatibility is deliberately explicit.  These historic versions have
# the same frontmatter shape as 1.0, so migration only records the current
# schema marker.  Future versions are never rewritten by an older Core.
SUPPORTED_MIGRATION_SOURCES: frozenset[str] = frozenset({"", "0.0", "0.1", "0.9", "1.0"})


def can_migrate_from(version: object | None) -> bool:
    """Return whether this Core has a reviewed migration path for *version*."""
    return str(version or "").strip() in SUPPORTED_MIGRATION_SOURCES


def register_migration(migration: Migration) -> None:
    """Register a migration step.

    Migrations should be registered in ascending order.
    """
    MIGRATIONS.append(migration)


def needs_migration(frontmatter: dict[str, Any] | None) -> bool:
    """Return True if *frontmatter* has a schema_version that is not current."""
    if frontmatter is None:
        return False
    version = str(frontmatter.get("schema_version", "")).strip()
    if not version:
        return True
    return version != CURRENT_SCHEMA_VERSION


def migrate_object(frontmatter: dict[str, Any] | None) -> dict[str, Any] | None:
    """Apply registered migrations to *frontmatter* until current version.

    Returns a new dict (or the original if no migrations apply).
    The returned dict will have ``schema_version`` set to
    :data:`CURRENT_SCHEMA_VERSION`.

    If *frontmatter* is None, returns None.
    """
    if frontmatter is None:
        return None

    result = dict(frontmatter)
    current = str(result.get("schema_version", "")).strip() or "0.0"

    # BFS-like application: apply the next migration that matches current.
    max_steps = len(MIGRATIONS) + 1
    for _ in range(max_steps):
        if current == CURRENT_SCHEMA_VERSION:
            break
        for migration in MIGRATIONS:
            if migration.from_version == current:
                migration.transform(result)
                result["schema_version"] = migration.to_version
                current = migration.to_version
                break
        else:
            # No matching migration found; stop.
            break

    result["schema_version"] = CURRENT_SCHEMA_VERSION
    return result


def get_migration_path(from_version: str) -> list[Migration]:
    """Return the ordered list of migrations from *from_version* to current.

    Useful for previewing what changes a migration would make.
    """
    path: list[Migration] = []
    current = from_version
    seen: set[str] = set()

    while current != CURRENT_SCHEMA_VERSION:
        if current in seen:
            raise ValueError(f"Migration cycle detected starting from {from_version}")
        seen.add(current)

        for migration in MIGRATIONS:
            if migration.from_version == current:
                path.append(migration)
                current = migration.to_version
                break
        else:
            break

    return path


def preview_migration(frontmatter: dict[str, Any] | None) -> dict[str, Any]:
    """Return a preview of what :func:`migrate_object` would produce.

    Does not mutate the original dict.
    """
    if frontmatter is None:
        return {}
    result = migrate_object(dict(frontmatter))
    return result if result is not None else {}
