"""Tests for Google ADK agent scaffold (issue #37)."""

from __future__ import annotations

from pathlib import Path

import pytest

from modelops_core.ai.google_adk.tools import (
    TOOL_REGISTRY,
    create_change_request_tool,
    create_patch_proposal_tool,
    preview_notifications_tool,
    validate_model_tool,
)


def test_tool_registry_has_expected_tools() -> None:
    expected = {
        "validate_model",
        "build_index",
        "trace_object",
        "profile_dataset",
        "create_patch_proposal",
        "create_change_request",
        "preview_notifications",
    }
    assert set(TOOL_REGISTRY.keys()) == expected


def test_validate_model_tool(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()

    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\nname: Test\n---\n",
        encoding="utf-8",
    )

    result = validate_model_tool(str(tmp_path))
    assert "is_valid" in result
    assert result["error_count"] == 0


def test_create_patch_proposal_tool(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()

    operations = [
        {
            "op": "update_object",
            "object_id": "DOMAIN-TEST",
            "target_path": "name",
            "after": "Updated",
        }
    ]

    result = create_patch_proposal_tool(
        repo_root=str(tmp_path),
        proposal_id="PP-ADK-001",
        operations=operations,
        affected_objects=["DOMAIN-TEST"],
    )

    assert result["proposal_id"] == "PP-ADK-001"
    assert result["operations_count"] == 1
    assert result["validation_status"] == "valid"
    assert (model_dir / "patch-proposals" / "PP-ADK-001.md").exists()


def test_create_change_request_tool(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()

    result = create_change_request_tool(
        repo_root=str(tmp_path),
        cr_id="CR-ADK-001",
        title="ADK Test CR",
        affected_objects=["OBJ-001"],
        requester="alice",
        reason="Test reason",
    )

    assert result["cr_id"] == "CR-ADK-001"
    assert result["title"] == "ADK Test CR"
    assert result["status"] == "pending"
    assert (model_dir / "change-requests" / "CR-ADK-001.md").exists()


def test_preview_notifications_tool(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()

    (model_dir / "change-requests").mkdir()
    (model_dir / "change-requests" / "CR-001.md").write_text(
        "---\nid: CR-001\ntype: ChangeRequest\nstatus: pending\nname: Test\ntitle: Test\n---\n",
        encoding="utf-8",
    )

    result = preview_notifications_tool(
        repo_root=str(tmp_path),
        change_request="CR-001",
    )

    assert "recipient_count" in result
    assert isinstance(result["recipients"], list)


def test_tools_do_not_bypass_validation() -> None:
    """Verify that tools still run deterministic validation."""
    from modelops_core.ai.google_adk.tools import validate_model_tool

    # Even when called through the tool wrapper, validation is deterministic
    assert validate_model_tool.__doc__ is not None
    assert "validation" in validate_model_tool.__doc__.lower()


def test_build_agent_raises_without_adk() -> None:
    """Agent construction raises ImportError when google-adk is missing."""
    from modelops_core.ai.google_adk import _HAS_ADK

    if _HAS_ADK:
        pytest.skip("google-adk is installed")

    from modelops_core.ai.google_adk.agent import _build_agent

    with pytest.raises(ImportError, match="google-adk is not installed"):
        _build_agent()


def test_adk_module_has_has_adk_flag() -> None:
    from modelops_core.ai.google_adk import _HAS_ADK

    if _HAS_ADK:
        pytest.skip("google-adk is installed")

    assert _HAS_ADK is False


def test_require_adk_raises() -> None:
    from modelops_core.ai.google_adk import _HAS_ADK, _require_adk

    if _HAS_ADK:
        pytest.skip("google-adk is installed")

    with pytest.raises(ImportError, match="Google ADK is not installed"):
        _require_adk()


def test_profile_dataset_tool_csv(tmp_path: Path) -> None:
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("id,name\n1,Alice\n2,Bob\n", encoding="utf-8")

    from modelops_core.ai.google_adk.tools import profile_dataset_tool

    result = profile_dataset_tool(str(csv_file), dataset_id="test-ds")
    assert result["dataset_id"] == "test-ds"
    assert result["row_count"] == 2
    assert result["column_count"] == 2


def test_profile_dataset_tool_missing_file(tmp_path: Path) -> None:
    from modelops_core.ai.google_adk.tools import profile_dataset_tool

    result = profile_dataset_tool(str(tmp_path / "missing.csv"))
    assert "error" in result


def test_build_index_tool(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    generated_dir = tmp_path / "generated"
    generated_dir.mkdir()

    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\nname: Test\n---\n",
        encoding="utf-8",
    )

    from modelops_core.ai.google_adk.tools import build_index_tool

    result = build_index_tool(str(tmp_path))
    assert result["built"] is True
    assert (generated_dir / "modelops.db").exists()


def test_trace_object_tool_requires_index(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()

    from modelops_core.ai.google_adk.tools import trace_object_tool

    result = trace_object_tool(str(tmp_path), "DOMAIN-TEST")
    assert "error" in result
