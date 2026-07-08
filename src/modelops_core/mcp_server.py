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
    """Return the path to the SQLite index, building it if necessary.

    Raises:
        ValueError: if the repository has validation errors and cannot be
            indexed safely. The agent should run ``validate_model`` to
            diagnose and fix issues before retrying.
    """
    db_path = resolve_generated_path(repo_root) / "modelops.db"
    if not db_path.exists():
        try:
            _build_index(repo_root=repo_root, db_path=db_path, allow_invalid=False)
        except ValueError as exc:
            raise ValueError(
                f"Cannot build index for invalid repository: {exc} "
                "Run validate_model to see errors, fix them, then retry."
            ) from exc
    return db_path


def create_mcp_server(repo: str | None = None) -> FastMCP:
    """Create and configure a FastMCP server for Martenweave.

    Raises:
        RuntimeError: if the ``mcp`` package is not installed.
    """
    if not _MCP_AVAILABLE or FastMCP is None:
        raise RuntimeError(
            "The 'mcp' package is required for the MCP server. Install it with: pip install mcp"
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
        paginated = search_objects(
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
                for r in paginated.results
            ],
            "total_returned": paginated.total_count,
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
        paginated = query_objects(
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
                for r in paginated.results
            ],
            "total_returned": paginated.total_count,
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
            return json.dumps({"error": f"Model path does not exist: {model_path}"})

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
            return json.dumps({"error": "No index found. Run validate_model or build_index first."})

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

    # ------------------------------------------------------------------
    # Resources
    # ------------------------------------------------------------------

    @mcp.resource(
        "modelops://repo/manifest",
        name="repo_manifest",
        description="Repository configuration and object counts.",
        mime_type="application/json",
    )
    def repo_manifest() -> str:
        """Return repository manifest with config and object counts."""
        model_path = resolve_model_path(repo_root)
        config = load_repo_config(repo_root)
        files = scan_repository(model_path) if model_path.exists() else []
        type_counts: dict[str, int] = {}
        for f in files:
            try:
                obj = parse_file(f)
                t = obj.frontmatter.get("type", "Unknown")
                type_counts[t] = type_counts.get(t, 0) + 1
            except Exception:
                continue
        manifest = {
            "repo_name": config.name if config else None,
            "schema_version": config.schema_version if config else None,
            "object_count": len(files),
            "type_counts": type_counts,
            "model_path": str(model_path),
        }
        return json.dumps(manifest, indent=2, default=str)

    @mcp.resource(
        "modelops://repo/validation",
        name="repo_validation",
        description="Latest validation summary.",
        mime_type="application/json",
    )
    def repo_validation() -> str:
        """Return the latest validation summary."""
        model_path = resolve_model_path(repo_root)
        if not model_path.exists():
            return json.dumps({"error": "Model path does not exist"})
        files = scan_repository(model_path)
        parsed_objects = [parse_file(f) for f in files]
        config = load_repo_config(repo_root)
        enabled_packs = config.enabled_domain_packs if config else None
        summary = validate_objects(parsed_objects, enabled_packs)
        return json.dumps(
            {
                "is_valid": summary.is_valid,
                "error_count": summary.error_count,
                "warning_count": summary.warning_count,
                "info_count": summary.info_count,
            },
            indent=2,
            default=str,
        )

    @mcp.resource(
        "modelops://repo/health",
        name="repo_health",
        description="Repository health report.",
        mime_type="application/json",
    )
    def repo_health() -> str:
        """Return repository health metrics."""
        from modelops_core.reports.health_report import generate_repository_health

        db_path = resolve_generated_path(repo_root) / "modelops.db"
        if not db_path.exists():
            return json.dumps({"error": "No index found. Run validate_model or build_index first."})
        report = generate_repository_health(db_path)
        return json.dumps(
            {
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
            },
            indent=2,
            default=str,
        )

    @mcp.resource(
        "modelops://repo/scorecard",
        name="repo_scorecard",
        description="Governance readiness scorecard.",
        mime_type="application/json",
    )
    def repo_scorecard() -> str:
        """Return governance scorecard."""
        from modelops_core.reports.scorecard_service import generate_scorecard

        db_path = resolve_generated_path(repo_root) / "modelops.db"
        if not db_path.exists():
            return json.dumps({"error": "No index found. Run validate_model or build_index first."})
        report = generate_scorecard(db_path, repo_root)
        return json.dumps(
            {
                "repo_name": report.repo_name,
                "readiness_level": report.readiness_level,
                "object_count": report.object_count,
                "metrics": [
                    {
                        "name": m.name,
                        "value": m.value,
                        "target": m.target,
                        "status": m.status,
                    }
                    for m in report.metrics
                ],
            },
            indent=2,
            default=str,
        )

    @mcp.resource(
        "modelops://repo/audit",
        name="repo_audit",
        description="Recent audit events (last 50).",
        mime_type="application/json",
    )
    def repo_audit() -> str:
        """Return recent audit events."""
        from modelops_core.reports.audit_service import AuditEventService

        service = AuditEventService(repo_root)
        events = service.read_events()
        return json.dumps(
            [e.to_dict() for e in events[-50:]],
            indent=2,
            default=str,
        )

    @mcp.resource(
        "modelops://repo/proposals",
        name="repo_proposals",
        description="List of PatchProposals in the repository.",
        mime_type="application/json",
    )
    def repo_proposals() -> str:
        """Return a list of PatchProposals."""
        model_path = resolve_model_path(repo_root)
        proposals_dir = model_path / "patch-proposals"
        if not proposals_dir.exists():
            return json.dumps({"proposals": []})
        proposals = []
        for f in sorted(proposals_dir.glob("PP-*.md")):
            try:
                parsed = parse_file(f)
                fm = parsed.frontmatter or {}
                proposals.append(
                    {
                        "id": fm.get("id", f.stem),
                        "status": fm.get("status"),
                        "validation_status": fm.get("validation_status"),
                        "operations_count": len(fm.get("operations", [])),
                        "applied_at": fm.get("applied_at"),
                    }
                )
            except Exception:
                continue
        return json.dumps({"proposals": proposals}, indent=2, default=str)

    @mcp.resource(
        "modelops://repo/sources",
        name="repo_sources",
        description="Registered import source summary.",
        mime_type="application/json",
    )
    def repo_sources() -> str:
        """Return registered import sources."""
        from modelops_core.reports.source_registry_service import SourceRegistryService

        service = SourceRegistryService(repo_root)
        entries = service.list_sources()
        return json.dumps(
            {"sources": entries},
            indent=2,
            default=str,
        )

    @mcp.resource(
        "modelops://object/{object_id}",
        name="object_by_id",
        description="Full frontmatter for a single object.",
        mime_type="application/json",
    )
    def object_by_id(object_id: str) -> str:
        """Return full frontmatter for a single object."""
        db_path = _ensure_index(repo_root)
        obj = get_object_by_id(db_path, object_id)
        if obj is None:
            return json.dumps({"error": f"Object not found: {object_id}"})
        return json.dumps(obj, indent=2, default=str)

    # ------------------------------------------------------------------
    # Prompts
    # ------------------------------------------------------------------

    @mcp.prompt()
    def review_proposal(proposal_id: str) -> list[dict[str, str]]:
        """Guide an agent through reviewing a PatchProposal."""
        return [
            {
                "role": "user",
                "content": (
                    f"Review PatchProposal {proposal_id} for safety and correctness.\n\n"
                    "1. Use get_object to read the proposal if it exists as a canonical object.\n"
                    "2. Use trace_object_tool to assess impact of affected objects.\n"
                    "3. Use validate_model to check if the repository is currently valid.\n"
                    "4. Look for risks: breaking changes, missing references, ownership gaps.\n"
                    "5. Recommend approve, reject, or request changes with reasoning.\n\n"
                    "Do not apply the proposal without human approval."
                ),
            }
        ]

    @mcp.prompt()
    def explain_trace(object_id: str) -> list[dict[str, str]]:
        """Guide an agent to explain the lineage of an object."""
        return [
            {
                "role": "user",
                "content": (
                    f"Explain the data lineage for object {object_id}.\n\n"
                    "1. Use get_object to understand what this object represents.\n"
                    "2. Use trace_object_tool with direction='upstream' to find sources.\n"
                    "3. Use trace_object_tool with direction='downstream' to find consumers.\n"
                    "4. Summarize the trace in business terms: what flows in, what flows out, "
                    "and what transformations happen along the way.\n\n"
                    "Keep the explanation concise and focused on business meaning."
                ),
            }
        ]

    @mcp.prompt()
    def find_governance_gaps() -> list[dict[str, str]]:
        """Guide an agent to find coverage and governance gaps."""
        return [
            {
                "role": "user",
                "content": (
                    "Find governance gaps in this Martenweave repository.\n\n"
                    "1. Use health_report to get coverage metrics.\n"
                    "2. Use validate_model to find validation issues.\n"
                    "3. Use query_model with object_type='Attribute' to list attributes "
                    "and check for missing entity_context.\n"
                    "4. Use query_model with object_type='FieldEndpoint' to check for "
                    "missing value_list or mapping coverage.\n"
                    "5. Summarize the top 5 gaps with severity and suggested fixes.\n\n"
                    "Focus on actionable gaps that a data steward could address."
                ),
            }
        ]

    @mcp.prompt()
    def build_model_from_file(dataset_path: str) -> list[dict[str, str]]:
        """Guide an agent to build a draft model from a dataset."""
        return [
            {
                "role": "user",
                "content": (
                    f"Build a draft model from dataset at {dataset_path}.\n\n"
                    "1. Use validate_model to understand the current model state.\n"
                    "2. Suggest Domain, Entity, Attribute, and FieldEndpoint candidates "
                    "based on the dataset structure.\n"
                    "3. Propose a PatchProposal with add operations for new objects.\n"
                    "4. Ensure every Attribute has an entity_context where possible.\n"
                    "5. Ensure every FieldEndpoint has a corresponding Attribute.\n\n"
                    "Do not apply the proposal directly. Return it for human review."
                ),
            }
        ]

    @mcp.prompt()
    def prepare_excel_review() -> list[dict[str, str]]:
        """Guide an agent to prepare an Excel export for business review."""
        return [
            {
                "role": "user",
                "content": (
                    "Prepare an Excel workbook for business review of this model.\n\n"
                    "1. Use query_model to list active objects by type.\n"
                    "2. Use health_report to identify objects missing names or descriptions.\n"
                    "3. Recommend which objects need business owner or steward assignment.\n"
                    "4. Suggest export-model --format xlsx --business-review as the final step.\n\n"
                    "Focus on making the review package actionable for non-technical stakeholders."
                ),
            }
        ]

    @mcp.prompt()
    def create_change_request(description: str) -> list[dict[str, str]]:
        """Guide an agent to create a well-formed ChangeRequest."""
        return [
            {
                "role": "user",
                "content": (
                    f"Create a ChangeRequest for: {description}\n\n"
                    "1. Use validate_model to confirm the current model state.\n"
                    "2. Identify affected objects using query_model or search_model.\n"
                    "3. Use trace_object_tool to assess downstream impact.\n"
                    "4. Draft a ChangeRequest with:\n"
                    "   - Clear title and reason\n"
                    "   - List of affected_object IDs\n"
                    "   - Expected impact summary\n"
                    "   - Required approvers based on object ownership\n\n"
                    "Do not modify canonical files directly. "
                    "Output a ChangeRequest for human review."
                ),
            }
        ]

    @mcp.prompt()
    def run_agent_loop(goal: str) -> list[dict[str, str]]:
        """Guide an agent through a closed propose-validate-refine cycle."""
        return [
            {
                "role": "user",
                "content": (
                    f"Run the agent loop for this modeling goal: {goal}\n\n"
                    "Follow this sequence exactly:\n"
                    "1. Use validate_model to check the current repository state.\n"
                    "2. Use propose_model_change with the goal as the note to create a "
                    "PatchProposal.\n"
                    "3. If the proposal is invalid, refine the note by appending the "
                    "validation errors and call propose_model_change again. Stop if errors "
                    "do not change between iterations.\n"
                    "4. Once the proposal is valid, use proposal_impact to assess "
                    "downstream risk.\n"
                    "5. Use proposal_dry_run to preview what applying the proposal would do.\n"
                    "6. If the impact is high-risk, create a ChangeRequest before applying.\n\n"
                    "Rules:\n"
                    "- Never apply proposals automatically.\n"
                    "- Stop after at most 5 iterations if the proposal remains invalid.\n"
                    "- Only write canonical PatchProposal files; do not mutate other "
                    "canonical objects.\n"
                    "- Return the final proposal ID, validation status, impact summary, "
                    "and next steps."
                ),
            }
        ]

    # ------------------------------------------------------------------
    # Write-intent tools (safe — all go through PatchProposal / CR)
    # ------------------------------------------------------------------

    @mcp.tool()
    def propose_model_change(
        note: str,
    ) -> str:
        """Create a PatchProposal from a free-text description of desired changes.

        The proposal is written to ``model/patch-proposals/`` for human review.
        It is NOT applied automatically.
        """
        from modelops_core.ai.patch_proposal_service import (
            build_patch_proposal_from_note,
        )
        from modelops_core.patching.patch_proposal_service import write_patch_proposal

        model_path = resolve_model_path(repo_root)
        result = build_patch_proposal_from_note(
            note, repo_root=repo_root, command="mcp-propose-model-change"
        )
        proposal = result.get("proposal")
        if proposal is None:
            return json.dumps(
                {
                    "error": "No proposal generated.",
                    "assumptions": result.get("assumptions", []),
                    "human_checks": result.get("human_checks", []),
                },
                indent=2,
                default=str,
            )
        path = write_patch_proposal(proposal, model_path)
        return json.dumps(
            {
                "proposal_id": proposal.get("id"),
                "operations_count": len(proposal.get("operations", [])),
                "is_safe": result.get("is_safe"),
                "path": str(path),
                "assumptions": result.get("assumptions", []),
                "human_checks": result.get("human_checks", []),
            },
            indent=2,
            default=str,
        )

    @mcp.tool()
    def infer_model(
        profile_path: str,
        dataset_id: str | None = None,
        domain: str | None = None,
    ) -> str:
        """Infer draft model objects from a dataset profile JSON and create a PatchProposal.

        The profile is typically generated by ``profile_dataset``.
        The proposal is written for human review, not applied automatically.
        """
        from modelops_core.imports import infer_model_from_profile
        from modelops_core.patching.patch_proposal_service import write_patch_proposal
        from modelops_core.patching.patch_validator import validate_patch_proposal

        profile_file = Path(profile_path)
        if not profile_file.exists():
            return json.dumps(
                {
                    "error": f"Profile not found: {profile_path}",
                    "assumptions": [],
                    "human_checks": [],
                },
                indent=2,
                default=str,
            )

        profile_dict = json.loads(profile_file.read_text(encoding="utf-8"))
        inferred_dataset_id = dataset_id if dataset_id is not None else profile_file.stem
        proposal = infer_model_from_profile(
            profile_dict, dataset_id=inferred_dataset_id, domain=domain
        )

        validation_results = validate_patch_proposal(proposal)
        proposal["validation_status"] = (
            "valid" if not any(v.severity == "ERROR" for v in validation_results) else "invalid"
        )

        model_path = resolve_model_path(repo_root)
        path = write_patch_proposal(proposal, model_path)
        return json.dumps(
            {
                "proposal_id": proposal["id"],
                "operations_count": len(proposal.get("operations", [])),
                "validation_status": proposal["validation_status"],
                "path": str(path),
                "assumptions": proposal.get("assumptions", []),
                "human_checks": proposal.get("human_checks", []),
            },
            indent=2,
            default=str,
        )

    @mcp.tool()
    def proposal_dry_run(
        proposal_id: str,
    ) -> str:
        """Preview what applying a PatchProposal would do without writing any files."""
        from modelops_core.patching.apply_service import dry_run_patch_proposal

        model_path = resolve_model_path(repo_root)
        result = dry_run_patch_proposal(model_path, proposal_id)
        return json.dumps(
            {
                "proposal_id": result.proposal_id,
                "would_change": result.would_change,
                "operations_preview": result.operations_preview,
                "error": result.error,
                "assumptions": [
                    "This dry-run is a simulation; no canonical files were changed."
                ],
                "human_checks": [
                    "Review the operations preview before applying the proposal.",
                    "Ensure the proposal is accepted through governance before applying.",
                ],
            },
            indent=2,
            default=str,
        )

    @mcp.tool()
    def proposal_impact(
        proposal_id: str,
        max_depth: int = 2,
    ) -> str:
        """Analyze the impact of a PatchProposal's operations."""
        from modelops_core.approval import compute_proposal_risk
        from modelops_core.impact.proposal_impact_service import (
            generate_proposal_impact_report,
        )

        db_path = resolve_generated_path(repo_root) / "modelops.db"
        model_path = resolve_model_path(repo_root)
        proposal_path = model_path / "patch-proposals" / f"{proposal_id}.md"
        if not proposal_path.exists():
            return json.dumps(
                {
                    "error": f"PatchProposal not found: {proposal_id}",
                    "assumptions": [],
                    "human_checks": [
                        "Verify the proposal ID and that the proposal has been written."
                    ],
                },
                indent=2,
                default=str,
            )

        parsed = parse_file(proposal_path)
        fm = parsed.frontmatter or {}
        operations = fm.get("operations", [])

        report = generate_proposal_impact_report(
            db_path, proposal_id, operations, max_depth=max_depth
        )
        risk = compute_proposal_risk(operations, model_path, impact_report=report)

        return json.dumps(
            {
                "proposal_id": report.proposal_id,
                "high_risk": report.high_risk,
                "requires_approval": risk.requires_approval,
                "risk_level": risk.risk_level,
                "risk_reasons": risk.risk_reasons,
                "affected_objects": [
                    {
                        "object_id": obj.object_id,
                        "object_type": obj.object_type,
                        "direction": obj.direction,
                        "depth": obj.depth,
                    }
                    for obj in report.all_affected_objects
                ],
                "assumptions": [
                    "Impact analysis is limited to indexed objects and known references."
                ],
                "human_checks": [
                    "Confirm the affected objects and risk level with stakeholders.",
                    "Verify that downstream consumers are included in the approval process.",
                ],
            },
            indent=2,
            default=str,
        )

    @mcp.tool()
    def create_change_request_tool(
        cr_id: str,
        title: str,
        requester: str | None = None,
        reason: str | None = None,
        requested_change: str | None = None,
        expected_impact: str | None = None,
        affected_objects: list[str] | None = None,
        linked_proposals: list[str] | None = None,
        approvers: list[str] | None = None,
        priority: str | None = None,
    ) -> str:
        """Create a new ChangeRequest canonical file for governance tracking.

        This does NOT modify model objects; it creates a governance artifact
        for human review and approval.
        """
        from modelops_core.change_request import create_change_request

        model_path = resolve_model_path(repo_root)
        try:
            path = create_change_request(
                model_path=model_path,
                cr_id=cr_id,
                title=title,
                requester=requester,
                reason=reason,
                requested_change=requested_change,
                expected_impact=expected_impact,
                affected_objects=affected_objects,
                linked_proposals=linked_proposals,
                approvers=approvers,
                priority=priority,
            )
        except ValueError as exc:
            return json.dumps(
                {
                    "error": str(exc),
                    "assumptions": [],
                    "human_checks": [],
                },
                indent=2,
                default=str,
            )

        return json.dumps(
            {
                "id": cr_id,
                "title": title,
                "path": str(path),
                "assumptions": [
                    "This tool creates a governance artifact only; "
                    "canonical objects are not modified."
                ],
                "human_checks": [
                    "Route the ChangeRequest to the appropriate approvers before implementation.",
                    "Link related PatchProposals or issues to provide full context.",
                ],
            },
            indent=2,
            default=str,
        )

    @mcp.tool()
    def export_model(
        fmt: str = "xlsx",
        business_review: bool = False,
    ) -> str:
        """Export canonical model objects to CSV or XLSX.

        Returns a summary of exported files. The export is read-only and
        does not modify canonical files.
        """
        from modelops_core.exports import export_model_csv, export_model_xlsx

        model_path = resolve_model_path(repo_root)
        if fmt.lower() == "csv":
            paths = export_model_csv(model_path)
            return json.dumps(
                {
                    "format": "csv",
                    "files": [str(p) for p in paths],
                    "assumptions": [
                        "Export is read-only and reflects the current canonical files."
                    ],
                    "human_checks": [
                        "Verify the exported files are suitable for the intended audience.",
                    ],
                },
                indent=2,
                default=str,
            )
        if fmt.lower() == "xlsx":
            path = export_model_xlsx(model_path, business_review=business_review)
            return json.dumps(
                {
                    "format": "xlsx",
                    "file": str(path),
                    "business_review": business_review,
                    "assumptions": [
                        "Export is read-only and reflects the current canonical files."
                    ],
                    "human_checks": [
                        "Verify the exported workbook is suitable for the intended audience.",
                    ],
                },
                indent=2,
                default=str,
            )
        return json.dumps(
            {
                "error": f"Unknown format: {fmt}. Use 'csv' or 'xlsx'.",
                "assumptions": [],
                "human_checks": ["Specify a supported export format: 'csv' or 'xlsx'."],
            },
            indent=2,
            default=str,
        )

    return mcp
