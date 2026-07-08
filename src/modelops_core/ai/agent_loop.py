"""Closed-loop agent that turns a modeling goal into a validated PatchProposal."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from modelops_core.ai.patch_proposal_service import build_patch_proposal_from_note
from modelops_core.approval import compute_proposal_risk
from modelops_core.config import (
    load_repo_config,
    resolve_generated_path,
    resolve_model_path,
)
from modelops_core.impact.proposal_impact_service import generate_proposal_impact_report
from modelops_core.patching.patch_proposal_service import write_patch_proposal
from modelops_core.reports.audit_service import (
    AuditEventService,
    create_audit_event,
)
from modelops_core.repository import parse_file, scan_repository
from modelops_core.validation import validate_objects


class AgentLoopStatus(StrEnum):
    """Terminal statuses for the agent loop."""

    VALID_PROPOSAL = "valid_proposal"
    INVALID_PROPOSAL = "invalid_proposal"
    NO_PROGRESS = "no_progress"
    HIGH_RISK = "high_risk"
    FAILED = "failed"


@dataclass
class IterationLogEntry:
    """A single iteration of the propose-validate-refine cycle."""

    iteration: int
    action: str
    proposal_id: str | None = None
    validation_status: str | None = None
    errors: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "iteration": self.iteration,
            "action": self.action,
            "proposal_id": self.proposal_id,
            "validation_status": self.validation_status,
            "errors": self.errors,
        }


@dataclass
class AgentLoopResult:
    """Result of running the agent loop."""

    goal: str
    iterations: int
    final_status: str
    proposal_id: str | None = None
    proposal_path: str | None = None
    validation_status: str = "pending"
    impact: dict[str, Any] = field(default_factory=dict)
    assumptions: list[str] = field(default_factory=list)
    human_checks: list[str] = field(default_factory=list)
    log: list[IterationLogEntry] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal": self.goal,
            "iterations": self.iterations,
            "final_status": self.final_status,
            "proposal_id": self.proposal_id,
            "proposal_path": self.proposal_path,
            "validation_status": self.validation_status,
            "impact": self.impact,
            "assumptions": self.assumptions,
            "human_checks": self.human_checks,
            "log": [entry.to_dict() for entry in self.log],
        }


def _extract_error_key(error: dict[str, Any]) -> tuple[str, ...]:
    """Normalize an error dict for stable comparison."""
    return (
        str(error.get("code", "")),
        str(error.get("message", "")),
        str(error.get("object_id", "") or ""),
    )


def _errors_unchanged(
    previous: list[dict[str, Any]], current: list[dict[str, Any]]
) -> bool:
    """Return True when two error lists are semantically identical."""
    if len(previous) != len(current):
        return False
    prev_keys = sorted(_extract_error_key(e) for e in previous)
    curr_keys = sorted(_extract_error_key(e) for e in current)
    return prev_keys == curr_keys


def _build_refined_note(
    goal: str,
    proposal: dict[str, Any],
    previous_errors: list[dict[str, Any]],
) -> str:
    """Construct a refined note that feeds validation errors back to the proposer."""
    proposal_id = proposal.get("id") if isinstance(proposal, dict) else None
    lines: list[str] = [f"Original goal: {goal}", ""]

    if proposal_id:
        lines.append(f"Previous proposal {proposal_id} had these validation errors:")
    else:
        lines.append("Previous proposal had these validation errors:")

    for error in previous_errors:
        obj_id = error.get("object_id")
        code = error.get("code")
        message = error.get("message", "Unknown error")
        suffix_parts: list[str] = []
        if obj_id:
            suffix_parts.append(f"object: {obj_id}")
        if code:
            suffix_parts.append(f"code: {code}")
        suffix = f" ({', '.join(suffix_parts)})" if suffix_parts else ""
        lines.append(f"- {message}{suffix}")

    lines.append("")
    lines.append("Please fix these errors and regenerate the proposal. Do not change the intent.")

    impact = proposal.get("impact") if isinstance(proposal, dict) else None
    if isinstance(impact, dict) and impact.get("affected_objects_count"):
        count = impact["affected_objects_count"]
        lines.append("")
        lines.append(
            f"The proposal affects {count} downstream objects. "
            "Ensure all affected object IDs are listed and the change is minimal."
        )

    return "\n".join(lines)


def _run_baseline_validation(repo_root: Path) -> dict[str, Any]:
    """Validate the current repository state and return a compact summary."""
    model_path = resolve_model_path(repo_root)
    if not model_path.exists():
        return {
            "is_valid": False,
            "error_count": 0,
            "warning_count": 0,
            "info_count": 0,
            "results": [],
            "message": "Model path does not exist.",
        }

    files = scan_repository(model_path)
    parsed_objects = [parse_file(f) for f in files]
    config = load_repo_config(repo_root)
    enabled_packs = config.enabled_domain_packs if config else None
    summary = validate_objects(parsed_objects, enabled_packs)

    return {
        "is_valid": summary.is_valid,
        "error_count": summary.error_count,
        "warning_count": summary.warning_count,
        "info_count": summary.info_count,
        "results": [r.model_dump() for r in summary.results],
    }


def _emit_iteration_audit(
    repo_root: Path,
    iteration: int,
    proposal_id: str | None,
    action: str,
    validation_status: str | None,
    errors: list[dict[str, Any]] | None,
    dry_run: bool,
) -> None:
    """Write an audit event for every loop iteration."""
    service = AuditEventService(repo_root)
    event = create_audit_event(
        event_type="agent_loop_iteration",
        actor="agent-loop",
        status="success",
        command="agent-loop",
        proposal_id=proposal_id,
        validation_status=validation_status,
        inputs={"iteration": iteration, "action": action, "dry_run": dry_run},
        outputs={
            "errors": errors or [],
            "proposal_id": proposal_id,
        },
        metadata={"dry_run": dry_run},
    )
    service.emit(event)


def run_agent_loop(
    repo_root: Path,
    goal: str,
    max_iterations: int = 5,
    dry_run: bool = False,
) -> AgentLoopResult:
    """Run a closed propose-validate-refine loop for a modeling goal.

    The loop never applies proposals automatically. It stops when a valid,
    low-risk proposal is produced, when it cannot make progress, or when it
    exhausts the iteration budget.
    """
    repo_root = repo_root.resolve()
    model_path = resolve_model_path(repo_root)
    generated_path = resolve_generated_path(repo_root)
    db_path = generated_path / "modelops.db"

    result = AgentLoopResult(goal=goal, iterations=0, final_status=AgentLoopStatus.FAILED)
    log: list[IterationLogEntry] = []

    # Guard against an unusable iteration budget.
    if max_iterations < 1:
        result.human_checks = [
            "max_iterations must be at least 1 to run the agent loop."
        ]
        return result

    # Baseline validation before first propose.
    baseline = _run_baseline_validation(repo_root)
    baseline_errors = [r for r in baseline["results"] if r.get("severity") == "ERROR"]
    _emit_iteration_audit(
        repo_root=repo_root,
        iteration=0,
        proposal_id=None,
        action="baseline_validation",
        validation_status="valid" if baseline["is_valid"] else "invalid",
        errors=baseline_errors,
        dry_run=dry_run,
    )

    if not baseline["is_valid"]:
        result.final_status = AgentLoopStatus.FAILED
        result.validation_status = "invalid"
        result.human_checks = [
            f"Baseline validation failed with {len(baseline_errors)} error(s). "
            "Fix the existing model before running the agent loop."
        ]
        return result

    current_note = goal
    previous_errors: list[dict[str, Any]] | None = None
    final_proposal: dict[str, Any] | None = None
    final_proposal_path: Path | None = None

    for iteration in range(1, max_iterations + 1):
        result.iterations = iteration

        # PROPOSE
        proposal_result = build_patch_proposal_from_note(
            current_note,
            repo_root=repo_root,
            command="agent-loop",
        )
        proposal = proposal_result.get("proposal")

        if proposal is None:
            log.append(
                IterationLogEntry(
                    iteration=iteration,
                    action="propose",
                    proposal_id=None,
                    validation_status="not_generated",
                    errors=[],
                )
            )
            _emit_iteration_audit(
                repo_root=repo_root,
                iteration=iteration,
                proposal_id=None,
                action="propose",
                validation_status="not_generated",
                errors=[],
                dry_run=dry_run,
            )
            result.final_status = AgentLoopStatus.FAILED
            result.validation_status = "not_generated"
            result.assumptions = proposal_result.get("assumptions", [])
            result.human_checks = proposal_result.get("human_checks", [])
            result.log = log
            return result

        proposal_id = proposal.get("id")
        validation_status = proposal.get("validation_status", "invalid")
        validation_results = proposal.get("validation_results", [])
        error_results = [r for r in validation_results if r.get("severity") == "ERROR"]

        log.append(
            IterationLogEntry(
                iteration=iteration,
                action="propose" if iteration == 1 else "refine",
                proposal_id=proposal_id,
                validation_status=validation_status,
                errors=error_results,
            )
        )
        _emit_iteration_audit(
            repo_root=repo_root,
            iteration=iteration,
            proposal_id=proposal_id,
            action="propose" if iteration == 1 else "refine",
            validation_status=validation_status,
            errors=error_results,
            dry_run=dry_run,
        )

        # VALIDATE
        if validation_status == "valid":
            final_proposal = proposal
            result.assumptions = proposal_result.get("assumptions", [])
            result.human_checks = proposal_result.get("human_checks", [])
            break

        # REFINE
        if previous_errors is not None and _errors_unchanged(previous_errors, error_results):
            result.final_status = AgentLoopStatus.NO_PROGRESS
            result.validation_status = "invalid"
            result.proposal_id = proposal_id
            result.assumptions = proposal_result.get("assumptions", [])
            result.human_checks = proposal_result.get("human_checks", [])
            result.log = log
            return result

        previous_errors = error_results
        current_note = _build_refined_note(goal, proposal, error_results)

    else:
        # Exhausted max_iterations without a valid proposal.
        result.final_status = AgentLoopStatus.INVALID_PROPOSAL
        result.validation_status = "invalid"
        if final_proposal is None and proposal is not None:
            # ``proposal`` is the loop variable from the last iteration.
            result.proposal_id = proposal.get("id")
            result.assumptions = proposal_result.get("assumptions", [])
            result.human_checks = proposal_result.get("human_checks", [])
        result.log = log
        return result

    # IMPACT analysis for a valid proposal.
    operations = final_proposal.get("operations", [])
    impact_report = generate_proposal_impact_report(
        db_path=db_path,
        proposal_id=final_proposal.get("id", "unknown"),
        operations=operations,
        max_depth=2,
    )
    risk = compute_proposal_risk(
        operations=operations,
        model_path=model_path,
        impact_report=impact_report,
    )

    result.impact = {
        "high_risk": impact_report.high_risk,
        "requires_approval": risk.requires_approval,
        "affected_objects_count": len(impact_report.affected_object_ids),
        "risk_level": risk.risk_level,
        "risk_reasons": risk.risk_reasons,
    }

    # Audit the terminal impact assessment before returning DONE or HIGH_RISK.
    _emit_iteration_audit(
        repo_root=repo_root,
        iteration=result.iterations,
        proposal_id=final_proposal.get("id"),
        action="impact_analysis",
        validation_status="valid",
        errors=[],
        dry_run=dry_run,
    )

    # Persist the proposal unless this is a dry-run preview.
    if not dry_run:
        final_proposal_path = write_patch_proposal(final_proposal, model_path)
        result.proposal_path = str(final_proposal_path)
    else:
        # Compute the path where the proposal would be written.
        final_proposal_path = model_path / "patch-proposals" / f"{final_proposal['id']}.md"
        result.proposal_path = str(final_proposal_path)

    result.proposal_id = final_proposal.get("id")

    if risk.requires_approval or impact_report.high_risk:
        result.final_status = AgentLoopStatus.HIGH_RISK
        result.validation_status = "valid"
        result.log = log
        return result

    result.final_status = AgentLoopStatus.VALID_PROPOSAL
    result.validation_status = "valid"
    result.log = log
    return result
