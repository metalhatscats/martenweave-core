"""Tests for dataset privacy and sanitization helpers."""

from __future__ import annotations

from modelops_core.imports.dataset_profiler import ColumnProfile, DatasetProfile
from modelops_core.imports.privacy import (
    DatasetPrivacyPolicy,
    apply_privacy_to_profile,
    apply_privacy_to_workbook,
    detect_high_risk_columns,
    is_high_risk_column,
    redact_sensitive_value,
    sanitize_profile_samples,
)


def test_is_high_risk_column_detects_email() -> None:
    assert is_high_risk_column("email") is True
    assert is_high_risk_column("user_email") is True
    assert is_high_risk_column("E_MAIL") is True


def test_is_high_risk_column_detects_phone() -> None:
    assert is_high_risk_column("phone") is True
    assert is_high_risk_column("mobile_number") is True
    assert is_high_risk_column("tel") is True


def test_is_high_risk_column_detects_name() -> None:
    assert is_high_risk_column("first_name") is True
    assert is_high_risk_column("lastName") is True
    assert is_high_risk_column("full_name") is True


def test_is_high_risk_column_detects_address() -> None:
    assert is_high_risk_column("address") is True
    assert is_high_risk_column("street") is True
    assert is_high_risk_column("postal_code") is True


def test_is_high_risk_column_detects_financial() -> None:
    assert is_high_risk_column("credit_card") is True
    assert is_high_risk_column("bank_account") is True
    assert is_high_risk_column("tax_id") is True
    assert is_high_risk_column("salary") is True


def test_is_high_risk_column_safe_columns() -> None:
    assert is_high_risk_column("customer_group") is False
    assert is_high_risk_column("sales_org") is False
    assert is_high_risk_column("product_id") is False
    assert is_high_risk_column("status") is False


def test_redact_sensitive_value() -> None:
    assert redact_sensitive_value("anything") == "[REDACTED]"
    assert redact_sensitive_value("") == "[REDACTED]"


def test_detect_high_risk_columns() -> None:
    profile = DatasetProfile(
        dataset_id="test",
        file_path="test.csv",
        file_hash="abc",
        columns=[
            ColumnProfile(name="email", position=1),
            ColumnProfile(name="sales_org", position=2),
            ColumnProfile(name="phone", position=3),
        ],
    )
    result = detect_high_risk_columns(profile)
    assert sorted(result) == ["email", "phone"]


def test_sanitize_profile_samples_redacts_high_risk() -> None:
    profile = DatasetProfile(
        dataset_id="test",
        file_path="test.csv",
        file_hash="abc",
        columns=[
            ColumnProfile(name="email", position=1, sample_values=["alice@example.com"]),
            ColumnProfile(name="sales_org", position=2, sample_values=["US01"]),
        ],
    )
    sanitized = sanitize_profile_samples(profile)
    assert sanitized.columns[0].sample_values == ["[REDACTED]"]
    assert sanitized.columns[1].sample_values == ["US01"]


def test_apply_privacy_to_profile_excludes_samples_by_default() -> None:
    profile = DatasetProfile(
        dataset_id="test",
        file_path="/secret/path.csv",
        file_hash="abc",
        columns=[
            ColumnProfile(name="customer_group", position=1, sample_values=["A", "B"]),
        ],
    )
    policy = DatasetPrivacyPolicy()
    result = apply_privacy_to_profile(profile, policy)
    assert result.file_path == ".../path.csv"
    assert result.columns[0].sample_values == []


def test_apply_privacy_to_profile_includes_samples_when_allowed() -> None:
    profile = DatasetProfile(
        dataset_id="test",
        file_path="/secret/path.csv",
        file_hash="abc",
        columns=[
            ColumnProfile(name="customer_group", position=1, sample_values=["A", "B"]),
            ColumnProfile(name="email", position=2, sample_values=["alice@example.com"]),
        ],
    )
    policy = DatasetPrivacyPolicy(include_raw_samples=True)
    result = apply_privacy_to_profile(profile, policy)
    assert result.columns[0].sample_values == ["A", "B"]
    assert result.columns[1].sample_values == ["[REDACTED]"]


def test_apply_privacy_to_workbook() -> None:
    from modelops_core.imports.dataset_profiler import WorkbookProfile

    sheet = DatasetProfile(
        dataset_id="test",
        file_path="/secret/path.xlsx",
        file_hash="abc",
        columns=[
            ColumnProfile(name="email", position=1, sample_values=["alice@example.com"]),
        ],
    )
    workbook = WorkbookProfile(
        dataset_id="test",
        file_path="/secret/path.xlsx",
        file_hash="abc",
        sheet_names=["Sheet1"],
        sheets=[sheet],
    )
    policy = DatasetPrivacyPolicy()
    result = apply_privacy_to_workbook(workbook, policy)
    assert result.file_path == ".../path.xlsx"
    assert result.sheets[0].columns[0].sample_values == []
