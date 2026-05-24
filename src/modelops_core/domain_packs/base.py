"""Base class for domain packs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ValidationRule:
    """A domain-specific validation rule definition."""

    code: str
    message_template: str
    severity: str = "ERROR"


class DomainPack:
    """Base class for optional domain-specific modeling rules.

    Subclasses should override:
    - ``name`` — unique identifier
    - ``description`` — human-readable summary
    - ``validate(objects, registry)`` — return list of validation dicts
    """

    name: str = ""
    description: str = ""

    def validate(
        self,
        objects: list[Any],
        registry: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Run domain-specific validation on a batch of objects.

        Args:
            objects: List of ParsedObject instances.
            registry: ID-to-object lookup mapping.

        Returns:
            List of validation result dicts with keys:
            ``severity``, ``code``, ``message``, ``object_id``,
            ``suggested_fix``.
        """
        return []
