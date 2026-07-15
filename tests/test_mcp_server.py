"""Tests for the optional MCP server scaffold, resources, prompts, and write-intent tools."""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from modelops_core.mcp_server import _MCP_AVAILABLE, create_mcp_server
from modelops_core.patching.patch_proposal_service import transition_patch_proposal_status

pytestmark = pytest.mark.skipif(not _MCP_AVAILABLE, reason="mcp package not installed")


def _call_tool_sync(server, name, arguments):
    """Synchronous helper to call an MCP tool."""
    result = asyncio.run(server.call_tool(name, arguments))
    assert len(result) == 2
    content, _meta = result
    assert len(content) == 1
    return json.loads(content[0].text)


class TestMCPServerCreation:
    def test_server_creation_fails_without_mcp(self, monkeypatch):
        """Server creation should fail gracefully if mcp is unavailable."""
        monkeypatch.setattr("modelops_core.mcp_server._MCP_AVAILABLE", False)
        monkeypatch.setattr("modelops_core.mcp_server.FastMCP", None)
        with pytest.raises(RuntimeError, match="mcp"):
            create_mcp_server()

    def test_server_creation_succeeds_with_mcp(self, sample_repo):
        """Server should create successfully when mcp is available."""
        server = create_mcp_server(repo=str(sample_repo))
        assert server is not None


class TestMCPTools:
    def test_search_model_tool(self, sample_repo):
        """search_model should return results for a known object."""
        server = create_mcp_server(repo=str(sample_repo))
        result = _call_tool_sync(
            server,
            "search_model",
            {"query": "Customer Group", "limit": 10},
        )
        assert "results" in result
        assert result["total_returned"] >= 0

    def test_query_model_tool(self, sample_repo):
        """query_model should filter by object type."""
        server = create_mcp_server(repo=str(sample_repo))
        result = _call_tool_sync(
            server,
            "query_model",
            {"object_type": "Attribute", "limit": 10},
        )
        assert "results" in result
        for r in result["results"]:
            assert r["object_type"] == "Attribute"

    def test_get_object_tool_found(self, sample_repo):
        """get_object should return frontmatter for an existing object."""
        server = create_mcp_server(repo=str(sample_repo))
        result = _call_tool_sync(
            server,
            "get_object",
            {"object_id": "ATTR-CUST-SALES-CUSTOMER-GROUP"},
        )
        assert "error" not in result
        assert result.get("id") == "ATTR-CUST-SALES-CUSTOMER-GROUP"
        assert result.get("type") == "Attribute"

    def test_get_object_tool_not_found(self, sample_repo):
        """get_object should return an error for a missing object."""
        server = create_mcp_server(repo=str(sample_repo))
        result = _call_tool_sync(
            server,
            "get_object",
            {"object_id": "DOES-NOT-EXIST"},
        )
        assert "error" in result

    def test_trace_object_tool(self, sample_repo):
        """trace_object should return nodes and edges."""
        server = create_mcp_server(repo=str(sample_repo))
        result = _call_tool_sync(
            server,
            "trace_object_tool",
            {
                "object_id": "FEP-S4-KNVV-KDGRP",
                "direction": "both",
                "max_depth": 2,
            },
        )
        assert result["root_object_id"] == "FEP-S4-KNVV-KDGRP"
        assert "nodes" in result
        assert "edges" in result

    def test_validate_model_tool(self, sample_repo):
        """validate_model should return a validation summary."""
        server = create_mcp_server(repo=str(sample_repo))
        result = _call_tool_sync(
            server,
            "validate_model",
            {},
        )
        assert "is_valid" in result
        assert "error_count" in result
        assert "warning_count" in result

    def test_health_report_tool(self, sample_repo):
        """health_report should return health metrics."""
        server = create_mcp_server(repo=str(sample_repo))
        result = _call_tool_sync(
            server,
            "health_report",
            {},
        )
        assert "object_count" in result
        assert "index_fresh" in result

    def test_list_tools(self, sample_repo):
        """Server should register expected read-only tools."""
        server = create_mcp_server(repo=str(sample_repo))
        tools = asyncio.run(server.list_tools())
        names = {t.name for t in tools}
        expected = {
            "search_model",
            "query_model",
            "get_object",
            "trace_object_tool",
            "validate_model",
            "health_report",
        }
        assert expected.issubset(names)


class TestMCPResources:
    def test_repo_manifest_resource(self, sample_repo):
        """repo_manifest should return repository info."""
        server = create_mcp_server(repo=str(sample_repo))
        result = asyncio.run(server.read_resource("modelops://repo/manifest"))
        data = json.loads(result[0].content)
        assert "repo_name" in data
        assert "object_count" in data
        assert "type_counts" in data

    def test_repo_validation_resource(self, sample_repo):
        """repo_validation should return validation summary."""
        server = create_mcp_server(repo=str(sample_repo))
        result = asyncio.run(server.read_resource("modelops://repo/validation"))
        data = json.loads(result[0].content)
        assert "is_valid" in data
        assert "error_count" in data

    def test_repo_health_resource(self, sample_repo):
        """repo_health should return health metrics."""
        server = create_mcp_server(repo=str(sample_repo))
        result = asyncio.run(server.read_resource("modelops://repo/health"))
        data = json.loads(result[0].content)
        assert "object_count" in data
        assert "index_fresh" in data

    def test_repo_scorecard_resource(self, sample_repo):
        """repo_scorecard should return scorecard."""
        server = create_mcp_server(repo=str(sample_repo))
        result = asyncio.run(server.read_resource("modelops://repo/scorecard"))
        data = json.loads(result[0].content)
        assert "repo_name" in data
        assert "readiness_level" in data

    def test_repo_audit_resource(self, sample_repo):
        """repo_audit should return audit events list."""
        server = create_mcp_server(repo=str(sample_repo))
        result = asyncio.run(server.read_resource("modelops://repo/audit"))
        data = json.loads(result[0].content)
        assert isinstance(data, list)

    def test_repo_proposals_resource(self, sample_repo):
        """repo_proposals should return proposals list."""
        server = create_mcp_server(repo=str(sample_repo))
        result = asyncio.run(server.read_resource("modelops://repo/proposals"))
        data = json.loads(result[0].content)
        assert "proposals" in data

    def test_repo_sources_resource(self, sample_repo):
        """repo_sources should return sources list."""
        server = create_mcp_server(repo=str(sample_repo))
        result = asyncio.run(server.read_resource("modelops://repo/sources"))
        data = json.loads(result[0].content)
        assert "sources" in data

    def test_object_by_id_resource_found(self, sample_repo):
        """object_by_id should return an existing object."""
        server = create_mcp_server(repo=str(sample_repo))
        result = asyncio.run(
            server.read_resource("modelops://object/ATTR-CUST-SALES-CUSTOMER-GROUP")
        )
        data = json.loads(result[0].content)
        assert data.get("id") == "ATTR-CUST-SALES-CUSTOMER-GROUP"

    def test_object_by_id_resource_not_found(self, sample_repo):
        """object_by_id should return error for missing object."""
        server = create_mcp_server(repo=str(sample_repo))
        result = asyncio.run(server.read_resource("modelops://object/DOES-NOT-EXIST"))
        data = json.loads(result[0].content)
        assert "error" in data

    def test_list_resources(self, sample_repo):
        """Server should register expected resources."""
        server = create_mcp_server(repo=str(sample_repo))
        resources = asyncio.run(server.list_resources())
        templates = asyncio.run(server.list_resource_templates())
        uris = {str(r.uri) for r in resources}
        template_uris = {str(t.uriTemplate) for t in templates}
        assert "modelops://repo/manifest" in uris
        assert "modelops://repo/validation" in uris
        assert "modelops://repo/health" in uris
        assert "modelops://repo/scorecard" in uris
        assert "modelops://repo/audit" in uris
        assert "modelops://repo/proposals" in uris
        assert "modelops://repo/sources" in uris
        assert "modelops://object/{object_id}" in template_uris


class TestMCPPrompts:
    def test_review_proposal_prompt(self, sample_repo):
        """review_proposal should return a guidance message."""
        server = create_mcp_server(repo=str(sample_repo))
        result = asyncio.run(server.get_prompt("review_proposal", {"proposal_id": "PP-001"}))
        messages = result.messages
        assert len(messages) == 1
        assert "PP-001" in messages[0].content.text
        assert "get_object" in messages[0].content.text

    def test_explain_trace_prompt(self, sample_repo):
        """explain_trace should return a guidance message."""
        server = create_mcp_server(repo=str(sample_repo))
        result = asyncio.run(server.get_prompt("explain_trace", {"object_id": "FEP-S4-KNVV-KDGRP"}))
        messages = result.messages
        assert len(messages) == 1
        assert "FEP-S4-KNVV-KDGRP" in messages[0].content.text

    def test_find_governance_gaps_prompt(self, sample_repo):
        """find_governance_gaps should return a guidance message."""
        server = create_mcp_server(repo=str(sample_repo))
        result = asyncio.run(server.get_prompt("find_governance_gaps", {}))
        messages = result.messages
        assert len(messages) == 1
        assert "health_report" in messages[0].content.text

    def test_build_model_from_file_prompt(self, sample_repo):
        """build_model_from_file should return a guidance message."""
        server = create_mcp_server(repo=str(sample_repo))
        result = asyncio.run(
            server.get_prompt("build_model_from_file", {"dataset_path": "/tmp/data.csv"})
        )
        messages = result.messages
        assert len(messages) == 1
        assert "/tmp/data.csv" in messages[0].content.text

    def test_prepare_excel_review_prompt(self, sample_repo):
        """prepare_excel_review should return a guidance message."""
        server = create_mcp_server(repo=str(sample_repo))
        result = asyncio.run(server.get_prompt("prepare_excel_review", {}))
        messages = result.messages
        assert len(messages) == 1
        assert "export-model" in messages[0].content.text

    def test_create_change_request_prompt(self, sample_repo):
        """create_change_request should return a guidance message."""
        server = create_mcp_server(repo=str(sample_repo))
        result = asyncio.run(
            server.get_prompt("create_change_request", {"description": "Add new field"})
        )
        messages = result.messages
        assert len(messages) == 1
        assert "Add new field" in messages[0].content.text

    def test_list_prompts(self, sample_repo):
        """Server should register expected prompts."""
        server = create_mcp_server(repo=str(sample_repo))
        prompts = asyncio.run(server.list_prompts())
        names = {p.name for p in prompts}
        expected = {
            "review_proposal",
            "explain_trace",
            "find_governance_gaps",
            "build_model_from_file",
            "prepare_excel_review",
            "create_change_request",
        }
        assert expected.issubset(names)


class TestMCPWriteIntentTools:
    def test_propose_model_change_tool(self, sample_repo):
        """propose_model_change should create a PatchProposal from a note."""
        server = create_mcp_server(repo=str(sample_repo))
        result = _call_tool_sync(
            server,
            "propose_model_change",
            {"note": "Update the description of Customer Group to clarify usage."},
        )
        assert "proposal_id" in result
        assert "operations_count" in result
        assert "path" in result
        assert isinstance(result.get("assumptions"), list)
        assert isinstance(result.get("human_checks"), list)

    def test_propose_model_change_triggers_telemetry(self, sample_repo):
        """propose_model_change should log an AI usage event when repo_root is provided."""
        server = create_mcp_server(repo=str(sample_repo))
        _call_tool_sync(
            server,
            "propose_model_change",
            {"note": "Update the description of Customer Group to clarify usage."},
        )
        log_path = sample_repo / "generated" / "ai_usage_events.jsonl"
        assert log_path.exists()
        raw_lines = log_path.read_text(encoding="utf-8").splitlines()
        events = [json.loads(line) for line in raw_lines if line.strip()]
        matching = [e for e in events if e.get("command") == "mcp-propose-model-change"]
        assert matching, (
            f"Expected a telemetry event with command='mcp-propose-model-change' in {events}"
        )
        assert matching[-1]["provider"] == "NoProviderAdapter"

    @patch("modelops_core.ai.patch_proposal_service.build_patch_proposal_from_note")
    def test_propose_model_change_provider_error(self, mock_build, sample_repo):
        """propose_model_change should return a structured error on provider failure."""
        from modelops_core.ai.provider_adapter import AIProviderError

        mock_build.side_effect = AIProviderError("provider is unavailable")
        server = create_mcp_server(repo=str(sample_repo))
        result = _call_tool_sync(
            server,
            "propose_model_change",
            {"note": "Update the description of Customer Group to clarify usage."},
        )
        assert result.get("is_safe") is False
        assert "error" in result
        assert "provider is unavailable" in result["error"]
        assert isinstance(result.get("assumptions"), list)
        assert isinstance(result.get("human_checks"), list)

    def test_proposal_dry_run_not_found(self, sample_repo):
        """proposal_dry_run should error for a missing proposal."""
        server = create_mcp_server(repo=str(sample_repo))
        result = _call_tool_sync(
            server,
            "proposal_dry_run",
            {"proposal_id": "PP-DOES-NOT-EXIST"},
        )
        assert "error" in result
        assert isinstance(result.get("assumptions"), list)
        assert isinstance(result.get("human_checks"), list)

    def test_proposal_dry_run_returns_assumptions_and_human_checks(self, sample_repo):
        """proposal_dry_run should include assumptions and human_checks for a valid proposal."""
        server = create_mcp_server(repo=str(sample_repo))
        created = _call_tool_sync(
            server,
            "propose_model_change",
            {"note": "Update the description of Customer Group to clarify usage."},
        )
        proposal_path = Path(created["path"])
        transition_patch_proposal_status(proposal_path, "accepted", reviewer="tester")

        result = _call_tool_sync(
            server,
            "proposal_dry_run",
            {"proposal_id": created["proposal_id"]},
        )
        assert result.get("error") is None
        assert result.get("would_change") is True
        assert isinstance(result.get("assumptions"), list)
        assert isinstance(result.get("human_checks"), list)

    def test_proposal_impact_not_found(self, sample_repo):
        """proposal_impact should error for a missing proposal."""
        server = create_mcp_server(repo=str(sample_repo))
        result = _call_tool_sync(
            server,
            "proposal_impact",
            {"proposal_id": "PP-DOES-NOT-EXIST"},
        )
        assert "error" in result
        assert isinstance(result.get("assumptions"), list)
        assert isinstance(result.get("human_checks"), list)

    def test_proposal_impact_returns_assumptions_and_human_checks(self, sample_repo):
        """proposal_impact should include assumptions and human_checks for a valid proposal."""
        server = create_mcp_server(repo=str(sample_repo))
        created = _call_tool_sync(
            server,
            "propose_model_change",
            {"note": "Update the description of Customer Group to clarify usage."},
        )
        result = _call_tool_sync(
            server,
            "proposal_impact",
            {"proposal_id": created["proposal_id"]},
        )
        assert "error" not in result
        assert "affected_objects" in result
        assert isinstance(result.get("assumptions"), list)
        assert isinstance(result.get("human_checks"), list)

    def test_create_change_request_tool(self, sample_repo):
        """create_change_request_tool should create a CR file."""
        server = create_mcp_server(repo=str(sample_repo))
        result = _call_tool_sync(
            server,
            "create_change_request_tool",
            {
                "cr_id": "CR-TEST-001",
                "title": "Test Change Request",
                "requester": "tester",
                "reason": "Testing MCP write-intent tool.",
            },
        )
        assert "error" not in result
        assert result.get("id") == "CR-TEST-001"
        assert "path" in result
        assert isinstance(result.get("assumptions"), list)
        assert isinstance(result.get("human_checks"), list)

    def test_create_change_request_tool_invalid_id(self, sample_repo):
        """create_change_request_tool should error for invalid ID."""
        server = create_mcp_server(repo=str(sample_repo))
        result = _call_tool_sync(
            server,
            "create_change_request_tool",
            {
                "cr_id": "invalid-id",
                "title": "Test",
            },
        )
        assert "error" in result
        assert isinstance(result.get("assumptions"), list)
        assert isinstance(result.get("human_checks"), list)

    def test_export_model_tool(self, sample_repo):
        """export_model should return exported file summary."""
        server = create_mcp_server(repo=str(sample_repo))
        result = _call_tool_sync(
            server,
            "export_model",
            {"fmt": "csv"},
        )
        assert "error" not in result
        assert result.get("format") == "csv"
        assert "files" in result
        assert isinstance(result.get("assumptions"), list)
        assert isinstance(result.get("human_checks"), list)

    def test_export_model_unknown_format(self, sample_repo):
        """export_model should error for unknown format."""
        server = create_mcp_server(repo=str(sample_repo))
        result = _call_tool_sync(
            server,
            "export_model",
            {"fmt": "pdf"},
        )
        assert "error" in result
        assert isinstance(result.get("assumptions"), list)
        assert isinstance(result.get("human_checks"), list)

    def test_infer_model_with_dataset_id_and_domain(self, sample_repo, tmp_path: Path):
        """infer_model should accept dataset_id and domain hints."""
        profile = {
            "file_path": "customer_sample.csv",
            "columns": [
                {"name": "customer_id", "inferred_type": "string"},
                {"name": "name", "inferred_type": "string"},
            ],
        }
        profile_path = tmp_path / "customer_profile.json"
        profile_path.write_text(json.dumps(profile), encoding="utf-8")

        server = create_mcp_server(repo=str(sample_repo))
        result = _call_tool_sync(
            server,
            "infer_model",
            {
                "profile_path": str(profile_path),
                "dataset_id": "my-dataset",
                "domain": "DOMAIN-MY-DOMAIN",
            },
        )
        assert "error" not in result
        assert result["proposal_id"] == "PP-INFER-MY-DATASET"
        assert isinstance(result.get("assumptions"), list)
        assert isinstance(result.get("human_checks"), list)
        operations = result.get("operations", [])
        assert all(op.get("after", {}).get("domain") == "DOMAIN-MY-DOMAIN" for op in operations)

    def test_infer_model_returns_assumptions_and_human_checks(self, sample_repo, tmp_path: Path):
        """infer_model should return assumptions and human_checks arrays."""
        profile = {
            "file_path": "customer_sample.csv",
            "columns": [
                {"name": "customer_id", "inferred_type": "string"},
            ],
        }
        profile_path = tmp_path / "customer_profile.json"
        profile_path.write_text(json.dumps(profile), encoding="utf-8")

        server = create_mcp_server(repo=str(sample_repo))
        result = _call_tool_sync(
            server,
            "infer_model",
            {"profile_path": str(profile_path)},
        )
        assert "error" not in result
        assert isinstance(result.get("assumptions"), list)
        assert isinstance(result.get("human_checks"), list)

    def test_infer_model_missing_profile_path(self, sample_repo):
        """infer_model should include assumptions and human_checks on error path."""
        server = create_mcp_server(repo=str(sample_repo))
        result = _call_tool_sync(
            server,
            "infer_model",
            {"profile_path": "/does/not/exist/profile.json"},
        )
        assert "error" in result
        assert isinstance(result.get("assumptions"), list)
        assert isinstance(result.get("human_checks"), list)

    def test_infer_model_invalid_json(self, sample_repo, tmp_path: Path):
        """infer_model should return a structured error for invalid JSON profiles."""
        profile_path = tmp_path / "profile.json"
        profile_path.write_text("not valid json", encoding="utf-8")
        server = create_mcp_server(repo=str(sample_repo))
        result = _call_tool_sync(
            server,
            "infer_model",
            {"profile_path": str(profile_path)},
        )
        assert "error" in result
        assert "Invalid JSON profile" in result["error"]
        assert isinstance(result.get("assumptions"), list)
        assert isinstance(result.get("human_checks"), list)

    def test_list_write_intent_tools(self, sample_repo):
        """Server should register write-intent tools."""
        server = create_mcp_server(repo=str(sample_repo))
        tools = asyncio.run(server.list_tools())
        names = {t.name for t in tools}
        expected = {
            "propose_model_change",
            "proposal_dry_run",
            "proposal_impact",
            "create_change_request_tool",
            "export_model",
            "infer_model",
        }
        assert expected.issubset(names)


class TestMCPInvalidRepo:
    def test_search_model_fails_on_invalid_repo(self, tmp_path: Path):
        """MCP tools must not silently build an index for invalid repositories."""
        model_dir = tmp_path / "model"
        model_dir.mkdir()
        # Two objects with the same ID -> validation error
        (model_dir / "OBJ-001.md").write_text(
            "---\nid: DUP-ID\ntype: Attribute\nstatus: draft\nname: A\n---\n",
            encoding="utf-8",
        )
        (model_dir / "OBJ-002.md").write_text(
            "---\nid: DUP-ID\ntype: Attribute\nstatus: draft\nname: B\n---\n",
            encoding="utf-8",
        )

        server = create_mcp_server(repo=str(tmp_path))
        with pytest.raises(Exception) as exc_info:
            _call_tool_sync(server, "search_model", {"query": "A", "limit": 10})
        combined = str(exc_info.value).lower()
        assert "cannot build index for invalid repository" in combined
        assert "validate_model" in combined

    def test_query_model_fails_on_invalid_repo(self, tmp_path: Path):
        """query_model must fail clearly when the repo is invalid."""
        model_dir = tmp_path / "model"
        model_dir.mkdir()
        (model_dir / "BAD.md").write_text(
            "---\nid: bad-id-lowercase\ntype: Attribute\nstatus: draft\nname: X\n---\n",
            encoding="utf-8",
        )

        server = create_mcp_server(repo=str(tmp_path))
        with pytest.raises(Exception, match="(?i)cannot build index for invalid repository"):
            _call_tool_sync(server, "query_model", {"object_type": "Attribute"})

    def test_get_object_fails_on_invalid_repo(self, tmp_path: Path):
        """get_object must fail clearly when the repo is invalid."""
        model_dir = tmp_path / "model"
        model_dir.mkdir()
        (model_dir / "BAD.md").write_text(
            "---\nid: BAD-ID\ntype: UnknownType\nstatus: draft\nname: X\n---\n",
            encoding="utf-8",
        )

        server = create_mcp_server(repo=str(tmp_path))
        with pytest.raises(Exception) as exc_info:
            _call_tool_sync(server, "get_object", {"object_id": "BAD-ID"})
        combined = str(exc_info.value).lower()
        assert "cannot build index for invalid repository" in combined

    def test_trace_object_fails_on_invalid_repo(self, tmp_path: Path):
        """trace_object_tool must fail clearly when the repo is invalid."""
        model_dir = tmp_path / "model"
        model_dir.mkdir()
        (model_dir / "BAD.md").write_text(
            "---\nid: bad-id-lowercase\ntype: Attribute\nstatus: draft\nname: X\n---\n",
            encoding="utf-8",
        )

        server = create_mcp_server(repo=str(tmp_path))
        with pytest.raises(Exception, match="(?i)cannot build index for invalid repository"):
            _call_tool_sync(
                server, "trace_object_tool", {"object_id": "bad-id-lowercase", "direction": "both"}
            )

    def test_object_by_id_resource_fails_on_invalid_repo(self, tmp_path: Path):
        """object_by_id resource must fail clearly when the repo is invalid."""
        model_dir = tmp_path / "model"
        model_dir.mkdir()
        (model_dir / "BAD.md").write_text(
            "---\nid: bad-id-lowercase\ntype: Attribute\nstatus: draft\nname: X\n---\n",
            encoding="utf-8",
        )

        server = create_mcp_server(repo=str(tmp_path))
        with pytest.raises(Exception, match="(?i)cannot build index for invalid repository"):
            asyncio.run(server.read_resource("modelops://object/bad-id-lowercase"))

    def test_no_index_created_for_invalid_repo(self, tmp_path: Path):
        """No SQLite db should be written when repo validation fails."""
        model_dir = tmp_path / "model"
        model_dir.mkdir()
        (model_dir / "DUP-A.md").write_text(
            "---\nid: DUP\ntype: Attribute\nstatus: draft\nname: A\n---\n",
            encoding="utf-8",
        )
        (model_dir / "DUP-B.md").write_text(
            "---\nid: DUP\ntype: Attribute\nstatus: draft\nname: B\n---\n",
            encoding="utf-8",
        )

        db_path = tmp_path / "generated" / "modelops.db"
        server = create_mcp_server(repo=str(tmp_path))
        with pytest.raises(Exception, match="(?i)cannot build index for invalid repository"):
            _call_tool_sync(server, "search_model", {"query": "A"})
        assert not db_path.exists()


class TestMCPCLIGracefulDegradation:
    def test_cli_shows_error_when_mcp_missing(self, tmp_path):
        """CLI should show a helpful error if mcp is not installed."""
        repo_path = str(tmp_path)
        code = (
            "import sys; "
            "sys.modules['mcp'] = None; "
            "sys.modules['mcp.server'] = None; "
            "sys.modules['mcp.server.fastmcp'] = None; "
            f"from modelops_core.cli import app; "
            "from typer.testing import CliRunner; "
            f"r = CliRunner().invoke(app, ['mcp', '--repo', {repo_path!r}]); "
            "print(r.output); "
            "sys.exit(r.exit_code)"
        )
        env = {
            **dict(subprocess.os.environ),
            "PYTHONPATH": "src",
        }
        repo_root = str(Path(__file__).resolve().parent.parent)
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            env=env,
            cwd=repo_root,
        )
        assert result.returncode == 1
        combined = (result.stdout + result.stderr).lower()
        assert "mcp" in combined
