"""Shared test fixtures."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from modelops_core.index.sqlite_builder import build_index


@pytest.fixture
def sample_repo(tmp_path: Path) -> Path:
    """Copy the example customer-bp model into a temporary directory."""
    src = Path(__file__).resolve().parent.parent / "examples" / "customer_bp_model"
    dst = tmp_path / "customer_bp_model"
    shutil.copytree(src, dst)
    # Build the SQLite index so tests that require it don't fail in CI.
    build_index(dst, allow_invalid=True)
    return dst


@pytest.fixture
def temp_model_dir(tmp_path: Path) -> Path:
    """Create a temporary model directory with a few canonical objects."""
    model_dir = tmp_path / "model"
    model_dir.mkdir()

    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\nname: Test Domain\n---\n",
        encoding="utf-8",
    )

    (model_dir / "ATTR-TEST.md").write_text(
        "---\n"
        "id: ATTR-TEST\n"
        "type: Attribute\n"
        "status: draft\n"
        "name: Test Attribute\n"
        "domain: DOMAIN-TEST\n"
        "---\n",
        encoding="utf-8",
    )

    return model_dir
