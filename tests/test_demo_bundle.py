"""Tests for the deterministic public demo bundle builder."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from modelops_core.cli import app

runner = CliRunner()

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "pilot"
MAPPING_WORKBOOK = FIXTURE_DIR / "sap_customer_mapping.xlsx"


def test_demo_bundle_defaults_resolve_bundled_source_tree_assets() -> None:
    """Source-tree defaults support the documented no-input demo path."""
    from modelops_core.pilot.demo_bundle import _default_mapping_path, _default_repo_root

    assert (_default_repo_root() / "modelops.config.yaml").is_file()
    assert _default_mapping_path().is_file()


@pytest.fixture
def demo_bundle(sample_repo: Path, tmp_path: Path):
    """Build a demo bundle using the golden pilot fixture."""
    from modelops_core.pilot.demo_bundle import build_demo_bundle

    out_dir = tmp_path / "demo-bundle"
    bundle = build_demo_bundle(
        out_dir=out_dir,
        repo_root=sample_repo,
        mapping_path=MAPPING_WORKBOOK,
        generated_at="2024-01-15T09:00:00Z",
    )
    return bundle


@pytest.mark.skipif(not MAPPING_WORKBOOK.exists(), reason="pilot fixture missing")
def test_build_demo_bundle_creates_manifest_and_artifacts(demo_bundle) -> None:
    """The bundle contains a manifest and the expected shareable artifacts."""
    bundle_dir = demo_bundle.bundle_dir
    manifest = demo_bundle.manifest

    assert bundle_dir.exists()
    assert manifest["tool"] == "martenweave"
    assert manifest["generated_at"] == "2024-01-15T09:00:00Z"
    assert manifest["fixture_version"]
    assert manifest["generation_command"]
    assert manifest["boundary_notes"]

    manifest_path = bundle_dir / "bundle-manifest.json"
    assert manifest_path.exists()
    written = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert written["repo_name"]
    assert written["artifact_count"] > 0
    assert len(written["artifacts"]) == written["artifact_count"]
    assert all("sha256" in a for a in written["artifacts"])

    required_files = {
        "executive-summary.md",
        "executive-summary.json",
        "finding-review-summary.json",
        "pilot-outcome.md",
        "pilot-outcome.json",
        "sanitization-manifest.json",
    }
    found_files = {a["path"] for a in written["artifacts"]}
    assert required_files <= found_files, f"Missing required files: {required_files - found_files}"


@pytest.mark.skipif(not MAPPING_WORKBOOK.exists(), reason="pilot fixture missing")
def test_demo_bundle_excludes_raw_datasets_and_binary_files(demo_bundle) -> None:
    """Raw datasets and unsupported binaries are not copied into the bundle."""
    bundle_dir = demo_bundle.bundle_dir
    manifest = demo_bundle.manifest

    assert not any("dataset_readiness" in a["path"] for a in manifest["artifacts"])
    assert not any(
        Path(a["path"]).suffix not in {".md", ".json", ".xlsx"} for a in manifest["artifacts"]
    )

    for path in bundle_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() not in {".md", ".json", ".xlsx"}:
            raise AssertionError(f"Unexpected file type in bundle: {path.relative_to(bundle_dir)}")


@pytest.mark.skipif(not MAPPING_WORKBOOK.exists(), reason="pilot fixture missing")
def test_demo_bundle_is_deterministic(sample_repo: Path, tmp_path: Path) -> None:
    """Two builds with the same generated_at produce identical artifact checksums."""
    from modelops_core.pilot.demo_bundle import build_demo_bundle

    def checksums(bundle):
        return {a["path"]: a["sha256"] for a in bundle.manifest["artifacts"]}

    bundle_a = build_demo_bundle(
        out_dir=tmp_path / "bundle-a",
        repo_root=sample_repo,
        mapping_path=MAPPING_WORKBOOK,
        generated_at="2024-01-15T09:00:00Z",
    )
    bundle_b = build_demo_bundle(
        out_dir=tmp_path / "bundle-b",
        repo_root=sample_repo,
        mapping_path=MAPPING_WORKBOOK,
        generated_at="2024-01-15T09:00:00Z",
    )

    assert checksums(bundle_a) == checksums(bundle_b)


@pytest.mark.skipif(not MAPPING_WORKBOOK.exists(), reason="pilot fixture missing")
def test_validate_demo_bundle_detects_tampering(demo_bundle) -> None:
    """Bundle validation reports mismatched checksums after an artifact is altered."""
    from modelops_core.pilot.demo_bundle import validate_demo_bundle

    bundle_dir = demo_bundle.bundle_dir
    errors_before = validate_demo_bundle(bundle_dir)
    assert errors_before == []

    # Tamper with a text artifact.
    md_files = list(bundle_dir.rglob("*.md"))
    assert md_files
    target = md_files[0]
    target.write_text(target.read_text(encoding="utf-8") + "\n<!-- tamper -->", encoding="utf-8")

    errors_after = validate_demo_bundle(bundle_dir)
    assert any("checksum" in e.lower() for e in errors_after)


@pytest.mark.skipif(not MAPPING_WORKBOOK.exists(), reason="pilot fixture missing")
def test_demo_bundle_cli_build(sample_repo: Path, tmp_path: Path) -> None:
    """The ``demo-bundle build`` CLI command produces a valid bundle."""
    out_dir = tmp_path / "cli-bundle"
    result = runner.invoke(
        app,
        [
            "demo-bundle",
            "build",
            "--repo",
            str(sample_repo),
            "--mapping",
            str(MAPPING_WORKBOOK),
            "--out",
            str(out_dir),
        ],
    )
    assert result.exit_code == 0, result.output
    assert (out_dir / "bundle-manifest.json").exists()
