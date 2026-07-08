"""Tests for the closed-loop agent command."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from modelops_core.ai.agent_loop import (
    AgentLoopStatus,
    IterationLogEntry,
    _build_refined_note,
    _errors_unchanged,
    run_agent_loop,
)
from modelops_core.ai.provider_adapter import AIProviderError
from modelops_core.approval.risk_service import RiskAssessment
from modelops_core.impact.proposal_impact_service import ProposalImpactReport
from modelops_core.patching.apply_service import DryRunResult


def _valid_proposal(proposal_id: str = "PP-TEST-001") -> dict:
    return {
        "id": proposal_id,
        "type": "PatchProposal",
        "status": "pending_review",
        "operations": [
            {
                "op": "update_object",
                "object_id": "ATTR-TEST",
                "object_type": "Attribute",
                "target_path": "description",
                "after": "Updated description.",
            }
        ],
        "validation_status": "valid",
        "validation_results": [],
    }


def _invalid_proposal(
    proposal_id: str = "PP-TEST-001",
    errors: list[dict] | None = None,
) -> dict:
    return {
        "id": proposal_id,
        "type": "PatchProposal",
        "status": "pending_review",
        "operations": [
            {
                "op": "update_object",
                "object_id": "ATTR-TEST",
                "object_type": "Attribute",
                "target_path": "description",
                "after": "Updated description.",
            }
        ],
        "validation_status": "invalid",
        "validation_results": errors or [
            {
                "severity": "ERROR",
                "code": "PATCH_UPDATE_OBJECT_NOT_FOUND",
                "message": "update_object targets non-existent object 'ATTR-TEST'.",
                "object_id": proposal_id,
            }
        ],
    }


def _make_result(proposal: dict | None, **overrides) -> dict:
    result = {
        "is_safe": proposal is not None and proposal.get("validation_status") == "valid",
        "proposal": proposal,
        "validation": proposal.get("validation_results", []) if proposal else [],
        "markdown": "",
        "assumptions": ["Assumption 1"],
        "human_checks": ["Check 1"],
    }
    result.update(overrides)
    return result


def test_errors_unchanged_true() -> None:
    errors = [
        {"code": "A", "message": "msg", "object_id": "O1"},
        {"code": "B", "message": "msg2", "object_id": "O2"},
    ]
    assert _errors_unchanged(errors, list(reversed(errors))) is True


def test_errors_unchanged_false() -> None:
    prev = [{"code": "A", "message": "msg", "object_id": "O1"}]
    curr = [{"code": "B", "message": "msg", "object_id": "O1"}]
    assert _errors_unchanged(prev, curr) is False


def test_build_refined_note_includes_goal_and_errors() -> None:
    proposal = {"id": "PP-TEST-001"}
    errors = [
        {
            "severity": "ERROR",
            "code": "PATCH_UPDATE_OBJECT_NOT_FOUND",
            "message": "update_object targets non-existent object 'ATTR-TEST'.",
            "object_id": "PP-TEST-001",
        }
    ]
    note = _build_refined_note("Add a new attribute.", proposal, errors)
    assert "Original goal: Add a new attribute." in note
    assert "Previous proposal PP-TEST-001 had these validation errors:" in note
    assert "update_object targets non-existent object 'ATTR-TEST'." in note
    assert "object: PP-TEST-001, code: PATCH_UPDATE_OBJECT_NOT_FOUND" in note


@patch("modelops_core.ai.agent_loop.build_patch_proposal_from_note")
@patch("modelops_core.ai.agent_loop.generate_proposal_impact_report")
@patch("modelops_core.ai.agent_loop.compute_proposal_risk")
def test_agent_loop_valid_goal(
    mock_risk,
    mock_impact,
    mock_build,
    sample_repo: Path,
) -> None:
    proposal = _valid_proposal()
    mock_build.return_value = _make_result(proposal)
    mock_impact.return_value = ProposalImpactReport(
        proposal_id=proposal["id"],
        operation_reports=[],
        high_risk=False,
    )
    mock_risk.return_value = RiskAssessment(
        requires_approval=False,
        risk_level="low",
        risk_reasons=[],
        affected_object_count=0,
        max_impact_depth=0,
    )

    result = run_agent_loop(sample_repo, "Add a new Attribute.", max_iterations=3)

    assert result.final_status == AgentLoopStatus.VALID_PROPOSAL
    assert result.iterations == 1
    assert result.validation_status == "valid"
    assert result.proposal_id == proposal["id"]
    assert result.proposal_path is not None


@patch("modelops_core.ai.agent_loop.build_patch_proposal_from_note")
@patch("modelops_core.ai.agent_loop.generate_proposal_impact_report")
@patch("modelops_core.ai.agent_loop.compute_proposal_risk")
def test_agent_loop_refines_on_validation_error(
    mock_risk,
    mock_impact,
    mock_build,
    sample_repo: Path,
) -> None:
    invalid = _invalid_proposal(errors=[
        {
            "severity": "ERROR",
            "code": "PATCH_UPDATE_OBJECT_NOT_FOUND",
            "message": "Target missing.",
            "object_id": "PP-TEST-001",
        }
    ])
    valid = _valid_proposal()
    mock_build.side_effect = [
        _make_result(invalid),
        _make_result(valid),
    ]
    mock_impact.return_value = ProposalImpactReport(
        proposal_id=valid["id"],
        operation_reports=[],
        high_risk=False,
    )
    mock_risk.return_value = RiskAssessment(
        requires_approval=False,
        risk_level="low",
        risk_reasons=[],
        affected_object_count=0,
        max_impact_depth=0,
    )

    result = run_agent_loop(sample_repo, "Fix the attribute.", max_iterations=3)

    assert result.final_status == AgentLoopStatus.VALID_PROPOSAL
    assert result.iterations == 2
    assert mock_build.call_count == 2
    # Second call should include the validation error from the first iteration.
    second_note = mock_build.call_args_list[1][0][0]
    assert "Target missing." in second_note


@patch("modelops_core.ai.agent_loop.build_patch_proposal_from_note")
def test_agent_loop_max_iterations(
    mock_build,
    sample_repo: Path,
) -> None:
    # Return a different error each iteration so no_progress is not triggered.
    def _make_invalid(iteration: int) -> dict:
        return _invalid_proposal(errors=[
            {
                "severity": "ERROR",
                "code": "PATCH_UPDATE_OBJECT_NOT_FOUND",
                "message": f"Target missing in iteration {iteration}.",
                "object_id": "PP-TEST-001",
            }
        ])

    mock_build.side_effect = [
        _make_result(_make_invalid(1)),
        _make_result(_make_invalid(2)),
        _make_result(_make_invalid(3)),
    ]

    result = run_agent_loop(sample_repo, "Invalid goal.", max_iterations=3)

    assert result.final_status == AgentLoopStatus.INVALID_PROPOSAL
    assert result.iterations == 3
    assert result.validation_status == "invalid"


@patch("modelops_core.ai.agent_loop.build_patch_proposal_from_note")
def test_agent_loop_no_progress(
    mock_build,
    sample_repo: Path,
) -> None:
    error = {
        "severity": "ERROR",
        "code": "PATCH_UPDATE_OBJECT_NOT_FOUND",
        "message": "Target missing.",
        "object_id": "PP-TEST-001",
    }
    invalid = _invalid_proposal(errors=[error])
    mock_build.return_value = _make_result(invalid)

    result = run_agent_loop(sample_repo, "Stuck goal.", max_iterations=3)

    assert result.final_status == AgentLoopStatus.NO_PROGRESS
    assert result.iterations == 2
    assert result.validation_status == "invalid"


@patch("modelops_core.ai.agent_loop.build_patch_proposal_from_note")
@patch("modelops_core.ai.agent_loop.generate_proposal_impact_report")
@patch("modelops_core.ai.agent_loop.compute_proposal_risk")
def test_agent_loop_high_risk(
    mock_risk,
    mock_impact,
    mock_build,
    sample_repo: Path,
) -> None:
    proposal = _valid_proposal()
    mock_build.return_value = _make_result(proposal)
    mock_impact.return_value = ProposalImpactReport(
        proposal_id=proposal["id"],
        operation_reports=[],
        high_risk=True,
    )
    mock_risk.return_value = RiskAssessment(
        requires_approval=True,
        risk_level="high",
        risk_reasons=["Touches high-risk object type."],
        affected_object_count=6,
        max_impact_depth=3,
    )

    result = run_agent_loop(sample_repo, "Add risky mapping.", max_iterations=3)

    assert result.final_status == AgentLoopStatus.HIGH_RISK
    assert result.validation_status == "valid"
    assert result.impact["requires_approval"] is True
    assert result.impact["high_risk"] is True
    assert any("ChangeRequest" in check for check in result.human_checks)


@patch("modelops_core.ai.agent_loop.build_patch_proposal_from_note")
def test_agent_loop_failed(
    mock_build,
    sample_repo: Path,
) -> None:
    mock_build.return_value = _make_result(None)

    result = run_agent_loop(sample_repo, "Generate nothing.", max_iterations=3)

    assert result.final_status == AgentLoopStatus.FAILED
    assert result.validation_status == "not_generated"
    assert result.proposal_id is None


@patch("modelops_core.ai.agent_loop._run_baseline_validation")
@patch("modelops_core.ai.agent_loop.build_patch_proposal_from_note")
def test_agent_loop_blocks_on_invalid_baseline(
    mock_build,
    mock_baseline,
    sample_repo: Path,
) -> None:
    mock_baseline.return_value = {
        "is_valid": False,
        "error_count": 1,
        "warning_count": 0,
        "info_count": 0,
        "results": [
            {
                "severity": "ERROR",
                "code": "BROKEN_REFERENCE",
                "message": "Reference points to missing object.",
                "object_id": "ATTR-TEST",
            }
        ],
        "message": "Baseline validation failed.",
    }

    result = run_agent_loop(sample_repo, "Fix the broken reference.", max_iterations=3)

    assert result.final_status == AgentLoopStatus.FAILED
    assert result.validation_status == "invalid"
    assert result.iterations == 0
    assert any("Baseline validation failed" in check for check in result.human_checks)
    mock_build.assert_not_called()


def test_agent_loop_rejects_zero_max_iterations(sample_repo: Path) -> None:
    result = run_agent_loop(sample_repo, "Do nothing useful.", max_iterations=0)

    assert result.final_status == AgentLoopStatus.FAILED
    assert result.iterations == 0
    assert any("max_iterations must be at least 1" in check for check in result.human_checks)


@patch("modelops_core.ai.agent_loop._emit_iteration_audit")
@patch("modelops_core.ai.agent_loop.build_patch_proposal_from_note")
@patch("modelops_core.ai.agent_loop.generate_proposal_impact_report")
@patch("modelops_core.ai.agent_loop.compute_proposal_risk")
def test_agent_loop_emits_terminal_impact_audit(
    mock_risk,
    mock_impact,
    mock_build,
    mock_audit,
    sample_repo: Path,
) -> None:
    proposal = _valid_proposal()
    mock_build.return_value = _make_result(proposal)
    mock_impact.return_value = ProposalImpactReport(
        proposal_id=proposal["id"],
        operation_reports=[],
        high_risk=False,
    )
    mock_risk.return_value = RiskAssessment(
        requires_approval=False,
        risk_level="low",
        risk_reasons=[],
        affected_object_count=0,
        max_impact_depth=0,
    )

    result = run_agent_loop(sample_repo, "Add a safe attribute.", max_iterations=3)

    assert result.final_status == AgentLoopStatus.VALID_PROPOSAL
    impact_calls = [
        call for call in mock_audit.call_args_list
        if call.kwargs.get("action") == "impact_analysis"
    ]
    assert len(impact_calls) == 1
    assert impact_calls[0].kwargs["proposal_id"] == proposal["id"]
    assert impact_calls[0].kwargs["validation_status"] == "valid"
    assert impact_calls[0].kwargs["status"] == "success"


@patch("modelops_core.ai.agent_loop._emit_iteration_audit")
@patch("modelops_core.ai.agent_loop.build_patch_proposal_from_note")
@patch("modelops_core.ai.agent_loop.generate_proposal_impact_report")
@patch("modelops_core.ai.agent_loop.compute_proposal_risk")
def test_agent_loop_emits_high_risk_audit(
    mock_risk,
    mock_impact,
    mock_build,
    mock_audit,
    sample_repo: Path,
) -> None:
    proposal = _valid_proposal()
    mock_build.return_value = _make_result(proposal)
    mock_impact.return_value = ProposalImpactReport(
        proposal_id=proposal["id"],
        operation_reports=[],
        high_risk=True,
    )
    mock_risk.return_value = RiskAssessment(
        requires_approval=True,
        risk_level="high",
        risk_reasons=["Touches high-risk object type."],
        affected_object_count=6,
        max_impact_depth=3,
    )

    result = run_agent_loop(sample_repo, "Add risky mapping.", max_iterations=3)

    assert result.final_status == AgentLoopStatus.HIGH_RISK
    impact_calls = [
        call for call in mock_audit.call_args_list
        if call.kwargs.get("action") == "impact_analysis"
    ]
    assert len(impact_calls) == 1
    assert impact_calls[0].kwargs["status"] == "high_risk"


def test_iteration_log_entry_to_dict() -> None:
    entry = IterationLogEntry(
        iteration=1,
        action="propose",
        proposal_id="PP-TEST-001",
        validation_status="invalid",
        errors=[{"code": "A"}],
    )
    assert entry.to_dict() == {
        "iteration": 1,
        "action": "propose",
        "proposal_id": "PP-TEST-001",
        "validation_status": "invalid",
        "errors": [{"code": "A"}],
    }


@patch("modelops_core.ai.agent_loop.build_patch_proposal_from_note")
@patch("modelops_core.ai.agent_loop.generate_proposal_impact_report")
@patch("modelops_core.ai.agent_loop.compute_proposal_risk")
@patch("modelops_core.ai.agent_loop.dry_run_patch_proposal")
@patch("modelops_core.ai.agent_loop.write_patch_proposal")
def test_agent_loop_dry_run_returns_operations_preview(
    mock_write,
    mock_dry_run,
    mock_risk,
    mock_impact,
    mock_build,
    sample_repo: Path,
) -> None:
    proposal = _valid_proposal()
    mock_build.return_value = _make_result(proposal)
    mock_impact.return_value = ProposalImpactReport(
        proposal_id=proposal["id"],
        operation_reports=[],
        high_risk=False,
    )
    mock_risk.return_value = RiskAssessment(
        requires_approval=False,
        risk_level="low",
        risk_reasons=[],
        affected_object_count=0,
        max_impact_depth=0,
    )
    mock_write.return_value = sample_repo / "model" / "patch-proposals" / f"{proposal['id']}.md"
    preview = DryRunResult(
        proposal_id=proposal["id"],
        would_change=True,
        operations_preview=[
            {
                "op": "update_object",
                "object_id": "ATTR-TEST",
                "status": "would_update",
            }
        ],
    )
    mock_dry_run.return_value = preview

    result = run_agent_loop(sample_repo, "Dry-run goal.", max_iterations=3, dry_run=True)

    assert result.final_status == AgentLoopStatus.VALID_PROPOSAL
    assert result.proposal_path is not None
    assert result.operations_preview == preview.operations_preview
    mock_dry_run.assert_called_once()


@patch("modelops_core.ai.agent_loop.build_patch_proposal_from_note")
def test_agent_loop_provider_failure(
    mock_build,
    sample_repo: Path,
) -> None:
    mock_build.side_effect = AIProviderError("provider is unavailable")

    result = run_agent_loop(sample_repo, "Generate with failing provider.", max_iterations=3)

    assert result.final_status == AgentLoopStatus.FAILED
    assert result.validation_status == "failed"
    assert result.iterations == 1
    assert any("provider" in check.lower() for check in result.human_checks)
    assert not any("Traceback" in check for check in result.human_checks)


@patch("modelops_core.ai.agent_loop.build_patch_proposal_from_note")
@patch("modelops_core.ai.agent_loop.generate_proposal_impact_report")
def test_agent_loop_impact_failure(
    mock_impact,
    mock_build,
    sample_repo: Path,
) -> None:
    proposal = _valid_proposal()
    mock_build.return_value = _make_result(proposal)
    mock_impact.side_effect = AIProviderError("impact engine failed")

    result = run_agent_loop(sample_repo, "Goal with bad impact.", max_iterations=3)

    assert result.final_status == AgentLoopStatus.FAILED
    assert result.validation_status == "failed"
    assert result.proposal_id == proposal["id"]
    assert any("impact" in check.lower() for check in result.human_checks)


@patch("modelops_core.ai.agent_loop.build_patch_proposal_from_note")
@patch("modelops_core.ai.agent_loop.generate_proposal_impact_report")
@patch("modelops_core.ai.agent_loop.compute_proposal_risk")
@patch("modelops_core.ai.agent_loop.write_patch_proposal")
def test_agent_loop_write_failure(
    mock_write,
    mock_risk,
    mock_impact,
    mock_build,
    sample_repo: Path,
) -> None:
    proposal = _valid_proposal()
    mock_build.return_value = _make_result(proposal)
    mock_impact.return_value = ProposalImpactReport(
        proposal_id=proposal["id"],
        operation_reports=[],
        high_risk=False,
    )
    mock_risk.return_value = RiskAssessment(
        requires_approval=False,
        risk_level="low",
        risk_reasons=[],
        affected_object_count=0,
        max_impact_depth=0,
    )
    mock_write.side_effect = OSError("disk full")

    result = run_agent_loop(sample_repo, "Goal that cannot be written.", max_iterations=3)

    assert result.final_status == AgentLoopStatus.FAILED
    assert result.validation_status == "failed"
    assert result.proposal_id == proposal["id"]
    assert any("write" in check.lower() or "disk" in check.lower() for check in result.human_checks)
