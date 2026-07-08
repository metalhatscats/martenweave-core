"""ProductOwner agentic loop for turning raw inputs into reviewed PatchProposals."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from modelops_core.ai.patch_proposal_service import build_patch_proposal_from_note
from modelops_core.ai.provider_adapter import AIProviderAdapter
from modelops_core.approval.risk_service import compute_proposal_risk
from modelops_core.change_request.service import create_change_request
from modelops_core.config import resolve_generated_path, resolve_model_path
from modelops_core.impact.proposal_impact_service import generate_proposal_impact_report
from modelops_core.issue_draft.draft_service import create_draft_from_proposal, write_draft
from modelops_core.notifications.event_service import emit_notification_event
from modelops_core.notifications.preview_service import preview_notifications
from modelops_core.patching.patch_proposal_service import write_patch_proposal
from modelops_core.patching.patch_validator import validate_patch_proposal

_ID_PATTERN = re.compile(r"[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*")


def _extract_object_ids(text: str) -> list[str]:
    """Extract candidate canonical object IDs from free text."""
    return list({m for m in _ID_PATTERN.findall(text) if len(m) >= 3})


@dataclass
class ProductOwnerInput:
    """Input to the ProductOwner agent."""

    source_type: str
    raw_text: str
    source_id: str | None = None
    repo_root: Path | None = None


@dataclass
class ProductOwnerResult:
    """Result of running the ProductOwner agent loop."""

    success: bool
    iterations: int
    proposal_id: str | None = None
    proposal_path: Path | None = None
    change_request_id: str | None = None
    change_request_path: Path | None = None
    validation_status: str | None = None
    impact_summary: dict[str, Any] = field(default_factory=dict)
    draft_issue_path: Path | None = None
    notification_event_ids: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    human_checks: list[str] = field(default_factory=list)
    error_message: str | None = None


class ProductOwnerAgent:
    """Agent that turns product inputs into validated PatchProposals.

    The agent never writes canonical model objects directly. It produces
    PatchProposal and ChangeRequest artifacts for human review.
    """

    def __init__(
        self,
        adapter: AIProviderAdapter | None = None,
        dry_run: bool = False,
        max_iterations: int = 3,
    ) -> None:
        self.adapter = adapter
        self.dry_run = dry_run
        self.max_iterations = max(max_iterations, 1)

    def run(self, input_data: ProductOwnerInput) -> ProductOwnerResult:
        """Run the product-owner loop."""
        repo_root = input_data.repo_root
        if repo_root is not None:
            repo_root = repo_root.resolve()

        note = self._build_note(input_data)
        if not note.strip():
            return ProductOwnerResult(
                success=False,
                iterations=0,
                error_message="Input contains no actionable text.",
            )

        best_result: dict[str, Any] | None = None
        iterations = 0
        current_note = note
        last_result: dict[str, Any] = {}

        for iteration in range(1, self.max_iterations + 1):
            iterations = iteration
            result = build_patch_proposal_from_note(
                note=current_note,
                adapter=self.adapter,
                repo_root=repo_root,
            )
            last_result = result

            if result.get("proposal") is not None:
                best_result = result
                if result.get("is_safe") is True:
                    break

            # Prepare refinement note for next iteration
            if iteration < self.max_iterations:
                current_note = self._build_refinement_note(note, result, iteration)

        if best_result is None or best_result.get("proposal") is None:
            return ProductOwnerResult(
                success=False,
                iterations=iterations,
                error_message=(
                    "Could not generate a PatchProposal from the input. "
                    "Try configuring an AI provider or adding more detail."
                ),
                assumptions=last_result.get("assumptions", []),
                human_checks=last_result.get("human_checks", []),
            )

        proposal: dict[str, Any] = best_result["proposal"]
        proposal_id = str(proposal.get("id", ""))

        # Re-validate with model path for semantic checks
        model_path = resolve_model_path(repo_root) if repo_root else None
        semantic_results = validate_patch_proposal(proposal, repo_model_path=model_path)
        has_errors = any(r.severity == "ERROR" for r in semantic_results)
        if has_errors:
            validation_status = "invalid"
            proposal["validation_status"] = "invalid"
            proposal["validation_results"] = [r.model_dump() for r in semantic_results]
        else:
            validation_status = "valid"
            proposal["validation_status"] = "valid"
            proposal["validation_results"] = [r.model_dump() for r in semantic_results]

        # Impact analysis
        impact_summary = self._build_impact_summary(proposal, repo_root)

        proposal_path: Path | None = None
        cr_id: str | None = None
        cr_path: Path | None = None
        draft_issue_path: Path | None = None
        notification_event_ids: list[str] = []

        if not self.dry_run and model_path is not None:
            proposal_path = write_patch_proposal(proposal, model_path)

            # Risk-based ChangeRequest creation
            risk = compute_proposal_risk(
                proposal.get("operations", []),
                model_path,
            )
            if (
                risk.requires_approval
                or input_data.source_type == "change_request"
                or validation_status != "valid"
            ):
                cr_id = self._next_change_request_id(model_path)
                cr_path = create_change_request(
                    model_path=model_path,
                    cr_id=cr_id,
                    title=f"Review {proposal_id}",
                    reason=note[:500],
                    requested_change=f"Apply PatchProposal {proposal_id}",
                    affected_objects=proposal.get("affected_objects") or [],
                    linked_proposals=[proposal_id],
                    related_issues=[input_data.source_id]
                    if input_data.source_type == "issue"
                    else None,
                    source_evidence=input_data.source_id,
                )

            # Issue draft
            try:
                generated_path = resolve_generated_path(repo_root) if repo_root else None
                if generated_path is not None:
                    draft = create_draft_from_proposal(
                        model_path=model_path,
                        generated_path=generated_path,
                        proposal_id=proposal_id,
                    )
                    draft_issue_path = write_draft(repo_root, draft)
            except Exception:
                # Draft generation is best-effort
                pass

            # Notifications
            notification_event_ids = self._emit_notifications(
                repo_root=repo_root,
                model_path=model_path,
                proposal_id=proposal_id,
                cr_id=cr_id,
                reason=f"ProductOwner agent created {proposal_id}",
            )

        return ProductOwnerResult(
            success=validation_status == "valid",
            iterations=iterations,
            proposal_id=proposal_id,
            proposal_path=proposal_path,
            change_request_id=cr_id,
            change_request_path=cr_path,
            validation_status=validation_status,
            impact_summary=impact_summary,
            draft_issue_path=draft_issue_path,
            notification_event_ids=notification_event_ids,
            assumptions=best_result.get("assumptions", []),
            human_checks=best_result.get("human_checks", []),
            error_message=None,
        )

    def _build_note(self, input_data: ProductOwnerInput) -> str:
        """Normalize input into a free-text note for proposal generation."""
        source_type = input_data.source_type
        raw_text = input_data.raw_text

        if source_type == "change_request":
            return self._note_from_change_request(raw_text)

        if source_type == "issue":
            return self._strip_frontmatter(raw_text)

        return raw_text

    def _note_from_change_request(self, raw_text: str) -> str:
        """Synthesize a note from ChangeRequest frontmatter text."""
        lines = ["Change request from product owner:"]
        for cr_field in ("reason", "requested_change", "expected_impact"):
            value = self._extract_frontmatter_field(raw_text, cr_field)
            if value:
                lines.append(f"{cr_field}: {value}")
        return "\n".join(lines)

    def _strip_frontmatter(self, raw_text: str) -> str:
        """Return body text from Markdown with YAML frontmatter."""
        stripped = raw_text.strip()
        if not stripped.startswith("---"):
            return raw_text
        parts = stripped.split("---", 2)
        if len(parts) < 3:
            return raw_text
        return parts[2].strip()

    def _extract_frontmatter_field(self, raw_text: str, field: str) -> str | None:
        """Extract a simple top-level field value from YAML frontmatter text."""
        stripped = raw_text.strip()
        if not stripped.startswith("---"):
            return None
        parts = stripped.split("---", 2)
        if len(parts) < 3:
            return None
        try:
            data = yaml.safe_load(parts[1])
            if isinstance(data, dict):
                value = data.get(field)
                if isinstance(value, str):
                    return value
        except yaml.YAMLError:
            pass
        return None

    def _build_refinement_note(
        self, original_note: str, previous_result: dict[str, Any], iteration: int
    ) -> str:
        """Append validation feedback to the note for the next iteration."""
        proposal = previous_result.get("proposal")
        errors: list[str] = []
        if proposal is not None:
            for vr in proposal.get("validation_results", []):
                if vr.get("severity") == "ERROR":
                    errors.append(f"- {vr.get('code')}: {vr.get('message')}")
        if not errors:
            errors.append("- Proposal failed validation; please revise.")

        errors_text = "\n".join(errors)
        return (
            f"{original_note}\n\n"
            f"[Refinement attempt {iteration}]\n"
            "The previous PatchProposal had these validation errors:\n"
            f"{errors_text}\n"
            "Please produce a corrected PatchProposal."
        )

    def _build_impact_summary(
        self, proposal: dict[str, Any], repo_root: Path | None
    ) -> dict[str, Any]:
        """Compute a lightweight impact summary for the result."""
        if repo_root is None:
            return {}

        db_path = resolve_generated_path(repo_root) / "modelops.db"
        if not db_path.exists():
            return {"index_missing": True}

        try:
            report = generate_proposal_impact_report(
                db_path=db_path,
                proposal_id=str(proposal.get("id", "")),
                operations=proposal.get("operations", []),
                max_depth=2,
            )
            return {
                "affected_object_count": len(report.affected_object_ids),
                "affected_object_ids": report.affected_object_ids[:20],
                "high_risk": report.high_risk,
            }
        except Exception as exc:
            return {"error": str(exc)}

    def _next_change_request_id(self, model_path: Path) -> str:
        """Generate the next ChangeRequest ID in sequence."""
        cr_dir = model_path / "change-requests"
        existing: list[int] = []
        if cr_dir.exists():
            for path in cr_dir.glob("CR-*.md"):
                stem = path.stem
                if stem.startswith("CR-"):
                    suffix = stem[3:]
                    if suffix.isdigit():
                        existing.append(int(suffix))
        next_num = max(existing, default=0) + 1
        return f"CR-{next_num:04d}"

    def _emit_notifications(
        self,
        repo_root: Path | None,
        model_path: Path,
        proposal_id: str,
        cr_id: str | None,
        reason: str,
    ) -> list[str]:
        """Emit notification events for reviewers and owners."""
        if repo_root is None:
            return []

        event_ids: list[str] = []
        try:
            recipients = preview_notifications(
                model_path=model_path,
                proposal_id=proposal_id,
            )
        except Exception:
            recipients = []

        for entry in recipients:
            try:
                event = emit_notification_event(
                    repo_root=repo_root,
                    event_type="product_owner_proposal_created",
                    source_type="PatchProposal",
                    source_id=proposal_id,
                    recipient_id=entry.recipient_id,
                    recipient_role=entry.recipient_role,
                    reason=reason,
                    affected_objects=[entry.source_object_id]
                    if entry.source_object_id
                    else [],
                    message_summary=f"Proposal {proposal_id} requires review.",
                )
                event_ids.append(event.event_id)
            except Exception:
                continue

        # Also notify the requester if we created a ChangeRequest
        if cr_id is not None:
            try:
                cr_recipients = preview_notifications(
                    model_path=model_path,
                    cr_id=cr_id,
                )
                for entry in cr_recipients:
                    event = emit_notification_event(
                        repo_root=repo_root,
                        event_type="product_owner_change_request_created",
                        source_type="ChangeRequest",
                        source_id=cr_id,
                        recipient_id=entry.recipient_id,
                        recipient_role=entry.recipient_role,
                        reason=reason,
                        affected_objects=[entry.source_object_id]
                        if entry.source_object_id
                        else [],
                        message_summary=f"ChangeRequest {cr_id} linked to {proposal_id}.",
                    )
                    event_ids.append(event.event_id)
            except Exception:
                pass

        return event_ids
