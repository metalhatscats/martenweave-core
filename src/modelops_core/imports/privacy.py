"""Dataset privacy policy and redaction helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from modelops_core.imports.dataset_profiler import DatasetProfile, WorkbookProfile

# High-risk column name patterns (case-insensitive)
HIGH_RISK_COLUMN_PATTERNS = [
    r"email",
    r"e[-_]?mail",
    r"phone",
    r"tel",
    r"mobile",
    r"fax",
    r"ssn",
    r"social[-_]?sec",
    r"credit[-_]?card",
    r"card[-_]?number",
    r"cc[-_]?num",
    r"iban",
    r"account[-_]?number",
    r"bank[-_]?account",
    r"tax[-_]?id",
    r"vat",
    r"passport",
    r"driver[-_]?lic",
    r"address",
    r"street",
    r"zip",
    r"postal",
    r"city",
    r"country",
    r"first[-_]?name",
    r"last[-_]?name",
    r"full[-_]?name",
    r"given[-_]?name",
    r"family[-_]?name",
    r"person[-_]?name",
    r"contact[-_]?name",
    r"user[-_]?name",
    r"dob",
    r"birth",
    r"age",
    r"gender",
    r"salary",
    r"income",
    r"compensation",
    r"ip[-_]?address",
    r"mac[-_]?address",
    r"latitude",
    r"longitude",
    r"geo",
    r"free[-_]?text",
    r"comments",
    r"notes",
    r"remarks",
]

_HIGH_RISK_RE = re.compile("|".join(f"(?:{p})" for p in HIGH_RISK_COLUMN_PATTERNS), re.IGNORECASE)


@dataclass
class DatasetPrivacyPolicy:
    redact_file_path: bool = True
    include_raw_samples: bool = False
    allow_in_ai_context: bool = False
    allow_in_logs: bool = False


def redact_file_path(path: str) -> str:
    """Redact the directory portion of a file path."""
    p = Path(path)
    return f".../{p.name}"


def is_high_risk_column(column_name: str) -> bool:
    """Return True if the column name looks like it could contain PII/sensitive data."""
    return bool(_HIGH_RISK_RE.search(column_name))


def redact_sensitive_value(value: str) -> str:
    """Redact a single sensitive value."""
    return "[REDACTED]"


def detect_high_risk_columns(profile: DatasetProfile) -> list[str]:
    """Return a list of high-risk column names in the profile."""
    return [col.name for col in profile.columns if is_high_risk_column(col.name)]


def sanitize_profile_samples(profile: DatasetProfile) -> DatasetProfile:
    """Redact sample values for high-risk columns in place."""
    for col in profile.columns:
        if is_high_risk_column(col.name) and col.sample_values:
            col.sample_values = [redact_sensitive_value(v) for v in col.sample_values]
    return profile


def apply_privacy_to_profile(
    profile: DatasetProfile, policy: DatasetPrivacyPolicy
) -> DatasetProfile:
    """Return a privacy-scrubbed copy of a DatasetProfile."""
    from dataclasses import replace

    new_profile = replace(profile)
    if policy.redact_file_path:
        new_profile.file_path = redact_file_path(profile.file_path)

    if not policy.include_raw_samples:
        for col in new_profile.columns:
            col.sample_values = []
    else:
        # Even when raw samples are allowed, redact high-risk columns
        for col in new_profile.columns:
            if is_high_risk_column(col.name) and col.sample_values:
                col.sample_values = [redact_sensitive_value(v) for v in col.sample_values]

    return new_profile


def apply_privacy_to_workbook(
    profile: WorkbookProfile, policy: DatasetPrivacyPolicy
) -> WorkbookProfile:
    """Return a privacy-scrubbed copy of a WorkbookProfile."""
    from dataclasses import replace

    new_profile = replace(profile)
    if policy.redact_file_path:
        new_profile.file_path = redact_file_path(profile.file_path)

    new_profile.sheets = [apply_privacy_to_profile(sheet, policy) for sheet in new_profile.sheets]
    return new_profile
