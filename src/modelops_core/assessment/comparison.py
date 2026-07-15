"""Deterministic lifecycle comparison for two migration assessment runs."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from modelops_core.assessment.finding_contract import AssessmentFinding


class AssessmentComparisonError(ValueError):
    """Raised when an assessment package cannot be compared safely."""


@dataclass(frozen=True)
class FindingLifecycleChange:
    """A lifecycle relationship established only through the stable finding ID."""

    finding_id: str
    lifecycle: str
    previous: dict[str, Any] | None
    current: dict[str, Any] | None


@dataclass
class AssessmentComparisonReport:
    """Portable comparison output for reports, APIs, and review workflows."""

    base_run_id: str
    head_run_id: str
    base_fingerprint: str
    head_fingerprint: str
    input_changes: dict[str, list[str]] = field(default_factory=dict)
    findings: list[FindingLifecycleChange] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        counts: dict[str, int] = {}
        for finding in self.findings:
            counts[finding.lifecycle] = counts.get(finding.lifecycle, 0) + 1
        return {
            "base_run_id": self.base_run_id,
            "head_run_id": self.head_run_id,
            "base_fingerprint": self.base_fingerprint,
            "head_fingerprint": self.head_fingerprint,
            "input_changes": self.input_changes,
            "counts": counts,
            "findings": [asdict(finding) for finding in self.findings],
        }


def _read_json(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise AssessmentComparisonError(f"{label} not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AssessmentComparisonError(f"{label} is not valid JSON: {path}") from exc
    if not isinstance(data, dict):
        raise AssessmentComparisonError(f"{label} must contain a JSON object: {path}")
    return data


def _load_run(manifest_path: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    manifest = _read_json(manifest_path, "Assessment manifest")
    required = ("run_id", "input_fingerprint", "input_checksums", "martenweave_version")
    missing = [name for name in required if not manifest.get(name)]
    if missing:
        raise AssessmentComparisonError(
            f"Assessment manifest is incompatible; missing {', '.join(missing)}: {manifest_path}"
        )
    checksums = manifest["input_checksums"]
    if not isinstance(checksums, dict):
        raise AssessmentComparisonError(
            f"Assessment manifest input_checksums must be an object: {manifest_path}"
        )

    findings_data = _read_json(manifest_path.parent / "findings.json", "Assessment findings")
    raw_findings = findings_data.get("findings")
    if not isinstance(raw_findings, list):
        raise AssessmentComparisonError("Assessment findings must contain a findings array")
    findings: dict[str, dict[str, Any]] = {}
    for raw in raw_findings:
        try:
            finding = AssessmentFinding.model_validate(raw)
        except Exception as exc:
            raise AssessmentComparisonError(
                "Assessment findings do not satisfy the typed contract"
            ) from exc
        if finding.provenance.assessment_run_id != manifest["run_id"]:
            raise AssessmentComparisonError(
                f"Finding {finding.id} provenance does not belong to manifest run "
                f"{manifest['run_id']}"
            )
        if finding.id in findings:
            raise AssessmentComparisonError(
                f"Duplicate stable finding ID {finding.id} in {manifest_path}"
            )
        findings[finding.id] = finding.model_dump(mode="json")
    return manifest, findings


def _input_changes(base: dict[str, Any], head: dict[str, Any]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {
        "workbook_or_evidence": [],
        "canonical_model": [],
        "configuration": [],
        "rule_set": [],
    }
    base_checksums = base["input_checksums"]
    head_checksums = head["input_checksums"]
    for key in sorted(set(base_checksums) | set(head_checksums)):
        if base_checksums.get(key) == head_checksums.get(key):
            continue
        if key.startswith("model/"):
            groups["canonical_model"].append(key)
        elif key == "modelops.config.yaml":
            groups["configuration"].append(key)
        else:
            groups["workbook_or_evidence"].append(key)
    base_packs = base.get("inputs", {}).get(
        "enabled_domain_packs", base.get("enabled_domain_packs", [])
    )
    head_packs = head.get("inputs", {}).get(
        "enabled_domain_packs", head.get("enabled_domain_packs", [])
    )
    if base_packs != head_packs:
        groups["rule_set"].append("enabled_domain_packs")
    return {kind: keys for kind, keys in groups.items() if keys}


def compare_assessments(base_manifest: Path, head_manifest: Path) -> AssessmentComparisonReport:
    """Compare two compatible assessment packages using stable finding identities only."""
    base, base_findings = _load_run(base_manifest)
    head, head_findings = _load_run(head_manifest)
    base_major = str(base["martenweave_version"]).split(".", maxsplit=1)[0]
    head_major = str(head["martenweave_version"]).split(".", maxsplit=1)[0]
    if base_major != head_major:
        raise AssessmentComparisonError(
            "Assessment manifests use incompatible Martenweave major versions; compare within one "
            "major version."
        )

    changes: list[FindingLifecycleChange] = []
    for finding_id in sorted(set(base_findings) | set(head_findings)):
        previous = base_findings.get(finding_id)
        current = head_findings.get(finding_id)
        if previous is None:
            lifecycle = "new"
        elif current is None:
            lifecycle = "resolved"
        elif previous["lifecycle_state"] == "resolved" and current["lifecycle_state"] != "resolved":
            lifecycle = "reopened"
        elif previous["severity"] != current["severity"]:
            lifecycle = "severity_changed"
        else:
            lifecycle = "unchanged"
        changes.append(
            FindingLifecycleChange(
                finding_id=finding_id,
                lifecycle=lifecycle,
                previous=previous,
                current=current,
            )
        )
    return AssessmentComparisonReport(
        base_run_id=base["run_id"],
        head_run_id=head["run_id"],
        base_fingerprint=base["input_fingerprint"],
        head_fingerprint=head["input_fingerprint"],
        input_changes=_input_changes(base, head),
        findings=changes,
    )


def write_assessment_comparison(
    report: AssessmentComparisonReport, out_dir: Path
) -> tuple[Path, Path]:
    """Write machine-readable and review-friendly comparison outputs."""
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = report.to_dict()
    json_path = out_dir / "assessment-comparison.json"
    markdown_path = out_dir / "assessment-comparison.md"
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Assessment comparison",
        "",
        f"- Base run: `{report.base_run_id}`",
        f"- Head run: `{report.head_run_id}`",
        "",
        "## Finding lifecycle",
        "",
        "| Finding | Lifecycle | Prior evidence | Current evidence |",
        "| --- | --- | --- | --- |",
    ]
    for finding in report.findings:
        prior = finding.previous["provenance"]["assessment_run_id"] if finding.previous else "—"
        current = finding.current["provenance"]["assessment_run_id"] if finding.current else "—"
        lines.append(f"| `{finding.finding_id}` | {finding.lifecycle} | `{prior}` | `{current}` |")
    lines.extend(["", "## Input changes", ""])
    if report.input_changes:
        for kind, keys in report.input_changes.items():
            lines.append(f"- **{kind}:** {', '.join(f'`{key}`' for key in keys)}")
    else:
        lines.append("No checksum or rule-set changes recorded.")
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, markdown_path
