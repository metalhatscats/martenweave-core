"""Tests for synthetic fixture generator."""

from __future__ import annotations

from pathlib import Path

from modelops_core.fixtures.fixture_generator import (
    FixtureProfile,
    generate_fixture_repo,
)
from modelops_core.index import build_index


def test_generate_small_fixture(tmp_path: Path) -> None:
    result = generate_fixture_repo(tmp_path, profile="small")
    assert result["profile"] == "small"
    assert result["counts"]["domain"] == 1
    assert result["counts"]["attribute"] == 5
    assert result["counts"]["field_endpoint"] == 5
    assert result["counts"]["mapping"] == 5
    assert result["with_gaps"] is True
    assert (tmp_path / "modelops.config.yaml").exists()


def test_generate_medium_fixture(tmp_path: Path) -> None:
    result = generate_fixture_repo(tmp_path, profile="medium")
    assert result["profile"] == "medium"
    assert result["counts"]["domain"] == 2
    assert result["counts"]["attribute"] == 20
    assert result["counts"]["mapping"] == 15


def test_generate_large_fixture_no_gaps(tmp_path: Path) -> None:
    result = generate_fixture_repo(tmp_path, profile="large")
    assert result["profile"] == "large"
    assert result["counts"]["attribute"] == 50
    assert result["with_gaps"] is False


def test_generate_custom_profile(tmp_path: Path) -> None:
    profile = FixtureProfile(
        name="custom",
        domain_count=1,
        attribute_count=3,
        field_endpoint_count=3,
        mapping_count=2,
        value_list_count=1,
        validation_rule_count=1,
        issue_count=0,
        with_gaps=False,
    )
    result = generate_fixture_repo(tmp_path, profile=profile)
    assert result["counts"]["attribute"] == 3
    assert result["counts"]["issue"] == 0


def test_fixture_files_are_written(tmp_path: Path) -> None:
    generate_fixture_repo(tmp_path, profile="small")
    model_dir = tmp_path / "model"
    assert (model_dir / "DOMAIN-001.md").exists()
    assert (model_dir / "ATTR-001.md").exists()
    assert (model_dir / "FEP-001.md").exists()
    assert (model_dir / "MAP-001.md").exists()
    assert (model_dir / "VLIST-001.md").exists()
    assert (model_dir / "RULE-001.md").exists()
    assert (model_dir / "ISS-001.md").exists()


def test_fixture_builds_index(tmp_path: Path) -> None:
    generate_fixture_repo(tmp_path, profile="small")
    db_path = tmp_path / "generated" / "modelops.db"
    build_index(repo_root=tmp_path, db_path=db_path, allow_invalid=True)
    assert db_path.exists()


def test_fixture_no_real_data(tmp_path: Path) -> None:
    generate_fixture_repo(tmp_path, profile="small")
    model_dir = tmp_path / "model"
    for path in model_dir.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        assert "real customer" not in text.lower()
        assert "password" not in text.lower()
        assert "ssn" not in text.lower()
