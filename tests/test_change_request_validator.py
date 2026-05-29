"""Tests for change request validator."""

from __future__ import annotations

from modelops_core.patching.change_request_validator import validate_change_request
from modelops_core.validation.result import ValidationSeverity


class TestValidateChangeRequest:
    def test_empty_dict_returns_multiple_errors(self) -> None:
        results = validate_change_request({})
        assert len(results) >= 4
        codes = {r.code for r in results}
        assert "CHANGE_REQUEST_ID_INVALID" in codes
        assert "CHANGE_REQUEST_TYPE_MISMATCH" in codes
        assert "CHANGE_REQUEST_STATUS_INVALID" in codes

    def test_no_patch_proposals_warning(self) -> None:
        results = validate_change_request({})
        warning = next((r for r in results if r.code == "CHANGE_REQUEST_NO_PATCH_PROPOSALS"), None)
        assert warning is not None
        assert warning.severity == ValidationSeverity.WARNING

    def test_valid_id_passes(self) -> None:
        results = validate_change_request(
            {"id": "CR-001", "type": "ChangeRequest", "status": "pending"}
        )
        assert not any(r.code == "CHANGE_REQUEST_ID_INVALID" for r in results)

    def test_lowercase_id_fails(self) -> None:
        results = validate_change_request(
            {"id": "cr-123", "type": "ChangeRequest", "status": "pending"}
        )
        error = next(r for r in results if r.code == "CHANGE_REQUEST_ID_INVALID")
        assert error.severity == ValidationSeverity.ERROR

    def test_none_id_fails(self) -> None:
        results = validate_change_request(
            {"id": None, "type": "ChangeRequest", "status": "pending"}
        )
        error = next(r for r in results if r.code == "CHANGE_REQUEST_ID_INVALID")
        assert error.object_id is None

    def test_type_mismatch_fails(self) -> None:
        results = validate_change_request(
            {"id": "CR-001", "type": "PatchProposal", "status": "pending"}
        )
        error = next(r for r in results if r.code == "CHANGE_REQUEST_TYPE_MISMATCH")
        assert error.severity == ValidationSeverity.ERROR

    def test_invalid_status_fails(self) -> None:
        results = validate_change_request(
            {"id": "CR-001", "type": "ChangeRequest", "status": "draft"}
        )
        error = next(r for r in results if r.code == "CHANGE_REQUEST_STATUS_INVALID")
        assert error.severity == ValidationSeverity.ERROR

    def test_invalid_approval_status_fails(self) -> None:
        results = validate_change_request(
            {"id": "CR-001", "type": "ChangeRequest", "status": "pending", "approval_status": "foo"}
        )
        error = next(r for r in results if r.code == "CHANGE_REQUEST_APPROVAL_STATUS_INVALID")
        assert error.severity == ValidationSeverity.ERROR

    def test_invalid_implementation_status_fails(self) -> None:
        results = validate_change_request(
            {
                "id": "CR-001",
                "type": "ChangeRequest",
                "status": "pending",
                "implementation_status": "foo",
            }
        )
        error = next(r for r in results if r.code == "CHANGE_REQUEST_IMPLEMENTATION_STATUS_INVALID")
        assert error.severity == ValidationSeverity.ERROR

    def test_valid_proposal_list_passes(self) -> None:
        results = validate_change_request(
            {
                "id": "CR-001",
                "type": "ChangeRequest",
                "status": "pending",
                "source_patch_proposals": ["PP-001"],
            }
        )
        assert not any(r.code == "CHANGE_REQUEST_NO_PATCH_PROPOSALS" for r in results)

    def test_all_errors_accumulate(self) -> None:
        results = validate_change_request(
            {
                "id": "bad",
                "type": "Wrong",
                "status": "bad",
                "approval_status": "bad",
                "implementation_status": "bad",
            }
        )
        assert len(results) == 6
