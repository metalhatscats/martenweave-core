"""Optional MCP server exposing Martenweave model operations as safe tools."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from modelops_core.config import (
    load_repo_config,
    resolve_generated_path,
    resolve_model_path,
)
from modelops_core.index import build_index as _build_index
from modelops_core.index.query_service import (
    get_object_by_id,
    query_objects,
    search_objects,
)
from modelops_core.repository import parse_file, scan_repository
from modelops_core.trace.trace_service import trace_object
from modelops_core.validation import validate_objects

_MCP_AVAILABLE = False
try:
    from mcp.server.fastmcp import FastMCP

    _MCP_AVAILABLE = True
except ImportError:
    FastMCP = None  # type: ignore[misc, assignment]


DEFAULT_MAX_RESULTS = 20
DEFAULT_MAX_TRACE_DEPTH = 3


def _resolve_repo(repo: str | None) -> Path:
    if repo is None:
        return Path.cwd()
    return Path(repo).resolve()


def _compact_object(obj: dict[str, Any]) -> dict[str, Any]:
    """Return a compact representation of an object for MCP responses."""
    return {
        "object_id": obj.get("id"),
        "object_type": obj.get("type"),
        "status": obj.get("status"),
        "name": obj.get("name") or obj.get("title"),
        "domain": obj.get("domain"),
        "source_file": obj.get("source_file"),
    }


def _ensure_index(repo_root: Path) -> Path:
    """Return the path to the SQLite index, building it if necessary."""
    db_path = resolve_generated_path(repo_root) / "modelops.db"
    if not db_path.exists():
        _build_index(repo_root=repo_root, db_path=db_path, allow_invalid=True)
    return db_path


def create_mcp_server(repo: str | None = None) -> FastMCP:
    """Create and configure a FastMCP server for Martenweave.

    Raises:
        RuntimeError: if the ``mcp`` package is not installed.
    """
    if not _MCP_AVAILABLE or FastMCP is None:
        raise RuntimeError(
            "The 'mcp' package is required for the MCP server. "
            "Install it with: pip install mcp"
        )

    repo_root = _resolve_repo(repo)
    mcp = FastMCP("martenweave")

    @mcp.tool()
    def search_model(
        query: str,
        object_type: str | None = None,
        status: str | None = None,
        domain: str | None = None,
        limit: int = DEFAULT_MAX_RESULTS,
    ) -> str:
        """Search model objects by keywords across name, title, description, and body."""
        db_path = _ensure_index(repo_root)
        results = search_objects(
            db_path=db_path,
            query=query,
            object_type=object_type,
            status=status,
            domain=domain,
            limit=limit,
        )
        output = {
            "results": [
                {
                    "object_id": r.object_id,
                    "object_type": r.object_type,
                    "status": r.status,
                    "name": r.name or r.title,
                    "domain": r.domain,
                    "score": r.score,
                    "matched_fields": r.matched_fields,
                }
                for r in results
            ],
            "total_returned": len(results),
        }
        return json.dumps(output, indent=2, default=str)

    @mcp.tool()
    def query_model(
        object_type: str | None = None,
        status: str | None = None,
        domain: str | None = None,
        name_like: str | None = None,
        limit: int = DEFAULT_MAX_RESULTS,
    ) -> str:
        """Run a structured query over indexed objects."""
        db_path = _ensure_index(repo_root)
        results = query_objects(
            db_path=db_path,
            object_type=object_type,
            status=status,
            domain=domain,
            name_like=name_like,
            limit=limit,
        )
        output = {
            "results": [
                {
                    "object_id": r.object_id,
                    "object_type": r.object_type,
                    "status": r.status,
                    "name": r.name or r.title,
                    "domain": r.domain,
                }
                for r in results
            ],
            "total_returned": len(results),
        }
        return json.dumps(output, indent=2, default=str)

    @mcp.tool()
    def get_object(object_id: str) -> str:
        """Fetch the full frontmatter for a single object by ID."""
        db_path = _ensure_index(repo_root)
        obj = get_object_by_id(db_path, object_id)
        if obj is None:
            return json.dumps({"error": f"Object not found: {object_id}"})
        return json.dumps(obj, indent=2, default=str)

    @mcp.tool()
    def trace_object_tool(
        object_id: str,
        direction: str = "both",
        max_depth: int = DEFAULT_MAX_TRACE_DEPTH,
    ) -> str:
        """Trace upstream and downstream relationships for an object."""
        db_path = _ensure_index(repo_root)
        result = trace_object(
            db_path=db_path,
            object_id=object_id,
            max_depth=max_depth,
            direction=direction,
        )
        output = {
            "root_object_id": result.root_object_id,
            "root_object_type": result.root_object_type,
            "root_object_name": result.root_object_name,
            "nodes": [
                {
                    "object_id": n.object_id,
                    "object_type": n.object_type,
                    "object_name": n.object_name,
                    "depth": n.depth,
                }
                for n in result.nodes
            ],
            "edges": [
                {
                    "from_object_id": e.from_object_id,
                    "to_object_id": e.to_object_id,
                    "relationship_type": e.relationship_type,
                    "direction": e.direction,
                }
                for e in result.edges
            ],
        }
        return json.dumps(output, indent=2, default=str)

    @mcp.tool()
    def validate_model() -> str:
        """Run deterministic validation on all canonical files."""
        model_path = resolve_model_path(repo_root)
        if not model_path.exists():
            return json.dumps(
                {"error": f"Model path does not exist: {model_path}"}
            )

        files = scan_repository(model_path)
        parsed_objects = [parse_file(f) for f in files]
        config = load_repo_config(repo_root)
        enabled_packs = config.enabled_domain_packs if config else None
        summary = validate_objects(parsed_objects, enabled_packs)

        output = {
            "is_valid": summary.is_valid,
            "error_count": summary.error_count,
            "warning_count": summary.warning_count,
            "info_count": summary.info_count,
            "results": [
                {
                    "severity": str(r.severity),
                    "code": r.code,
                    "object_id": r.object_id,
                    "message": r.message,
                    "suggested_fix": r.suggested_fix,
                }
                for r in summary.results[:50]
            ],
            "truncated": len(summary.results) > 50,
            "total_results": len(summary.results),
        }
        return json.dumps(output, indent=2, default=str)

    @mcp.tool()
    def health_report() -> str:
        """Show repository health report."""
        from modelops_core.reports.health_report import generate_repository_health

        db_path = resolve_generated_path(repo_root) / "modelops.db"
        if not db_path.exists():
            return json.dumps(
                {"error": "No index found. Run validate_model or build_index first."}
            )

        report = generate_repository_health(db_path)
        output = {
            "object_count": report.object_count,
            "index_fresh": report.index_fresh,
            "coverage_gaps": {
                "objects_without_name": report.coverage_gaps.objects_without_name
                if report.coverage_gaps
                else 0,
                "objects_without_description": report.coverage_gaps.objects_without_description
                if report.coverage_gaps
                else 0,
            }
            if report.coverage_gaps
            else {},
            "type_counts": report.type_counts,
        }
        return json.dumps(output, indent=2, default=str)

    return mcp
