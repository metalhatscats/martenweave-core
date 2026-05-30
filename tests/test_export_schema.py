"""Tests for JSON Schema export service and CLI."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from modelops_core.cli import app
from modelops_core.exports.schema_export_service import export_schemas, write_schema_export
from modelops_core.schemas.registry import get_all_types

runner = CliRunner()


class TestExportSchemasService:
    def test_export_all_types(self) -> None:
        result = export_schemas()
        assert result["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert result["title"] == "ModelOps Canonical Object Schemas"
        all_types = get_all_types()
        assert result["type_count"] == len(all_types)
        schemas = result["schemas"]
        for t in all_types:
            assert t in schemas
            schema = schemas[t]
            assert "properties" in schema
            assert "id" in schema["properties"]
            assert "type" in schema["properties"]
            assert "status" in schema["properties"]

    def test_export_single_type(self) -> None:
        result = export_schemas(type_filter="Attribute")
        assert result["type_count"] == 1
        assert "Attribute" in result["schemas"]
        schema = result["schemas"]["Attribute"]
        assert "properties" in schema
        assert "semantic_category" in schema["properties"]

    def test_export_type_all_explicit(self) -> None:
        result = export_schemas(type_filter="all")
        all_types = get_all_types()
        assert result["type_count"] == len(all_types)

    def test_export_unknown_type_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown object type"):
            export_schemas(type_filter="NotARealType")

    def test_deterministic_sorted_keys(self) -> None:
        result = export_schemas()
        text = json.dumps(result, sort_keys=True)
        result2 = export_schemas()
        text2 = json.dumps(result2, sort_keys=True)
        assert text == text2
        type_names = list(result["schemas"].keys())
        assert type_names == sorted(type_names)

    def test_write_schema_export(self, tmp_path: Path) -> None:
        out = tmp_path / "schema.json"
        path = write_schema_export(out, type_filter="MasterDataDomain")
        assert path == out
        assert out.exists()
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["type_count"] == 1
        assert "MasterDataDomain" in data["schemas"]


class TestExportSchemaCLI:
    def test_cli_export_schema_json(self, sample_repo: Path) -> None:
        result = runner.invoke(
            app, ["export-schema", "--repo", str(sample_repo), "--json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output.strip())
        assert data["type_count"] > 0
        assert "schemas" in data
        all_types = get_all_types()
        assert data["type_count"] == len(all_types)

    def test_cli_export_schema_type_filter(self, sample_repo: Path) -> None:
        result = runner.invoke(
            app,
            ["export-schema", "--repo", str(sample_repo), "--type", "FieldEndpoint", "--json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output.strip())
        assert data["type_count"] == 1
        assert "FieldEndpoint" in data["schemas"]
        schema = data["schemas"]["FieldEndpoint"]
        assert "properties" in schema
        assert "sap_table" in schema["properties"]
        assert "endpoint_type" in schema["properties"]

    def test_cli_export_schema_output_file(self, sample_repo: Path) -> None:
        out = sample_repo / "generated" / "schemas" / "test.json"
        result = runner.invoke(
            app,
            [
                "export-schema",
                "--repo",
                str(sample_repo),
                "--type",
                "Attribute",
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 0
        assert out.exists()
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["type_count"] == 1
        assert "Attribute" in data["schemas"]

    def test_cli_export_schema_unknown_type(self, sample_repo: Path) -> None:
        result = runner.invoke(
            app,
            [
                "export-schema",
                "--repo",
                str(sample_repo),
                "--type",
                "BogusType",
                "--json",
            ],
        )
        assert result.exit_code == 1
        data = json.loads(result.output.strip())
        assert "error" in data
        assert "Unknown object type" in data["error"]

    def test_cli_export_schema_required_fields_match(self, sample_repo: Path) -> None:
        result = runner.invoke(
            app,
            [
                "export-schema",
                "--repo",
                str(sample_repo),
                "--type",
                "Attribute",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output.strip())
        schema = data["schemas"]["Attribute"]
        assert "required" in schema
        assert "id" in schema["required"]
        assert "type" in schema["required"]
        assert "status" in schema["required"]
