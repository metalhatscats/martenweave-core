"""Tests for degraded-mode recovery states and actions."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from modelops_core.api.app import app
from modelops_core.api.recovery import (
    BLOCKED_IMPORT,
    READ_ONLY_REPOSITORY,
    RecoveryAction,
    RecoveryState,
    assessment_recovery_state,
    recovery_for_error,
    workspace_recovery_states,
)

client = TestClient(app)


def test_recovery_action_as_dict() -> None:
    action = RecoveryAction(code="TEST", label="Test action", command="cmd")
    assert action.as_dict() == {
        "code": "TEST",
        "label": "Test action",
        "command": "cmd",
        "requires_confirmation": False,
    }


def test_recovery_state_as_dict() -> None:
    state = RecoveryState(
        code="TEST",
        severity="warning",
        label="Test",
        message="Something is wrong.",
        actions=[RecoveryAction(code="ACT", label="Do it")],
    )
    data = state.as_dict()
    assert data["code"] == "TEST"
    assert data["severity"] == "warning"
    assert data["actions"][0]["code"] == "ACT"


def test_recovery_for_error_maps_missing_index() -> None:
    code, action = recovery_for_error(400, "Index not found. Run build-index first.")
    assert code == "MISSING_INDEX"
    assert action is not None
    assert action.code == "BUILD_INDEX"


def test_recovery_for_error_maps_invalid_proposal() -> None:
    code, action = recovery_for_error(400, "Proposal is invalid or not approved")
    assert code == "INVALID_PROPOSAL"
    assert action is not None
    assert action.code == "REVIEW_PROPOSAL"


def test_recovery_for_error_maps_failed_apply() -> None:
    code, action = recovery_for_error(400, "Apply failed")
    assert code == "FAILED_APPLY"
    assert action is not None
    assert action.code == "REVIEW_PROPOSAL"


def test_workspace_recovery_states_for_missing_index(temp_model_dir: Path) -> None:
    repo_root = temp_model_dir.parent
    states = workspace_recovery_states(
        repo_root,
        indexed=False,
        read_only=False,
        ai_configured=False,
    )
    codes = {s.code for s in states}
    assert "MISSING_INDEX" in codes
    assert "AI_UNAVAILABLE" in codes
    assert "READ_ONLY_REPOSITORY" not in codes


def test_workspace_recovery_states_for_read_only_and_ai_available(
    temp_model_dir: Path,
) -> None:
    repo_root = temp_model_dir.parent
    states = workspace_recovery_states(
        repo_root,
        indexed=True,
        read_only=True,
        ai_configured=True,
    )
    codes = {s.code for s in states}
    assert "READ_ONLY_REPOSITORY" in codes
    assert "AI_UNAVAILABLE" not in codes
    assert "MISSING_INDEX" not in codes


def test_workspace_recovery_states_for_invalid_repo(tmp_path: Path) -> None:
    states = workspace_recovery_states(
        tmp_path / "does-not-exist",
        indexed=False,
        read_only=False,
        ai_configured=True,
    )
    codes = {s.code for s in states}
    assert "INVALID_REPOSITORY" in codes


def test_assessment_recovery_state_partial() -> None:
    stages = [
        {"name": "validation", "status": "success"},
        {"name": "index", "status": "failed"},
    ]
    state = assessment_recovery_state(stages)
    assert state is not None
    assert state.code == "PARTIAL_ASSESSMENT"


def test_assessment_recovery_state_not_partial() -> None:
    stages = [
        {"name": "validation", "status": "success"},
        {"name": "index", "status": "success"},
    ]
    assert assessment_recovery_state(stages) is None


def test_api_recovery_endpoint_returns_states(sample_repo: Path) -> None:
    response = client.get("/api/v1/recovery", params={"repo": str(sample_repo)})
    assert response.status_code == 200
    data = response.json()
    assert "states" in data
    codes = {s["code"] for s in data["states"]}
    assert "AI_UNAVAILABLE" in codes
    for state in data["states"]:
        assert "severity" in state
        assert "label" in state
        assert "message" in state
        assert "actions" in state


def test_api_capabilities_include_recovery_actions(sample_repo: Path) -> None:
    response = client.get("/api/v1/capabilities", params={"repo": str(sample_repo)})
    assert response.status_code == 200
    data = response.json()
    assert "recovery" in data
    codes = {a["code"] for a in data["recovery"]}
    assert "AI_UNAVAILABLE" in codes


def test_block_import_recovery_state() -> None:
    assert BLOCKED_IMPORT.severity == "warning"
    assert BLOCKED_IMPORT.actions[0].code == "CHOOSE_WORKSPACE_FILE"


def test_read_only_repository_allows_inspection() -> None:
    assert READ_ONLY_REPOSITORY.actions[0].code == "INSPECT_READ_ONLY"
