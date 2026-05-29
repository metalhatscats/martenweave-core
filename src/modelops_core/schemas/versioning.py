"""Schema versioning constants and validation for canonical objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Current schema version for newly created objects and repositories.
CURRENT_SCHEMA_VERSION: str = "1.0"

# Versions that are fully supported.
SUPPORTED_SCHEMA_VERSIONS: set[str] = {"1.0"}

# Versions that still work but generate deprecation warnings.
DEPRECATED_SCHEMA_VERSIONS: set[str] = set()

# Versions that are explicitly unsupported (will error).
UNSUPPORTED_SCHEMA_VERSIONS: set[str] = set()


@dataclass
class SchemaVersionIssue:
    """A schema version validation issue."""

    severity: str
    code: str
    message: str
    object_id: str | None = None
    source_file: str | None = None
    current_version: str | None = None
    suggested_fix: str | None = None


def validate_object_schema_version(
    frontmatter: dict[str, Any] | None,
    source_file: str,
) -> list[SchemaVersionIssue]:
    """Validate the schema_version field of a single canonical object.

    Rules:
    - Missing schema_version → INFO (encourage adoption)
    - schema_version in SUPPORTED → no issue
    - schema_version in DEPRECATED → WARNING
    - schema_version in UNSUPPORTED → ERROR
    - Unknown schema_version → WARNING (may be forward-compatible)
    """
    issues: list[SchemaVersionIssue] = []
    if frontmatter is None:
        return issues

    obj_id = frontmatter.get("id")
    obj_id_str = str(obj_id) if obj_id is not None else None
    version = frontmatter.get("schema_version")

    if version is None:
        issues.append(
            SchemaVersionIssue(
                severity="INFO",
                code="SCHEMA_VERSION_MISSING",
                message=(
                    f"Object '{obj_id_str or 'unknown'}' is missing "
                    f"schema_version. Current version is {CURRENT_SCHEMA_VERSION}."
                ),
                object_id=obj_id_str,
                source_file=source_file,
                current_version=CURRENT_SCHEMA_VERSION,
                suggested_fix=f'Add schema_version: "{CURRENT_SCHEMA_VERSION}" to the frontmatter.',
            )
        )
        return issues

    version_str = str(version).strip()
    if version_str in UNSUPPORTED_SCHEMA_VERSIONS:
        issues.append(
            SchemaVersionIssue(
                severity="ERROR",
                code="SCHEMA_VERSION_UNSUPPORTED",
                message=(
                    f"Object '{obj_id_str or 'unknown'}' uses unsupported "
                    f"schema_version '{version_str}'."
                ),
                object_id=obj_id_str,
                source_file=source_file,
                current_version=CURRENT_SCHEMA_VERSION,
                suggested_fix=f"Migrate to schema_version {CURRENT_SCHEMA_VERSION}.",
            )
        )
    elif version_str in DEPRECATED_SCHEMA_VERSIONS:
        issues.append(
            SchemaVersionIssue(
                severity="WARNING",
                code="SCHEMA_VERSION_DEPRECATED",
                message=(
                    f"Object '{obj_id_str or 'unknown'}' uses deprecated "
                    f"schema_version '{version_str}'."
                ),
                object_id=obj_id_str,
                source_file=source_file,
                current_version=CURRENT_SCHEMA_VERSION,
                suggested_fix=f"Update to schema_version {CURRENT_SCHEMA_VERSION}.",
            )
        )
    elif version_str not in SUPPORTED_SCHEMA_VERSIONS:
        issues.append(
            SchemaVersionIssue(
                severity="WARNING",
                code="SCHEMA_VERSION_UNKNOWN",
                message=(
                    f"Object '{obj_id_str or 'unknown'}' uses unknown "
                    f"schema_version '{version_str}'. "
                    f"Supported versions: {', '.join(sorted(SUPPORTED_SCHEMA_VERSIONS))}."
                ),
                object_id=obj_id_str,
                source_file=source_file,
                current_version=CURRENT_SCHEMA_VERSION,
                suggested_fix=f"Confirm compatibility or update to {CURRENT_SCHEMA_VERSION}.",
            )
        )

    return issues


def validate_repo_schema_version(
    config: dict[str, Any] | None,
    source_file: str | None = None,
) -> list[SchemaVersionIssue]:
    """Validate the schema_version field in repository config.

    Mirrors the object-level rules for repo-level schema_version.
    """
    issues: list[SchemaVersionIssue] = []
    if config is None:
        return issues

    version = config.get("schema_version")
    if version is None:
        issues.append(
            SchemaVersionIssue(
                severity="INFO",
                code="REPO_SCHEMA_VERSION_MISSING",
                message=(
                    "Repository config is missing schema_version. "
                    f"Current version is {CURRENT_SCHEMA_VERSION}."
                ),
                source_file=source_file,
                current_version=CURRENT_SCHEMA_VERSION,
                suggested_fix=f'Add schema_version: "{CURRENT_SCHEMA_VERSION}" '
                "to modelops.config.yaml.",
            )
        )
        return issues

    version_str = str(version).strip()
    if version_str in UNSUPPORTED_SCHEMA_VERSIONS:
        issues.append(
            SchemaVersionIssue(
                severity="ERROR",
                code="REPO_SCHEMA_VERSION_UNSUPPORTED",
                message=(f"Repository uses unsupported schema_version '{version_str}'."),
                source_file=source_file,
                current_version=CURRENT_SCHEMA_VERSION,
                suggested_fix=f"Migrate to schema_version {CURRENT_SCHEMA_VERSION}.",
            )
        )
    elif version_str in DEPRECATED_SCHEMA_VERSIONS:
        issues.append(
            SchemaVersionIssue(
                severity="WARNING",
                code="REPO_SCHEMA_VERSION_DEPRECATED",
                message=(f"Repository uses deprecated schema_version '{version_str}'."),
                source_file=source_file,
                current_version=CURRENT_SCHEMA_VERSION,
                suggested_fix=f"Update to schema_version {CURRENT_SCHEMA_VERSION}.",
            )
        )
    elif version_str not in SUPPORTED_SCHEMA_VERSIONS:
        issues.append(
            SchemaVersionIssue(
                severity="WARNING",
                code="REPO_SCHEMA_VERSION_UNKNOWN",
                message=(
                    f"Repository uses unknown schema_version '{version_str}'. "
                    f"Supported versions: {', '.join(sorted(SUPPORTED_SCHEMA_VERSIONS))}."
                ),
                source_file=source_file,
                current_version=CURRENT_SCHEMA_VERSION,
                suggested_fix=f"Confirm compatibility or update to {CURRENT_SCHEMA_VERSION}.",
            )
        )

    return issues
