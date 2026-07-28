from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from modelops_core.cli import app
from modelops_core.imports.schema_comparison import compare_schema_files


def _write_openapi(path: Path, required: bool = False, type_name: str = "string") -> None:
    required_line = ["      required: [id]"] if required else []
    path.write_text(
        "\n".join(
            [
                "openapi: 3.0.0",
                "info:",
                "  title: Customer API",
                "  version: 1.0.0",
                "paths:",
                "  /customers:",
                "    get:",
                "      operationId: listCustomers",
                "      responses:",
                '        "200":',
                "          description: ok",
                "components:",
                "  schemas:",
                "    Customer:",
                *required_line,
                "      type: object",
                "      properties:",
                "        id:",
                f"          type: {type_name}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_schema_comparison_is_deterministic_and_classifies_required_field(tmp_path: Path) -> None:
    base, candidate = tmp_path / "base.yaml", tmp_path / "candidate.yaml"
    _write_openapi(base)
    _write_openapi(candidate, required=True)

    report = compare_schema_files(str(base), str(candidate))
    assert report == compare_schema_files(str(base), str(candidate))
    field_changes = [item for item in report["differences"] if item["kind"] == "fields"]
    assert field_changes == [
        {
            "kind": "fields",
            "id": "Customer.id",
            "change": "modified",
            "breaking": True,
            "rule_id": "SCHEMA_FIELD_NOW_REQUIRED",
            "before": field_changes[0]["before"],
            "after": field_changes[0]["after"],
        }
    ]


def test_schema_compare_cli_emits_stable_json_and_parser_errors(tmp_path: Path) -> None:
    base, candidate = tmp_path / "base.yaml", tmp_path / "candidate.yaml"
    _write_openapi(base)
    _write_openapi(candidate, type_name="integer")
    runner = CliRunner()

    result = runner.invoke(app, ["schema", "compare", str(base), str(candidate), "--json"])
    assert result.exit_code == 0, result.output
    differences = json.loads(result.stdout)["differences"]
    assert differences[0]["rule_id"] == "SCHEMA_FIELD_CONSTRAINT_CHANGED"

    invalid = tmp_path / "invalid.txt"
    invalid.write_text("not a supported contract", encoding="utf-8")
    failed = runner.invoke(app, ["schema", "compare", str(base), str(invalid)])
    assert failed.exit_code == 1
    assert "Schema file must be" in failed.output
