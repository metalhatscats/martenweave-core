"""Tests for AI context builder service."""

from __future__ import annotations

from pathlib import Path

from modelops_core.ai.context_builder import build_context_bundle
from modelops_core.index import build_index


def _build_repo(tmp_path: Path, objects: list[dict]) -> Path:
    model_dir = tmp_path / "model"
    model_dir.mkdir(parents=True, exist_ok=True)
    generated_dir = tmp_path / "generated"
    generated_dir.mkdir(parents=True, exist_ok=True)

    for obj in objects:
        obj_id = obj["id"]
        frontmatter_lines = []
        for k, v in obj.items():
            if isinstance(v, list):
                frontmatter_lines.append(f"{k}:")
                for item in v:
                    frontmatter_lines.append(f"  - {item}")
            else:
                frontmatter_lines.append(f"{k}: {v}")
        frontmatter = "\n".join(frontmatter_lines)
        content = f"---\n{frontmatter}\n---\n\n# {obj_id}\n"
        (model_dir / f"{obj_id}.md").write_text(content, encoding="utf-8")

    db_path = generated_dir / "modelops.db"
    build_index(repo_root=tmp_path, db_path=db_path, allow_invalid=True)
    return db_path


def test_bundle_for_exact_lookup(tmp_path: Path) -> None:
    db_path = _build_repo(
        tmp_path,
        [
            {"id": "ATTR-1", "type": "Attribute", "status": "active", "name": "A1"},
        ],
    )
    bundle = build_context_bundle(
        db_path=db_path,
        workflow="chat-to-model",
        target_object_id="ATTR-1",
    )
    assert bundle.workflow == "chat-to-model"
    assert len(bundle.included_objects) == 1
    assert bundle.included_objects[0]["object_id"] == "ATTR-1"
    assert bundle.bundle_id


def test_bundle_with_relationship_expansion(tmp_path: Path) -> None:
    db_path = _build_repo(
        tmp_path,
        [
            {"id": "ATTR-1", "type": "Attribute", "status": "active", "name": "A1"},
            {
                "id": "USE-1",
                "type": "AttributeUsage",
                "status": "active",
                "attribute": "ATTR-1",
            },
            {"id": "FEP-1", "type": "FieldEndpoint", "status": "active", "name": "F1"},
        ],
    )
    bundle = build_context_bundle(
        db_path=db_path,
        workflow="trace-explanation",
        target_object_id="ATTR-1",
        max_depth=2,
    )
    ids = {o["object_id"] for o in bundle.included_objects}
    assert "ATTR-1" in ids
    assert "USE-1" in ids
    assert len(bundle.relationship_refs) > 0


def test_bundle_structured_query(tmp_path: Path) -> None:
    db_path = _build_repo(
        tmp_path,
        [
            {"id": "ATTR-1", "type": "Attribute", "status": "active", "name": "A1"},
            {"id": "ATTR-2", "type": "Attribute", "status": "active", "name": "A2"},
            {"id": "FEP-1", "type": "FieldEndpoint", "status": "active", "name": "F1"},
        ],
    )
    bundle = build_context_bundle(
        db_path=db_path,
        workflow="metadata-gap-suggestion",
        extra_query={"type": "Attribute", "status": "active"},
    )
    ids = {o["object_id"] for o in bundle.included_objects}
    assert "ATTR-1" in ids
    assert "ATTR-2" in ids


def test_bundle_compaction_on_large_set(tmp_path: Path) -> None:
    objects = [
        {"id": f"ATTR-{i:03d}", "type": "Attribute", "status": "active", "name": f"A{i}"}
        for i in range(60)
    ]
    db_path = _build_repo(tmp_path, objects)
    bundle = build_context_bundle(
        db_path=db_path,
        workflow="chat-to-model",
        extra_query={"type": "Attribute"},
        max_objects=20,
    )
    assert len(bundle.included_objects) <= 20
    assert any("Excluded" in w for w in bundle.warnings)


def test_bundle_missing_db() -> None:
    bundle = build_context_bundle(
        db_path=Path("/nonexistent/db.sqlite"),
        workflow="chat-to-model",
        target_object_id="X",
    )
    assert len(bundle.included_objects) == 0
    assert any("not found" in w for w in bundle.warnings)


def test_bundle_metadata(tmp_path: Path) -> None:
    db_path = _build_repo(
        tmp_path,
        [
            {"id": "DOMAIN-1", "type": "MasterDataDomain", "status": "active", "name": "D1"},
        ],
    )
    bundle = build_context_bundle(
        db_path=db_path,
        workflow="impact-explanation",
        target_object_id="DOMAIN-1",
    )
    meta = bundle.to_metadata()
    assert meta["workflow"] == "impact-explanation"
    assert meta["object_count"] == 1
    assert "bundle_id" in meta
    assert "created_at" in meta


def test_bundle_redaction_policy(tmp_path: Path) -> None:
    db_path = _build_repo(
        tmp_path,
        [
            {"id": "ATTR-1", "type": "Attribute", "status": "active", "name": "A1"},
        ],
    )
    bundle = build_context_bundle(
        db_path=db_path,
        workflow="chat-to-model",
        target_object_id="ATTR-1",
        redaction_policy="summary_only",
    )
    assert bundle.redaction_policy == "summary_only"
    assert bundle.included_sources == []


def test_bundle_estimate_size(tmp_path: Path) -> None:
    db_path = _build_repo(
        tmp_path,
        [
            {"id": "ATTR-1", "type": "Attribute", "status": "active", "name": "A1"},
        ],
    )
    bundle = build_context_bundle(
        db_path=db_path,
        workflow="chat-to-model",
        target_object_id="ATTR-1",
    )
    size = bundle.estimate_size()
    assert size > 0
