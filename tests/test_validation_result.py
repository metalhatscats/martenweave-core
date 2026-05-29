"""Tests for validation result models."""

from __future__ import annotations

from modelops_core.validation.result import ValidationResult, ValidationSeverity, ValidationSummary


class TestValidationSeverity:
    def test_values_are_distinct(self) -> None:
        assert ValidationSeverity.ERROR != ValidationSeverity.WARNING
        assert ValidationSeverity.WARNING != ValidationSeverity.INFO
        assert ValidationSeverity.ERROR != ValidationSeverity.INFO

    def test_string_values(self) -> None:
        assert str(ValidationSeverity.ERROR) == "ERROR"
        assert str(ValidationSeverity.WARNING) == "WARNING"
        assert str(ValidationSeverity.INFO) == "INFO"


class TestValidationResult:
    def test_minimal_construction(self) -> None:
        r = ValidationResult(severity=ValidationSeverity.ERROR, code="TEST", message="msg")
        assert r.object_id is None
        assert r.object_type is None

    def test_model_dump_roundtrip(self) -> None:
        r = ValidationResult(
            severity=ValidationSeverity.WARNING,
            code="TEST",
            message="msg",
            object_id="OBJ-001",
        )
        d = r.model_dump()
        assert d["severity"] == "WARNING"
        assert d["code"] == "TEST"
        assert d["object_id"] == "OBJ-001"


class TestValidationSummary:
    def test_empty_is_valid(self) -> None:
        summary = ValidationSummary()
        assert summary.is_valid is True
        assert summary.error_count == 0

    def test_only_warnings_is_valid(self) -> None:
        summary = ValidationSummary(
            results=[
                ValidationResult(severity=ValidationSeverity.WARNING, code="W1", message="m"),
            ]
        )
        assert summary.is_valid is True
        assert summary.error_count == 0
        assert summary.warning_count == 1

    def test_with_error_is_invalid(self) -> None:
        summary = ValidationSummary(
            results=[
                ValidationResult(severity=ValidationSeverity.ERROR, code="E1", message="m"),
                ValidationResult(severity=ValidationSeverity.WARNING, code="W1", message="m"),
            ]
        )
        assert summary.is_valid is False
        assert summary.error_count == 1

    def test_summary_by_code_aggregates(self) -> None:
        summary = ValidationSummary(
            results=[
                ValidationResult(severity=ValidationSeverity.ERROR, code="E1", message="m1"),
                ValidationResult(severity=ValidationSeverity.ERROR, code="E1", message="m2"),
                ValidationResult(severity=ValidationSeverity.WARNING, code="W1", message="m3"),
            ]
        )
        by_code = summary.summary_by_code
        assert by_code["E1"]["count"] == 2
        assert by_code["W1"]["count"] == 1

    def test_summary_by_code_is_sorted(self) -> None:
        summary = ValidationSummary(
            results=[
                ValidationResult(severity=ValidationSeverity.WARNING, code="Z", message="m"),
                ValidationResult(severity=ValidationSeverity.ERROR, code="A", message="m"),
            ]
        )
        keys = list(summary.summary_by_code.keys())
        assert keys == ["A", "Z"]
