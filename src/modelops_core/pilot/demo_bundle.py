"""Deterministic public demo bundle builder.

Builds a repeatable, sanitized package suitable for design-partner demos and
public case-study sharing. The bundle runs the golden SAP migration assessment,
records a small set of human dispositions, and packages only shareable artifacts.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from modelops_core import __version__
from modelops_core.guardrails.secrets import SecretFinding, scan_repo
from modelops_core.pilot import executive_summary as executive_summary_service
from modelops_core.pilot import outcome as pilot_outcome_service
from modelops_core.pilot import review as assessment_review_service
from modelops_core.pilot.sanitize import sanitize_assessment
from modelops_core.run.migration_assessment import generate_migration_assessment


@dataclass
class DemoBundle:
    """A built demo bundle."""

    bundle_dir: Path
    manifest: dict[str, Any]


@dataclass
class BundleValidationResult:
    """Result of validating a demo bundle."""

    valid: bool
    errors: list[str] = field(default_factory=list)


_REQUIRED_ARTIFACTS: frozenset[str] = frozenset(
    {
        "executive-summary.md",
        "executive-summary.json",
        "finding-review-summary.json",
        "pilot-outcome.md",
        "pilot-outcome.json",
        "sanitization-manifest.json",
    }
)

_BOUNDARY_NOTES: str = (
    "This bundle is intended for public demo and case-study sharing only. "
    "It contains no raw customer datasets, no secrets, and no machine-specific paths. "
    "Confirming findings were recorded against a synthetic workbook fixture; "
    "they do not represent a real client's migration state."
)

_GENERATION_COMMAND: str = (
    "martenweave demo-bundle build --repo <repo> --mapping <mapping> --out <out>"
)


def _file_hash(path: Path) -> str:
    """Return SHA-256 hex digest for a file."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _default_repo_root() -> Path:
    """Return the bundled customer-bp example repository path."""
    return Path(__file__).resolve().parents[4] / "examples" / "customer_bp_model"


def _default_mapping_path() -> Path:
    """Return the bundled synthetic SAP mapping workbook path."""
    return (
        Path(__file__).resolve().parents[4]
        / "tests"
        / "fixtures"
        / "pilot"
        / "sap_customer_mapping.xlsx"
    )


def _record_demo_dispositions(assessment_dir: Path, generated_at: str) -> None:
    """Record a deterministic mix of dispositions for demo purposes."""
    findings_data = assessment_review_service.load_findings(assessment_dir)
    findings = findings_data.get("findings", [])

    # Pick a small, deterministic sample of findings and assign mixed dispositions.
    disposition_sequence = [
        "confirmed",
        "false_positive",
        "accepted_risk",
        "deferred",
        "resolved",
    ]
    for finding, disposition in zip(findings, disposition_sequence, strict=False):
        finding_id = finding.get("id")
        if not finding_id:
            continue
        assessment_review_service.set_review(
            assessment_dir=assessment_dir,
            finding_id=finding_id,
            disposition=disposition,
            reviewer="martenweave-demo",
            note=f"Demo disposition recorded for public bundle ({disposition}).",
            reviewed_at=generated_at,
        )


def _write_finding_review_summary(assessment_dir: Path, out_dir: Path) -> Path:
    """Write a JSON summary of the current finding-review state."""
    summary = assessment_review_service.summarize_reviews(assessment_dir)
    path = out_dir / "finding-review-summary.json"
    path.write_text(
        json.dumps(summary, indent=2, default=str, sort_keys=True),
        encoding="utf-8",
    )
    return path


def _collect_artifact_manifest(bundle_dir: Path) -> list[dict[str, Any]]:
    """Collect all files in the bundle with size and sha256."""
    artifacts: list[dict[str, Any]] = []
    for path in sorted(bundle_dir.rglob("*")):
        if path.is_file():
            rel = path.relative_to(bundle_dir).as_posix()
            artifacts.append(
                {
                    "path": rel,
                    "size": path.stat().st_size,
                    "sha256": _file_hash(path),
                }
            )
    return artifacts


def build_demo_bundle(
    out_dir: Path,
    repo_root: Path | None = None,
    mapping_path: Path | None = None,
    generated_at: str | None = None,
) -> DemoBundle:
    """Build a deterministic, sanitized demo bundle.

    Args:
        out_dir: Directory where the bundle will be written. This directory
            becomes the bundle root and will contain ``bundle-manifest.json``.
        repo_root: Model repository to assess. Defaults to the bundled
            ``examples/customer_bp_model`` when run from the source tree.
        mapping_path: Synthetic mapping workbook. Defaults to the bundled
            ``tests/fixtures/pilot/sap_customer_mapping.xlsx``.
        generated_at: Optional ISO timestamp for deterministic output.

    Returns:
        ``DemoBundle`` with the bundle directory and manifest.
    """
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    repo_root = (repo_root or _default_repo_root()).resolve()
    mapping_path = (mapping_path or _default_mapping_path()).resolve()

    if not repo_root.exists():
        raise FileNotFoundError(f"Repository not found: {repo_root}")
    if not mapping_path.exists():
        raise FileNotFoundError(f"Mapping workbook not found: {mapping_path}")

    generated_at = generated_at or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    fixture_hash = _file_hash(mapping_path)

    # Run the golden migration assessment in a hidden build directory.
    assessment_dir = out_dir / ".demo-build" / "assessment"
    assessment_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = assessment_dir / "manifest.json"
    generate_migration_assessment(
        repo_root=repo_root,
        mapping_path=mapping_path,
        dataset_path=None,
        evidence_paths=[],
        out_dir=assessment_dir,
        generated_at=generated_at,
    )

    # Record deterministic demo dispositions.
    _record_demo_dispositions(assessment_dir, generated_at)

    # Generate review-facing outputs.
    _write_finding_review_summary(assessment_dir, assessment_dir)

    summary = executive_summary_service.generate_executive_summary(
        manifest_path,
        generated_at=generated_at,
    )
    executive_summary_service.write_executive_summary(
        summary, assessment_dir / "executive-summary.md"
    )

    outcome = pilot_outcome_service.generate_pilot_outcome(
        manifest_path,
        baselines={
            "prior_trace_hours": 4.0,
            "review_hours": 2.0,
            "onboarding_days": 5.0,
        },
        generated_at=generated_at,
    )
    pilot_outcome_service.write_pilot_outcome(outcome, assessment_dir / "pilot-outcome.md")

    # Sanitize and package only shareable artifacts into the bundle root.
    bundle_dir = out_dir
    sanitize_assessment(
        assessment_dir,
        bundle_dir,
        exclude_raw_datasets=True,
    )

    # Copy the review summary into the bundle (sanitize skips files it does not know).
    review_summary_src = assessment_dir / "finding-review-summary.json"
    if review_summary_src.exists():
        shutil.copy2(review_summary_src, bundle_dir / "finding-review-summary.json")

    # Drop non-deterministic binary workbooks from the public bundle and
    # remove their entries from the copied assessment manifest.
    assessment_manifest_path = bundle_dir / "manifest.json"
    if assessment_manifest_path.exists():
        assessment_manifest = json.loads(assessment_manifest_path.read_text(encoding="utf-8"))
        assessment_manifest["generated_artifacts"] = [
            a
            for a in assessment_manifest.get("generated_artifacts", [])
            if a["path"] != "manifest.json" and not a["path"].lower().endswith(".xlsx")
        ]
        assessment_manifest_path.write_text(
            json.dumps(assessment_manifest, indent=2, sort_keys=True),
            encoding="utf-8",
        )
    for path in list(bundle_dir.rglob("*.xlsx")):
        path.unlink()

    # Normalize the sanitization manifest for determinism (fixed timestamp and
    # redacted machine-specific paths).
    sanitize_manifest_path = bundle_dir / "sanitization-manifest.json"
    if sanitize_manifest_path.exists():
        sanitize_manifest = json.loads(sanitize_manifest_path.read_text(encoding="utf-8"))
        sanitize_manifest["generated_at"] = generated_at
        for key in ("input_dir", "output_dir"):
            if sanitize_manifest.get(key):
                sanitize_manifest[key] = "<redacted-path>"
        sanitize_manifest_path.write_text(
            json.dumps(sanitize_manifest, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    # Remove the build directory; only sanitized bundle artifacts remain.
    build_dir = out_dir / ".demo-build"
    if build_dir.exists():
        shutil.rmtree(build_dir)

    # Write bundle manifest (exclude the manifest from its own artifact list).
    artifacts = [
        a for a in _collect_artifact_manifest(bundle_dir) if a["path"] != "bundle-manifest.json"
    ]
    manifest: dict[str, Any] = {
        "tool": "martenweave",
        "version": __version__,
        "generated_at": generated_at,
        "repo_name": manifest_path.parent.name,
        "fixture_version": fixture_hash,
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "generation_command": _GENERATION_COMMAND,
        "boundary_notes": _BOUNDARY_NOTES,
    }
    manifest_path_bundle = bundle_dir / "bundle-manifest.json"
    manifest_path_bundle.write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    return DemoBundle(bundle_dir=bundle_dir, manifest=manifest)


def validate_demo_bundle(bundle_dir: Path) -> list[str]:
    """Validate a demo bundle.

    Checks that required artifacts exist, recorded checksums match, no raw
    datasets are present, and no secrets were detected.

    Returns:
        A list of human-readable validation errors. An empty list means valid.
    """
    bundle_dir = bundle_dir.resolve()
    errors: list[str] = []

    if not bundle_dir.exists():
        return [f"Bundle directory not found: {bundle_dir}"]

    manifest_path = bundle_dir / "bundle-manifest.json"
    if not manifest_path.exists():
        errors.append("Missing bundle-manifest.json")
        return errors

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"bundle-manifest.json is not valid JSON: {exc}")
        return errors

    artifacts = manifest.get("artifacts", [])
    artifact_paths = {a["path"] for a in artifacts}
    missing_required = _REQUIRED_ARTIFACTS - artifact_paths
    if missing_required:
        errors.append(f"Missing required artifacts: {', '.join(sorted(missing_required))}")

    for artifact in artifacts:
        rel = artifact.get("path", "")
        expected_hash = artifact.get("sha256", "")
        path = bundle_dir / rel
        if not path.exists():
            errors.append(f"Artifact missing on disk: {rel}")
            continue
        if expected_hash and _file_hash(path) != expected_hash:
            errors.append(f"Checksum mismatch for artifact: {rel}")

    if any("dataset_readiness" in a["path"] for a in artifacts):
        errors.append("Bundle contains raw dataset artifacts under dataset_readiness/")

    secret_findings = scan_repo(bundle_dir)
    for finding in secret_findings:
        if isinstance(finding, SecretFinding):
            errors.append(
                f"Potential secret in {finding.file_path}:{finding.line_number} "
                f"({finding.secret_type})"
            )
        else:
            errors.append(f"Potential secret finding: {finding}")

    return errors
