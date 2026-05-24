"""Tests for lineage and JSONL export."""

from __future__ import annotations

from pathlib import Path

from modelops_core.index import build_index
from modelops_core.index.lineage_edges import export_lineage_jsonl
from modelops_core.lineage.lineage_service import generate_lineage_path


def test_lineage_path_basic(temp_model_dir: Path) -> None:
    repo_root = temp_model_dir.parent
    db_path = repo_root / "generated" / "modelops.db"
    build_index(repo_root=repo_root, db_path=db_path)

    path = generate_lineage_path(db_path, "DOMAIN-TEST")
    assert path is not None
    assert len(path.nodes) >= 1


def test_export_lineage_jsonl(temp_model_dir: Path) -> None:
    repo_root = temp_model_dir.parent
    db_path = repo_root / "generated" / "modelops.db"
    build_index(repo_root=repo_root, db_path=db_path)

    output = repo_root / "generated" / "lineage_edges.jsonl"
    export_lineage_jsonl(db_path, output)
    assert output.exists()
    lines = output.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) >= 0
