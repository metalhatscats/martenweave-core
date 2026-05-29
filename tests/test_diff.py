"""Tests for model diff service and CLI."""

from __future__ import annotations

from pathlib import Path

from modelops_core.diff.diff_service import (
    _compare_values,
    _diff_object,
    diff_repositories,
)

# ---------------------------------------------------------------------------
# _compare_values
# ---------------------------------------------------------------------------


class TestCompareValues:
    def test_primitives_equal(self) -> None:
        assert _compare_values("a", "a") is True
        assert _compare_values(1, 1) is True

    def test_primitives_different(self) -> None:
        assert _compare_values("a", "b") is False
        assert _compare_values(1, 2) is False

    def test_dicts_equal(self) -> None:
        assert _compare_values({"a": 1}, {"a": 1}) is True

    def test_dicts_different_keys(self) -> None:
        assert _compare_values({"a": 1}, {"b": 1}) is False

    def test_dicts_different_values(self) -> None:
        assert _compare_values({"a": 1}, {"a": 2}) is False

    def test_lists_equal(self) -> None:
        assert _compare_values([1, 2], [1, 2]) is True

    def test_lists_different_length(self) -> None:
        assert _compare_values([1], [1, 2]) is False

    def test_lists_different_items(self) -> None:
        assert _compare_values([1, 2], [1, 3]) is False

    def test_type_mismatch(self) -> None:
        assert _compare_values("1", 1) is False


# ---------------------------------------------------------------------------
# _diff_object
# ---------------------------------------------------------------------------


class TestDiffObject:
    def test_no_changes(self) -> None:
        base = {"id": "TEST", "type": "Attribute", "status": "draft"}
        head = {"id": "TEST", "type": "Attribute", "status": "draft"}
        assert _diff_object(base, head) == []

    def test_added_field(self) -> None:
        base = {"id": "TEST", "type": "Attribute"}
        head = {"id": "TEST", "type": "Attribute", "name": "New Name"}
        changes = _diff_object(base, head)
        assert len(changes) == 1
        assert changes[0].field == "name"
        assert changes[0].old_value is None
        assert changes[0].new_value == "New Name"

    def test_removed_field(self) -> None:
        base = {"id": "TEST", "type": "Attribute", "name": "Old Name"}
        head = {"id": "TEST", "type": "Attribute"}
        changes = _diff_object(base, head)
        assert len(changes) == 1
        assert changes[0].field == "name"
        assert changes[0].old_value == "Old Name"
        assert changes[0].new_value is None

    def test_changed_field(self) -> None:
        base = {"id": "TEST", "type": "Attribute", "status": "draft"}
        head = {"id": "TEST", "type": "Attribute", "status": "active"}
        changes = _diff_object(base, head)
        assert len(changes) == 1
        assert changes[0].field == "status"
        assert changes[0].old_value == "draft"
        assert changes[0].new_value == "active"

    def test_ignores_schema_version(self) -> None:
        base = {"id": "TEST", "schema_version": "0.9"}
        head = {"id": "TEST", "schema_version": "1.0"}
        assert _diff_object(base, head) == []


# ---------------------------------------------------------------------------
# diff_repositories
# ---------------------------------------------------------------------------


class TestDiffRepositories:
    def test_empty_repos(self, tmp_path: Path) -> None:
        base = tmp_path / "base" / "model"
        head = tmp_path / "head" / "model"
        base.mkdir(parents=True)
        head.mkdir(parents=True)
        result = diff_repositories(base, head)
        assert result.base_count == 0
        assert result.head_count == 0
        assert not result.has_changes

    def test_added_object(self, tmp_path: Path) -> None:
        base = tmp_path / "base" / "model"
        head = tmp_path / "head" / "model"
        base.mkdir(parents=True)
        head.mkdir(parents=True)

        (head / "OBJ-001.md").write_text(
            "---\nid: OBJ-001\ntype: Attribute\nstatus: draft\nname: New\n---\n",
            encoding="utf-8",
        )

        result = diff_repositories(base, head)
        assert len(result.added) == 1
        assert result.added[0]["object_id"] == "OBJ-001"
        assert result.has_changes

    def test_removed_object(self, tmp_path: Path) -> None:
        base = tmp_path / "base" / "model"
        head = tmp_path / "head" / "model"
        base.mkdir(parents=True)
        head.mkdir(parents=True)

        (base / "OBJ-001.md").write_text(
            "---\nid: OBJ-001\ntype: Attribute\nstatus: draft\nname: Old\n---\n",
            encoding="utf-8",
        )

        result = diff_repositories(base, head)
        assert len(result.removed) == 1
        assert result.removed[0]["object_id"] == "OBJ-001"
        assert result.has_changes

    def test_changed_object(self, tmp_path: Path) -> None:
        base = tmp_path / "base" / "model"
        head = tmp_path / "head" / "model"
        base.mkdir(parents=True)
        head.mkdir(parents=True)

        (base / "OBJ-001.md").write_text(
            "---\nid: OBJ-001\ntype: Attribute\nstatus: draft\nname: Old\n---\n",
            encoding="utf-8",
        )
        (head / "OBJ-001.md").write_text(
            "---\nid: OBJ-001\ntype: Attribute\nstatus: active\nname: New\n---\n",
            encoding="utf-8",
        )

        result = diff_repositories(base, head)
        assert len(result.changed) == 1
        changed = result.changed[0]
        assert changed.object_id == "OBJ-001"
        assert any(fc.field == "status" for fc in changed.field_changes)
        assert any(fc.field == "name" for fc in changed.field_changes)
        assert result.has_changes

    def test_no_changes(self, tmp_path: Path) -> None:
        base = tmp_path / "base" / "model"
        head = tmp_path / "head" / "model"
        base.mkdir(parents=True)
        head.mkdir(parents=True)

        content = "---\nid: OBJ-001\ntype: Attribute\nstatus: draft\n---\n"
        (base / "OBJ-001.md").write_text(content, encoding="utf-8")
        (head / "OBJ-001.md").write_text(content, encoding="utf-8")

        result = diff_repositories(base, head)
        assert not result.has_changes
        assert result.added == []
        assert result.removed == []
        assert result.changed == []

    def test_changed_relationship(self, tmp_path: Path) -> None:
        base = tmp_path / "base" / "model"
        head = tmp_path / "head" / "model"
        base.mkdir(parents=True)
        head.mkdir(parents=True)

        (base / "OBJ-001.md").write_text(
            "---\nid: OBJ-001\ntype: Attribute\ndomain: DOMAIN-A\n---\n",
            encoding="utf-8",
        )
        (head / "OBJ-001.md").write_text(
            "---\nid: OBJ-001\ntype: Attribute\ndomain: DOMAIN-B\n---\n",
            encoding="utf-8",
        )

        result = diff_repositories(base, head)
        assert len(result.changed) == 1
        assert any(
            fc.field == "domain" and fc.old_value == "DOMAIN-A" and fc.new_value == "DOMAIN-B"
            for fc in result.changed[0].field_changes
        )

    def test_changed_lov_entries(self, tmp_path: Path) -> None:
        base = tmp_path / "base" / "model"
        head = tmp_path / "head" / "model"
        base.mkdir(parents=True)
        head.mkdir(parents=True)

        (base / "VLIST-001.md").write_text(
            "---\nid: VLIST-001\ntype: ValueList\nentries:\n  - code: A\n---\n",
            encoding="utf-8",
        )
        (head / "VLIST-001.md").write_text(
            "---\nid: VLIST-001\ntype: ValueList\nentries:\n  - code: A\n  - code: B\n---\n",
            encoding="utf-8",
        )

        result = diff_repositories(base, head)
        assert len(result.changed) == 1
        assert any(fc.field == "entries" for fc in result.changed[0].field_changes)
