"""Tests for the object-card CLI command and service."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from modelops_core.cli import app
from modelops_core.index.sqlite_builder import build_index
from modelops_core.reports.object_card_service import generate_object_card, object_card_to_dict


def _build_minimal_repo(tmp_path: Path) -> Path:
    """Create a minimal linked repository: domain → attribute ← field endpoint."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    (repo_root / "modelops.config.yaml").write_text(
        'schema_version: "1.0"\nname: Test Repository\n', encoding="utf-8"
    )

    model_dir = repo_root / "model"
    model_dir.mkdir()
    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\nname: Test Domain\n---\n",
        encoding="utf-8",
    )
    (model_dir / "ATTR-TEST.md").write_text(
        "---\n"
        "id: ATTR-TEST\n"
        "type: Attribute\n"
        "status: active\n"
        "name: Test Attribute\n"
        "domain: DOMAIN-TEST\n"
        "description: A test attribute.\n"
        "---\n",
        encoding="utf-8",
    )
    (model_dir / "FEP-TEST.md").write_text(
        "---\n"
        "id: FEP-TEST\n"
        "type: FieldEndpoint\n"
        "status: active\n"
        "name: Test Field\n"
        "attribute: ATTR-TEST\n"
        "endpoint_type: file_column\n"
        "---\n",
        encoding="utf-8",
    )

    build_index(repo_root, allow_invalid=True)
    return repo_root


class TestObjectCardService:
    def test_loads_attribute_with_relationships(self, tmp_path: Path) -> None:
        repo_root = _build_minimal_repo(tmp_path)
        card = generate_object_card(repo_root, "ATTR-TEST")

        assert card.object_id == "ATTR-TEST"
        assert card.object_type == "Attribute"
        assert card.status == "active"
        assert card.name == "Test Attribute"
        assert card.description == "A test attribute."
        # FEP-TEST references ATTR-TEST via the "has_attribute" relationship.
        assert "has_attribute" in card.incoming
        assert any(r["object_id"] == "FEP-TEST" for r in card.incoming["has_attribute"])
        # ATTR-TEST references DOMAIN-TEST via "belongs_to_domain".
        assert "belongs_to_domain" in card.outgoing
        assert any(
            r["object_id"] == "DOMAIN-TEST" for r in card.outgoing["belongs_to_domain"]
        )

    def test_unknown_object_returns_unknown_card(self, tmp_path: Path) -> None:
        repo_root = _build_minimal_repo(tmp_path)
        card = generate_object_card(repo_root, "MISSING-ID")

        assert card.object_type == "Unknown"
        assert card.status == "unknown"

    def test_dict_contract(self, tmp_path: Path) -> None:
        repo_root = _build_minimal_repo(tmp_path)
        card = generate_object_card(repo_root, "ATTR-TEST")
        data = object_card_to_dict(card)

        assert data["object_id"] == "ATTR-TEST"
        assert data["object_type"] == "Attribute"
        assert "incoming_relationships" in data
        assert "outgoing_relationships" in data
        assert "validation_results" in data
        assert "open_issues" in data
        assert "decisions" in data
        assert "evidence" in data
        assert "impact" in data
        assert "trace" in data
        assert "stale_index" in data


class TestObjectCardCli:
    def test_happy_path(self, sample_repo: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            app,
            ["object-card", "ATTR-CUST-SALES-CUSTOMER-GROUP", "--repo", str(sample_repo)],
        )
        assert result.exit_code == 0
        assert "ATTR-CUST-SALES-CUSTOMER-GROUP" in result.output
        assert "Attribute" in result.output
        assert "Source:" in result.output
        assert "Impact summary" in result.output
        assert "Trace summary" in result.output

    def test_json_output(self, sample_repo: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "object-card",
                "ATTR-CUST-SALES-CUSTOMER-GROUP",
                "--repo",
                str(sample_repo),
                "--json",
            ],
        )
        assert result.exit_code == 0
        assert '"object_id"' in result.output
        assert '"object_type"' in result.output
        assert '"incoming_relationships"' in result.output
        assert '"outgoing_relationships"' in result.output

    def test_missing_object(self, sample_repo: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            app,
            ["object-card", "DOES-NOT-EXIST", "--repo", str(sample_repo)],
        )
        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_missing_index(self, tmp_path: Path) -> None:
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        (repo_root / "modelops.config.yaml").write_text(
            'schema_version: "1.0"\nname: Test\n', encoding="utf-8"
        )
        (repo_root / "model").mkdir()

        runner = CliRunner()
        result = runner.invoke(
            app,
            ["object-card", "ANY-ID", "--repo", str(repo_root)],
        )
        assert result.exit_code == 1
        assert "No index found" in result.output

    def test_missing_sections_shown_as_gaps(self, tmp_path: Path) -> None:
        repo_root = _build_minimal_repo(tmp_path)

        runner = CliRunner()
        result = runner.invoke(
            app,
            ["object-card", "ATTR-TEST", "--repo", str(repo_root)],
        )
        assert result.exit_code == 0
        assert "Open issues: none" in result.output
        assert "Decisions: none" in result.output
