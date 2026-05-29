"""Validation result models."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ValidationSeverity(StrEnum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


class ValidationResult(BaseModel):
    """A single validation finding."""

    severity: ValidationSeverity
    code: str
    message: str
    object_id: str | None = Field(default=None)
    object_type: str | None = Field(default=None)
    source_file: str | None = Field(default=None)
    field_path: str | None = Field(default=None)
    related_objects: list[str] | None = Field(default=None)
    suggested_fix: str | None = Field(default=None)
    details: dict[str, Any] | None = Field(default=None)


class ValidationSummary(BaseModel):
    """Aggregated validation results."""

    results: list[ValidationResult] = Field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for r in self.results if r.severity == ValidationSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for r in self.results if r.severity == ValidationSeverity.WARNING)

    @property
    def info_count(self) -> int:
        return sum(1 for r in self.results if r.severity == ValidationSeverity.INFO)

    @property
    def is_valid(self) -> bool:
        return self.error_count == 0

    @property
    def summary_by_code(self) -> dict[str, dict[str, Any]]:
        """Group results by validation code with severity and count."""
        groups: dict[str, dict[str, Any]] = {}
        for r in self.results:
            entry = groups.setdefault(r.code, {"severity": str(r.severity), "count": 0})
            entry["count"] += 1
        return dict(sorted(groups.items()))
