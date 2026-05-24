"""Dataset privacy policy and redaction helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from modelops_core.imports.dataset_profiler import DatasetProfile


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

    return new_profile
