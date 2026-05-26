"""Tests for ownership and steward workload report (#233)."""

from __future__ import annotations

from pathlib import Path

from modelops_core.index.sqlite_builder import build_index
from modelops_core.reports.ownership_report import (
    OwnershipReport,
    generate_ownership_report,
)


class TestOwnershipReportOnExample:
    def test_ownership_report_has_owners(self, sample_repo: Path) -> None:
        repo_root = sample_repo
        db_path = repo_root / "generated" / "modelops.db"
        report = generate_ownership_report(db_path, repo_root)
        assert isinstance(report, OwnershipReport)
        assert report.total_eligible >= 0

    def test_ownership_report_json_serializable(self, sample_repo: Path) -> None:
        import json

        repo_root = sample_repo
        db_path = repo_root / "generated" / "modelops.db"
        report = generate_ownership_report(db_path, repo_root)
        data = {
            "owners": [
                {
                    "owner_id": o.owner_id,
                    "role": o.role,
                    "object_count": o.object_count,
                    "object_types": o.object_types,
                }
                for o in report.owners
            ],
            "orphaned_objects": [
                {
                    "object_id": o.object_id,
                    "object_type": o.object_type,
                    "object_name": o.object_name,
                }
                for o in report.orphaned_objects
            ],
            "coverage_percent": report.coverage_percent,
            "total_eligible": report.total_eligible,
            "total_with_owner": report.total_with_owner,
        }
        text = json.dumps(data, indent=2, default=str)
        assert "coverage_percent" in text


class TestOwnershipReportEmpty:
    def test_empty_repo(self, tmp_path: Path) -> None:
        model_dir = tmp_path / "model"
        model_dir.mkdir()
        generated_dir = tmp_path / "generated"
        generated_dir.mkdir()
        (tmp_path / "modelops.config.yaml").write_text(
            "model_dir: model\ngenerated_dir: generated\n", encoding="utf-8"
        )
        build_index(
            repo_root=tmp_path,
            db_path=generated_dir / "modelops.db",
            allow_invalid=True,
        )
        report = generate_ownership_report(generated_dir / "modelops.db", tmp_path)
        assert report.owners == []
        assert report.orphaned_objects == []
        assert report.coverage_percent == 0.0
        assert report.total_eligible == 0
        assert report.total_with_owner == 0


class TestOwnershipReportOwners:
    def test_single_owner_single_object(self, tmp_path: Path) -> None:
        model_dir = tmp_path / "model"
        model_dir.mkdir()
        generated_dir = tmp_path / "generated"
        generated_dir.mkdir()
        (model_dir / "ATTR-001.md").write_text(
            "---\nid: ATTR-001\ntype: Attribute\nstatus: active\n"
            "name: Test Attribute\nbusiness_owner: alice\nschema_version: '1.0'\n---\n",
            encoding="utf-8",
        )
        (tmp_path / "modelops.config.yaml").write_text(
            "model_dir: model\ngenerated_dir: generated\n", encoding="utf-8"
        )
        build_index(
            repo_root=tmp_path,
            db_path=generated_dir / "modelops.db",
            allow_invalid=True,
        )
        report = generate_ownership_report(generated_dir / "modelops.db", tmp_path)
        assert len(report.owners) == 1
        assert report.owners[0].owner_id == "alice"
        assert report.owners[0].role == "business_owner"
        assert report.owners[0].object_count == 1
        assert report.owners[0].object_types == {"Attribute": 1}
        assert report.coverage_percent == 100.0
        assert report.total_eligible == 1
        assert report.total_with_owner == 1
        assert report.orphaned_objects == []

    def test_multiple_roles_same_owner(self, tmp_path: Path) -> None:
        model_dir = tmp_path / "model"
        model_dir.mkdir()
        generated_dir = tmp_path / "generated"
        generated_dir.mkdir()
        (model_dir / "ATTR-001.md").write_text(
            "---\nid: ATTR-001\ntype: Attribute\nstatus: active\n"
            "name: Test Attribute\nbusiness_owner: alice\n"
            "technical_owner: alice\nschema_version: '1.0'\n---\n",
            encoding="utf-8",
        )
        (tmp_path / "modelops.config.yaml").write_text(
            "model_dir: model\ngenerated_dir: generated\n", encoding="utf-8"
        )
        build_index(
            repo_root=tmp_path,
            db_path=generated_dir / "modelops.db",
            allow_invalid=True,
        )
        report = generate_ownership_report(generated_dir / "modelops.db", tmp_path)
        assert len(report.owners) == 2
        roles = {o.role for o in report.owners}
        assert roles == {"business_owner", "technical_owner"}
        for o in report.owners:
            assert o.owner_id == "alice"
            assert o.object_count == 1

    def test_owner_list_value(self, tmp_path: Path) -> None:
        model_dir = tmp_path / "model"
        model_dir.mkdir()
        generated_dir = tmp_path / "generated"
        generated_dir.mkdir()
        (model_dir / "ATTR-001.md").write_text(
            "---\nid: ATTR-001\ntype: Attribute\nstatus: active\n"
            "name: Test Attribute\nbusiness_owner:\n  - alice\n  - bob\n"
            "schema_version: '1.0'\n---\n",
            encoding="utf-8",
        )
        (tmp_path / "modelops.config.yaml").write_text(
            "model_dir: model\ngenerated_dir: generated\n", encoding="utf-8"
        )
        build_index(
            repo_root=tmp_path,
            db_path=generated_dir / "modelops.db",
            allow_invalid=True,
        )
        report = generate_ownership_report(generated_dir / "modelops.db", tmp_path)
        assert len(report.owners) == 2
        owner_ids = {o.owner_id for o in report.owners}
        assert owner_ids == {"alice", "bob"}

    def test_sorted_by_object_count_descending(self, tmp_path: Path) -> None:
        model_dir = tmp_path / "model"
        model_dir.mkdir()
        generated_dir = tmp_path / "generated"
        generated_dir.mkdir()
        (model_dir / "ATTR-001.md").write_text(
            "---\nid: ATTR-001\ntype: Attribute\nstatus: active\n"
            "name: A1\nbusiness_owner: alice\nschema_version: '1.0'\n---\n",
            encoding="utf-8",
        )
        (model_dir / "ATTR-002.md").write_text(
            "---\nid: ATTR-002\ntype: Attribute\nstatus: active\n"
            "name: A2\nbusiness_owner: alice\nschema_version: '1.0'\n---\n",
            encoding="utf-8",
        )
        (model_dir / "ATTR-003.md").write_text(
            "---\nid: ATTR-003\ntype: Attribute\nstatus: active\n"
            "name: A3\nbusiness_owner: bob\nschema_version: '1.0'\n---\n",
            encoding="utf-8",
        )
        (tmp_path / "modelops.config.yaml").write_text(
            "model_dir: model\ngenerated_dir: generated\n", encoding="utf-8"
        )
        build_index(
            repo_root=tmp_path,
            db_path=generated_dir / "modelops.db",
            allow_invalid=True,
        )
        report = generate_ownership_report(generated_dir / "modelops.db", tmp_path)
        assert [o.owner_id for o in report.owners] == ["alice", "bob"]
        assert report.owners[0].object_count == 2
        assert report.owners[1].object_count == 1


class TestOwnershipReportOrphaned:
    def test_orphaned_object_reported(self, tmp_path: Path) -> None:
        model_dir = tmp_path / "model"
        model_dir.mkdir()
        generated_dir = tmp_path / "generated"
        generated_dir.mkdir()
        (model_dir / "ATTR-001.md").write_text(
            "---\nid: ATTR-001\ntype: Attribute\nstatus: active\n"
            "name: Test Attribute\nschema_version: '1.0'\n---\n",
            encoding="utf-8",
        )
        (tmp_path / "modelops.config.yaml").write_text(
            "model_dir: model\ngenerated_dir: generated\n", encoding="utf-8"
        )
        build_index(
            repo_root=tmp_path,
            db_path=generated_dir / "modelops.db",
            allow_invalid=True,
        )
        report = generate_ownership_report(generated_dir / "modelops.db", tmp_path)
        assert len(report.orphaned_objects) == 1
        assert report.orphaned_objects[0].object_id == "ATTR-001"
        assert report.orphaned_objects[0].object_type == "Attribute"
        assert report.orphaned_objects[0].object_name == "Test Attribute"
        assert report.coverage_percent == 0.0
        assert report.total_eligible == 1
        assert report.total_with_owner == 0

    def test_inactive_objects_ignored(self, tmp_path: Path) -> None:
        model_dir = tmp_path / "model"
        model_dir.mkdir()
        generated_dir = tmp_path / "generated"
        generated_dir.mkdir()
        (model_dir / "ATTR-001.md").write_text(
            "---\nid: ATTR-001\ntype: Attribute\nstatus: retired\n"
            "name: Test Attribute\nschema_version: '1.0'\n---\n",
            encoding="utf-8",
        )
        (tmp_path / "modelops.config.yaml").write_text(
            "model_dir: model\ngenerated_dir: generated\n", encoding="utf-8"
        )
        build_index(
            repo_root=tmp_path,
            db_path=generated_dir / "modelops.db",
            allow_invalid=True,
        )
        report = generate_ownership_report(generated_dir / "modelops.db", tmp_path)
        assert report.owners == []
        assert report.orphaned_objects == []
        assert report.total_eligible == 0

    def test_non_ownership_type_ignored(self, tmp_path: Path) -> None:
        model_dir = tmp_path / "model"
        model_dir.mkdir()
        generated_dir = tmp_path / "generated"
        generated_dir.mkdir()
        (model_dir / "DOMAIN-001.md").write_text(
            "---\nid: DOMAIN-001\ntype: MasterDataDomain\nstatus: active\n"
            "name: Test Domain\nschema_version: '1.0'\n---\n",
            encoding="utf-8",
        )
        (tmp_path / "modelops.config.yaml").write_text(
            "model_dir: model\ngenerated_dir: generated\n", encoding="utf-8"
        )
        build_index(
            repo_root=tmp_path,
            db_path=generated_dir / "modelops.db",
            allow_invalid=True,
        )
        report = generate_ownership_report(generated_dir / "modelops.db", tmp_path)
        assert report.owners == []
        assert report.orphaned_objects == []
        assert report.total_eligible == 0

    def test_mixed_ownership_and_orphaned(self, tmp_path: Path) -> None:
        model_dir = tmp_path / "model"
        model_dir.mkdir()
        generated_dir = tmp_path / "generated"
        generated_dir.mkdir()
        (model_dir / "ATTR-001.md").write_text(
            "---\nid: ATTR-001\ntype: Attribute\nstatus: active\n"
            "name: Owned Attribute\nbusiness_owner: alice\n"
            "schema_version: '1.0'\n---\n",
            encoding="utf-8",
        )
        (model_dir / "ATTR-002.md").write_text(
            "---\nid: ATTR-002\ntype: Attribute\nstatus: active\n"
            "name: Orphaned Attribute\nschema_version: '1.0'\n---\n",
            encoding="utf-8",
        )
        (tmp_path / "modelops.config.yaml").write_text(
            "model_dir: model\ngenerated_dir: generated\n", encoding="utf-8"
        )
        build_index(
            repo_root=tmp_path,
            db_path=generated_dir / "modelops.db",
            allow_invalid=True,
        )
        report = generate_ownership_report(generated_dir / "modelops.db", tmp_path)
        assert len(report.owners) == 1
        assert report.owners[0].object_count == 1
        assert len(report.orphaned_objects) == 1
        assert report.orphaned_objects[0].object_id == "ATTR-002"
        assert report.coverage_percent == 50.0
        assert report.total_eligible == 2
        assert report.total_with_owner == 1
