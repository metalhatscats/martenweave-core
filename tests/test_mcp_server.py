"""Tests for the optional MCP server scaffold."""

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
