"""Tests for the optional MCP server scaffold, resources, and prompts."""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys

import pytest

from modelops_core.mcp_server import _MCP_AVAILABLE, create_mcp_server

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
        result = asyncio.run(
            server.get_prompt("explain_trace", {"object_id": "FEP-S4-KNVV-KDGRP"})
        )
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
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            env=env,
            cwd="/Users/dzmitryikharlanau/Developments/martenweave",
        )
        assert result.returncode == 1
        combined = (result.stdout + result.stderr).lower()
        assert "mcp" in combined
