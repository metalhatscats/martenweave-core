"""Tests for AI patch proposal service (issue #192)."""

from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

from modelops_core.ai.patch_proposal_service import (
    _extract_object_ids,
    _get_default_adapter,
    build_patch_proposal_from_note,
)
from modelops_core.ai.provider_adapter import (
    AICandidateOutput,
    AIContextBundle,
    AIOutputValidationError,
    NoProviderAdapter,
    ProviderOutputValidator,
)
from modelops_core.index import build_index
from modelops_core.telemetry.ai_usage import AIUsageTelemetryService


class TestBuildPatchProposalFromNote:
    def test_uses_no_provider_adapter_by_default(self, monkeypatch) -> None:
        """Default call with no env var uses NoProviderAdapter scaffold."""
        monkeypatch.delenv("MARTENWEAVE_AI_PROVIDER", raising=False)
        result = build_patch_proposal_from_note("update CUSTOMER GROUP")
        assert result["is_safe"] is True
        assert result["proposal"] is not None
        assert result["proposal"]["id"] == "PP-SCAFFOLD-001"
        assert result["assumptions"]
        assert result["human_checks"]

    def test_customer_group_keyword_triggers_scaffold_operation(self) -> None:
        result = build_patch_proposal_from_note("Update the CUSTOMER GROUP logic")
        assert result["is_safe"] is True
        proposal = result["proposal"]
        assert proposal["id"] == "PP-SCAFFOLD-001"
        assert len(proposal["operations"]) == 1
        assert proposal["operations"][0]["object_id"] == "ATTR-CUST-SALES-CUSTOMER-GROUP"
        assert "ATTR-CUST-SALES-CUSTOMER-GROUP" in proposal["affected_objects"]

    def test_knvv_kdgrp_keyword_triggers_scaffold_operation(self) -> None:
        result = build_patch_proposal_from_note("The KNVV-KDGRP field needs new rules")
        assert result["is_safe"] is True
        proposal = result["proposal"]
        assert proposal["operations"][0]["object_id"] == "ATTR-CUST-SALES-CUSTOMER-GROUP"

    def test_generic_note_explains_missing_provider(self) -> None:
        """NoProviderAdapter returns no candidates for generic notes;
        the service surfaces a provider-configuration hint instead of
        the low-level 'Candidate has no operations' message."""
        result = build_patch_proposal_from_note("This note has no relevant keywords")
        assert result["is_safe"] is False
        assert result["proposal"] is None
        assert any("No AI provider is configured" in a for a in result["assumptions"])
        assert any("Set an AI provider" in h for h in result["human_checks"])

    def test_include_raw_samples_false(self) -> None:
        received: list[AIContextBundle] = []

        class SpyAdapter:
            def generate_candidates(self, context: AIContextBundle) -> list[AICandidateOutput]:
                received.append(context)
                return []

        build_patch_proposal_from_note("test note", include_raw_samples=False, adapter=SpyAdapter())
        assert len(received) == 1
        assert received[0].include_raw_samples is False

    def test_include_raw_samples_true(self) -> None:
        received: list[AIContextBundle] = []

        class SpyAdapter:
            def generate_candidates(self, context: AIContextBundle) -> list[AICandidateOutput]:
                received.append(context)
                return []

        build_patch_proposal_from_note("test note", include_raw_samples=True, adapter=SpyAdapter())
        assert len(received) == 1
        assert received[0].include_raw_samples is True

    def test_custom_adapter_injection(self) -> None:
        class CustomAdapter:
            def generate_candidates(self, context: AIContextBundle) -> list[AICandidateOutput]:
                return [
                    AICandidateOutput(
                        proposal_id="PP-CUSTOM-001",
                        title="Custom Proposal",
                        operations=[
                            {
                                "op": "update_object",
                                "object_id": "DOMAIN-TEST",
                                "object_type": "MasterDataDomain",
                                "target_path": "name",
                                "after": "Updated",
                                "reason": "Test",
                            }
                        ],
                        affected_objects=["DOMAIN-TEST"],
                        assumptions=["Custom assumption"],
                        human_checks=["Custom check"],
                        source_evidence="Custom evidence",
                    )
                ]

        result = build_patch_proposal_from_note("any note", adapter=CustomAdapter())
        assert result["is_safe"] is True
        assert result["proposal"]["id"] == "PP-CUSTOM-001"
        assert result["assumptions"] == ["Custom assumption"]
        assert result["human_checks"] == ["Custom check"]

    def test_no_candidates_returns_safe_false(self, monkeypatch) -> None:
        class EmptyAdapter:
            def generate_candidates(self, context: AIContextBundle) -> list[AICandidateOutput]:
                return []

        monkeypatch.setenv("MARTENWEAVE_AI_PROVIDER", "test")
        result = build_patch_proposal_from_note("any note", adapter=EmptyAdapter())
        assert result["is_safe"] is False
        assert result["proposal"] is None
        assert result["validation"] == []
        assert result["markdown"] == ""
        assert "No candidates generated." in result["assumptions"]
        assert "refine the note" in result["human_checks"][0].lower()

    def test_telemetry_wraps_adapter_when_repo_root_given(self, tmp_path: Path) -> None:
        result = build_patch_proposal_from_note(
            "Update CUSTOMER GROUP",
            repo_root=tmp_path,
        )
        assert result["is_safe"] is True

        service = AIUsageTelemetryService(repo_root=tmp_path)
        events = service.read_events()
        assert len(events) == 1
        assert events[0].provider == "NoProviderAdapter"
        assert events[0].command == "propose-patch"
        assert events[0].status == "success"

    def test_proposal_structure(self) -> None:
        result = build_patch_proposal_from_note("Update CUSTOMER GROUP")
        proposal = result["proposal"]
        assert proposal["type"] == "PatchProposal"
        assert proposal["status"] == "pending_review"
        assert proposal["created_by"] == "no_provider_scaffold"
        assert proposal["generated_by"] == "no_provider_scaffold"
        assert "created_at" in proposal
        assert "validation_status" in proposal
        assert "validation_results" in proposal
        assert isinstance(result["assumptions"], list)
        assert isinstance(result["human_checks"], list)
        assert isinstance(result["validation"], list)

    def test_no_provider_scaffold_marker(self) -> None:
        result = build_patch_proposal_from_note("Update CUSTOMER GROUP")
        proposal = result["proposal"]
        assert proposal["generated_by"] == "no_provider_scaffold"
        assert proposal["created_by"] == "no_provider_scaffold"
        assert any("deterministic scaffold" in a for a in result["assumptions"])

    def test_custom_adapter_does_not_set_scaffold_marker(self) -> None:
        class CustomAdapter:
            def generate_candidates(self, context: AIContextBundle) -> list[AICandidateOutput]:
                return [
                    AICandidateOutput(
                        proposal_id="PP-CUSTOM-001",
                        title="Custom Proposal",
                        operations=[
                            {
                                "op": "update_object",
                                "object_id": "DOMAIN-TEST",
                                "object_type": "MasterDataDomain",
                                "target_path": "name",
                                "after": "Updated",
                                "reason": "Test",
                            }
                        ],
                        affected_objects=["DOMAIN-TEST"],
                        assumptions=["Custom assumption"],
                        human_checks=["Custom check"],
                        source_evidence="Custom evidence",
                    )
                ]

        result = build_patch_proposal_from_note("any note", adapter=CustomAdapter())
        proposal = result["proposal"]
        assert "generated_by" not in proposal
        assert proposal["created_by"] == "ai"


class TestGetDefaultAdapter:
    def test_returns_no_provider_when_env_unset(self, monkeypatch) -> None:
        monkeypatch.delenv("MARTENWEAVE_AI_PROVIDER", raising=False)
        adapter = _get_default_adapter()
        assert isinstance(adapter, NoProviderAdapter)

    def test_returns_kimi_when_env_set(self, monkeypatch) -> None:
        monkeypatch.setenv("MARTENWEAVE_AI_PROVIDER", "kimi")
        monkeypatch.setenv("MOONSHOT_API_KEY", "fake-key")

        with mock.patch(
            "modelops_core.ai.kimi_adapter._post_chat_completion",
            return_value={"choices": []},
        ):
            adapter = _get_default_adapter()
            assert type(adapter).__name__ == "KimiAdapter"


class TestProviderOutputValidator:
    def _valid_candidate(self) -> AICandidateOutput:
        return AICandidateOutput(
            proposal_id="PP-TEST-001",
            title="Valid Candidate",
            operations=[
                {
                    "op": "update_object",
                    "object_id": "DOMAIN-TEST",
                    "object_type": "MasterDataDomain",
                    "target_path": "name",
                    "after": "Updated",
                    "reason": "Test",
                }
            ],
            affected_objects=["DOMAIN-TEST"],
            assumptions=["Assume"],
            human_checks=["Check"],
        )

    def test_validate_valid_candidate(self) -> None:
        validator = ProviderOutputValidator()
        candidate = self._valid_candidate()
        result = validator.validate(candidate)
        assert result["valid"] is True
        assert result["candidate"] == candidate

    def test_validate_missing_proposal_id_raises(self) -> None:
        validator = ProviderOutputValidator()
        candidate = self._valid_candidate()
        candidate.proposal_id = ""
        with pytest.raises(AIOutputValidationError, match="proposal_id"):
            validator.validate(candidate)

    def test_validate_missing_title_raises(self) -> None:
        validator = ProviderOutputValidator()
        candidate = self._valid_candidate()
        candidate.title = ""
        with pytest.raises(AIOutputValidationError, match="title"):
            validator.validate(candidate)

    def test_validate_empty_operations_raises(self) -> None:
        validator = ProviderOutputValidator()
        candidate = self._valid_candidate()
        candidate.operations = []
        with pytest.raises(AIOutputValidationError, match="operations"):
            validator.validate(candidate)

    def test_validate_disallowed_operation_raises(self) -> None:
        validator = ProviderOutputValidator()
        candidate = self._valid_candidate()
        candidate.operations = [
            {
                "op": "delete_object",
                "object_id": "DOMAIN-TEST",
                "object_type": "MasterDataDomain",
            }
        ]
        with pytest.raises(AIOutputValidationError, match="Disallowed operation"):
            validator.validate(candidate)

    def test_to_patch_proposal_builds_valid_dict(self) -> None:
        validator = ProviderOutputValidator()
        candidate = self._valid_candidate()
        result = validator.to_patch_proposal(candidate)
        assert result["is_safe"] is True
        assert result["proposal"]["type"] == "PatchProposal"
        assert result["proposal"]["created_by"] == "ai"
        assert result["proposal"]["id"] == "PP-TEST-001"
        assert result["assumptions"] == ["Assume"]
        assert result["human_checks"] == ["Check"]
        assert isinstance(result["validation"], list)

    def test_to_patch_proposal_sets_is_safe_false_on_invalid_id(self) -> None:
        validator = ProviderOutputValidator()
        candidate = self._valid_candidate()
        candidate.proposal_id = "pp-lowercase"
        result = validator.to_patch_proposal(candidate)
        assert result["is_safe"] is False
        assert result["proposal"]["validation_status"] == "invalid"
        assert any(
            v["code"] == "PATCH_ID_INVALID" for v in result["proposal"]["validation_results"]
        )


class TestExtractObjectIds:
    def test_extracts_single_id(self) -> None:
        assert _extract_object_ids("Update ATTR-CUST-SALES-CUSTOMER-GROUP") == [
            "ATTR-CUST-SALES-CUSTOMER-GROUP"
        ]

    def test_extracts_multiple_ids(self) -> None:
        ids = _extract_object_ids("Link FEP-S4-KNVV-KDGRP to ATTR-CUST-SALES-CUSTOMER-GROUP")
        assert set(ids) == {"FEP-S4-KNVV-KDGRP", "ATTR-CUST-SALES-CUSTOMER-GROUP"}

    def test_no_ids_returns_empty(self) -> None:
        assert _extract_object_ids("Just a generic note") == []


def _build_repo(tmp_path: Path, objects: list[dict]) -> Path:
    model_dir = tmp_path / "model"
    model_dir.mkdir(parents=True, exist_ok=True)
    generated_dir = tmp_path / "generated"
    generated_dir.mkdir(parents=True, exist_ok=True)

    for obj in objects:
        obj_id = obj["id"]
        frontmatter_lines = []
        for k, v in obj.items():
            if isinstance(v, list):
                frontmatter_lines.append(f"{k}:")
                for item in v:
                    frontmatter_lines.append(f"  - {item}")
            else:
                frontmatter_lines.append(f"{k}: {v}")
        frontmatter = "\n".join(frontmatter_lines)
        content = f"---\n{frontmatter}\n---\n\n# {obj_id}\n"
        (model_dir / f"{obj_id}.md").write_text(content, encoding="utf-8")

    db_path = generated_dir / "modelops.db"
    build_index(repo_root=tmp_path, db_path=db_path, allow_invalid=True)
    return tmp_path


class TestBuildPatchProposalFromNoteWithRepoRoot:
    def test_repo_root_builds_context_bundle(self, tmp_path: Path) -> None:
        repo_root = _build_repo(
            tmp_path,
            [
                {"id": "ATTR-1", "type": "Attribute", "status": "active", "name": "A1"},
                {"id": "FEP-1", "type": "FieldEndpoint", "status": "active", "name": "F1"},
            ],
        )

        received: list[AIContextBundle] = []

        class SpyAdapter:
            def generate_candidates(self, context: AIContextBundle) -> list[AICandidateOutput]:
                received.append(context)
                return []

        build_patch_proposal_from_note(
            "Update ATTR-1 and FEP-1",
            adapter=SpyAdapter(),
            repo_root=repo_root,
        )

        assert len(received) == 1
        ctx = received[0]
        assert ctx.repository_context is not None
        assert ctx.repository_context["metadata"]["workflow"] == "proposal-review"
        assert ctx.repository_context["metadata"]["token_budget"] == 4000
        assert len(ctx.repository_context["included_objects"]) >= 2
        ids = {o["object_id"] for o in ctx.repository_context["included_objects"]}
        assert "ATTR-1" in ids
        assert "FEP-1" in ids
        assert ctx.repository_context["validation_summary"] is not None

    def test_repo_root_no_index_empty_context(self, tmp_path: Path) -> None:
        received: list[AIContextBundle] = []

        class SpyAdapter:
            def generate_candidates(self, context: AIContextBundle) -> list[AICandidateOutput]:
                received.append(context)
                return []

        build_patch_proposal_from_note(
            "Update ATTR-1",
            adapter=SpyAdapter(),
            repo_root=tmp_path,
        )

        assert len(received) == 1
        ctx = received[0]
        assert ctx.repository_context is not None
        assert any(
            "not found" in str(w).lower() for w in ctx.repository_context.get("warnings", [])
        )


class TestProposePatchPrivacyCli:
    def test_cli_include_raw_samples_prints_warning(
        self, tmp_path: Path, temp_model_dir: Path
    ) -> None:
        from typer.testing import CliRunner

        from modelops_core.cli import app

        note_file = tmp_path / "note.md"
        note_file.write_text("Update CUSTOMER GROUP", encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "propose-patch",
                "--from",
                str(note_file),
                "--repo",
                str(temp_model_dir.parent),
                "--dry-run",
                "--include-raw-samples",
            ],
        )
        assert result.exit_code == 0
        assert "raw dataset rows may leave the local environment" in result.output

    def test_cli_default_does_not_print_raw_samples_warning(
        self, tmp_path: Path, temp_model_dir: Path
    ) -> None:
        from typer.testing import CliRunner

        from modelops_core.cli import app

        note_file = tmp_path / "note.md"
        note_file.write_text("Update CUSTOMER GROUP", encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "propose-patch",
                "--from",
                str(note_file),
                "--repo",
                str(temp_model_dir.parent),
                "--dry-run",
            ],
        )
        assert result.exit_code == 0
        assert "raw dataset rows may leave the local environment" not in result.output

    def test_cli_dry_run_generic_note_explains_provider_config(
        self, tmp_path: Path, temp_model_dir: Path
    ) -> None:
        """Generic notes with no provider must not show 'Candidate has no operations'."""
        from typer.testing import CliRunner

        from modelops_core.cli import app

        note_file = tmp_path / "note.md"
        note_file.write_text("This note has no relevant keywords", encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "propose-patch",
                "--from",
                str(note_file),
                "--repo",
                str(temp_model_dir.parent),
                "--dry-run",
            ],
        )
        assert result.exit_code == 1
        assert "No proposal generated" in result.output
        assert "No AI provider is configured" in result.output
        assert "Set an AI provider" in result.output
        assert "Candidate has no operations" not in result.output
