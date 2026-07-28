from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from modelops_core.cli import app
from modelops_core.package_service import create_package, inspect_package, verify_package


def test_package_is_deterministic_and_excludes_operational_content(
    sample_repo: Path, tmp_path: Path
) -> None:
    (sample_repo / "data" / "private.csv").write_text("secret\n", encoding="utf-8")
    (sample_repo / "generated" / "patch-transactions").mkdir(parents=True, exist_ok=True)
    (sample_repo / "generated" / "patch-transactions" / "receipt.json").write_text(
        "{}", encoding="utf-8"
    )
    first, second = tmp_path / "first.mwpkg", tmp_path / "second.mwpkg"

    first_manifest = create_package(sample_repo, first)
    second_manifest = create_package(sample_repo, second)

    assert first.read_bytes() == second.read_bytes()
    assert first_manifest == second_manifest
    assert verify_package(first)["valid"] is True
    with zipfile.ZipFile(first) as archive:
        names = archive.namelist()
    assert all(not name.startswith(("data/", "generated/")) for name in names)
    assert all("patch-transactions" not in name for name in names)


def test_package_detects_tampering_and_unsafe_paths(sample_repo: Path, tmp_path: Path) -> None:
    package = tmp_path / "source.mwpkg"
    create_package(sample_repo, package)
    tampered = tmp_path / "tampered.mwpkg"
    with zipfile.ZipFile(package) as source, zipfile.ZipFile(tampered, "w") as target:
        for info in source.infolist():
            content = source.read(info.filename)
            if info.filename.startswith("model/"):
                content += b"tampered"
            target.writestr(info, content)
    with pytest.raises(ValueError, match="checksum mismatch"):
        verify_package(tampered)

    unsafe = tmp_path / "unsafe.mwpkg"
    with zipfile.ZipFile(unsafe, "w") as archive:
        archive.writestr("../escape", "no")
        archive.writestr("manifest.json", json.dumps({}))
        archive.writestr("integrity.json", json.dumps({}))
    with pytest.raises(ValueError, match="Unsafe archive"):
        inspect_package(unsafe)


def test_package_cli_rejects_invalid_repository_and_reports_metadata(
    temp_model_dir: Path, tmp_path: Path
) -> None:
    runner = CliRunner()
    output = tmp_path / "model.mwpkg"
    created = runner.invoke(
        app, ["package", "create", "--repo", str(temp_model_dir), "--output", str(output)]
    )
    assert created.exit_code == 0, created.output
    inspected = runner.invoke(app, ["package", "inspect", str(output), "--json"])
    assert inspected.exit_code == 0, inspected.output
    assert json.loads(inspected.stdout)["package_format_version"] == "1.0"
    verified = runner.invoke(app, ["package", "verify", str(output)])
    assert verified.exit_code == 0, verified.output

    invalid = tmp_path / "invalid"
    invalid.mkdir()
    (invalid / "model").mkdir()
    (invalid / "model" / "broken.md").write_text("---\nid: invalid\n---\n", encoding="utf-8")
    rejected = runner.invoke(
        app,
        ["package", "create", "--repo", str(invalid), "--output", str(tmp_path / "bad.mwpkg")],
    )
    assert rejected.exit_code == 1
    assert "Cannot package invalid repository" in rejected.stdout
