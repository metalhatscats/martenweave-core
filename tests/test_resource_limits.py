"""Tests for runtime resource limits and graceful failure behavior (#94)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from modelops_core.config import ResourceLimits, load_repo_config
from modelops_core.errors import ResourceLimitExceeded
from modelops_core.exports import export_model_csv, export_model_xlsx
from modelops_core.fixtures.fixture_generator import generate_fixture_repo
from modelops_core.imports.model_sheet_import_service import import_model_sheet_xlsx
from modelops_core.index.sqlite_builder import build_index


class TestResourceLimitsDefaults:
    def test_default_limits(self) -> None:
        limits = ResourceLimits()
        assert limits.max_file_size_bytes == 50 * 1024 * 1024
        assert limits.max_profile_rows == 500_000
        assert limits.max_profile_columns == 1_000
        assert limits.max_trace_depth == 5
        assert limits.max_index_objects == 10_000
        assert limits.max_export_objects == 10_000
        assert limits.max_import_rows == 100_000
        assert limits.max_context_objects == 50
        assert limits.max_context_relationships == 100
        assert limits.max_response_size_bytes == 10 * 1024 * 1024

    def test_custom_limits(self) -> None:
        limits = ResourceLimits(max_index_objects=5, max_trace_depth=2)
        assert limits.max_index_objects == 5
        assert limits.max_trace_depth == 2
        # Unchanged defaults
        assert limits.max_profile_rows == 500_000


class TestRepoConfigWithResourceLimits:
    def test_load_repo_config_with_limits(self, tmp_path: Path) -> None:
        config_path = tmp_path / "modelops.config.yaml"
        config_path.write_text(
            yaml.safe_dump(
                {
                    "name": "Test Repo",
                    "resource_limits": {"max_index_objects": 42, "max_trace_depth": 3},
                }
            ),
            encoding="utf-8",
        )
        config = load_repo_config(tmp_path)
        assert config is not None
        assert config.resource_limits.max_index_objects == 42
        assert config.resource_limits.max_trace_depth == 3
        assert config.resource_limits.max_profile_rows == 500_000

    def test_load_repo_config_without_limits_uses_defaults(self, tmp_path: Path) -> None:
        config_path = tmp_path / "modelops.config.yaml"
        config_path.write_text(
            yaml.safe_dump({"name": "Test Repo"}),
            encoding="utf-8",
        )
        config = load_repo_config(tmp_path)
        assert config is not None
        assert config.resource_limits.max_index_objects == 10_000


class TestBuildIndexLimit:
    def test_build_index_exceeds_max_objects(self, tmp_path: Path) -> None:
        generate_fixture_repo(tmp_path, profile="small")
        with pytest.raises(ResourceLimitExceeded) as exc_info:
            build_index(tmp_path, max_objects=1, allow_invalid=True)
        assert exc_info.value.resource == "max_index_objects"
        assert "exceeding max_index_objects limit" in exc_info.value.message

    def test_build_index_respects_high_limit(self, tmp_path: Path) -> None:
        generate_fixture_repo(tmp_path, profile="small")
        summary = build_index(tmp_path, max_objects=10_000, allow_invalid=True)
        assert summary is not None


class TestExportModelLimit:
    def test_export_csv_exceeds_max_objects(self, tmp_path: Path) -> None:
        generate_fixture_repo(tmp_path, profile="small")
        model_path = tmp_path / "model"
        with pytest.raises(ResourceLimitExceeded) as exc_info:
            export_model_csv(model_path, max_objects=1)
        assert exc_info.value.resource == "max_export_objects"
        assert "exceeding max_export_objects limit" in exc_info.value.message

    def test_export_xlsx_exceeds_max_objects(self, tmp_path: Path) -> None:
        generate_fixture_repo(tmp_path, profile="small")
        model_path = tmp_path / "model"
        with pytest.raises(ResourceLimitExceeded) as exc_info:
            export_model_xlsx(model_path, max_objects=1)
        assert exc_info.value.resource == "max_export_objects"

    def test_export_respects_high_limit(self, tmp_path: Path) -> None:
        generate_fixture_repo(tmp_path, profile="small")
        model_path = tmp_path / "model"
        csv_files = export_model_csv(model_path, max_objects=10_000)
        assert isinstance(csv_files, list)
        xlsx_path = export_model_xlsx(model_path, max_objects=10_000)
        assert isinstance(xlsx_path, Path)


class TestImportModelSheetLimit:
    def test_import_xlsx_truncates_at_max_rows(self, tmp_path: Path) -> None:
        from openpyxl import Workbook

        # Build a small model repo
        generate_fixture_repo(tmp_path, profile="small")
        model_path = tmp_path / "model"

        # Create a workbook with 5 rows of data
        wb = Workbook()
        ws = wb.active
        ws.title = "Attribute"
        ws.append(["id", "type", "status", "name"])
        for i in range(1, 6):
            ws.append([f"ATTR-IMPORT-{i}", "Attribute", "draft", f"Import Attribute {i}"])
        xlsx_path = tmp_path / "import.xlsx"
        wb.save(xlsx_path)
        wb.close()

        proposal = import_model_sheet_xlsx(xlsx_path, model_path, max_rows=3)
        # 3 data rows imported (header is not counted as data)
        assert len(proposal["operations"]) == 3
        warnings = proposal.get("warnings", [])
        assert any("truncated at 3 rows" in w for w in warnings)

    def test_import_xlsx_no_truncation_when_under_limit(self, tmp_path: Path) -> None:
        from openpyxl import Workbook

        generate_fixture_repo(tmp_path, profile="small")
        model_path = tmp_path / "model"

        wb = Workbook()
        ws = wb.active
        ws.title = "Attribute"
        ws.append(["id", "type", "status", "name"])
        for i in range(1, 4):
            ws.append([f"ATTR-IMPORT-{i}", "Attribute", "draft", f"Import Attribute {i}"])
        xlsx_path = tmp_path / "import.xlsx"
        wb.save(xlsx_path)
        wb.close()

        proposal = import_model_sheet_xlsx(xlsx_path, model_path, max_rows=100)
        assert len(proposal["operations"]) == 3
        warnings = proposal.get("warnings", [])
        assert not any("truncated" in w for w in warnings)
