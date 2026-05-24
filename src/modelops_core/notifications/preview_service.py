"""Notification preview service for model workflow actions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from modelops_core.change_request import load_change_request
from modelops_core.repository import parse_file, scan_repository


@dataclass
class NotificationPreviewEntry:
    """A single notification preview row."""

    recipient_id: str
    recipient_role: str
    reason: str
    source_object_id: str | None = None
    source_object_type: str | None = None


def _load_object_registry(model_path: Path) -> dict[str, dict[str, Any]]:
    """Build a quick lookup of all canonical objects by ID."""
    registry: dict[str, dict[str, Any]] = {}
    if not model_path.exists():
        return registry
    for f in scan_repository(model_path):
        parsed = parse_file(f)
        if parsed.frontmatter is None:
            continue
        obj_id = parsed.frontmatter.get("id")
        if isinstance(obj_id, str):
            registry[obj_id] = dict(parsed.frontmatter)
    return registry


def _collect_recipients(
    obj: dict[str, Any],
    cr_obj: dict[str, Any] | None = None,
) -> list[NotificationPreviewEntry]:
    """Extract notification recipients from an object and optional CR."""
    entries: list[NotificationPreviewEntry] = []
    obj_id = obj.get("id")
    obj_type = obj.get("type")

    # Ownership fields
    owner_fields = {
        "business_owner": "business_owner",
        "technical_owner": "technical_owner",
        "data_steward": "data_steward",
        "approver": "approver",
    }
    for field, role in owner_fields.items():
        value = obj.get(field)
        if isinstance(value, str) and value:
            entries.append(
                NotificationPreviewEntry(
                    recipient_id=value,
                    recipient_role=role,
                    reason=f"{field} on {obj_type} '{obj_id}'",
                    source_object_id=obj_id,
                    source_object_type=obj_type,
                )
            )
        elif isinstance(value, list):
            for v in value:
                if isinstance(v, str) and v:
                    entries.append(
                        NotificationPreviewEntry(
                            recipient_id=v,
                            recipient_role=role,
                            reason=f"{field} on {obj_type} '{obj_id}'",
                            source_object_id=obj_id,
                            source_object_type=obj_type,
                        )
                    )

    # Explicit watchers
    watchers = obj.get("watchers")
    if isinstance(watchers, list):
        for w in watchers:
            if isinstance(w, str) and w:
                entries.append(
                    NotificationPreviewEntry(
                        recipient_id=w,
                        recipient_role="watcher",
                        reason=f"explicit watcher on {obj_type} '{obj_id}'",
                        source_object_id=obj_id,
                        source_object_type=obj_type,
                    )
                )

    # ChangeRequest-specific recipients
    if cr_obj is not None:
        cr_id = cr_obj.get("id")
        requester = cr_obj.get("requester")
        if isinstance(requester, str) and requester:
            entries.append(
                NotificationPreviewEntry(
                    recipient_id=requester,
                    recipient_role="requester",
                    reason=f"requester of ChangeRequest '{cr_id}'",
                    source_object_id=cr_id,
                    source_object_type="ChangeRequest",
                )
            )
        cr_approvers = cr_obj.get("approvers")
        if isinstance(cr_approvers, list):
            for a in cr_approvers:
                if isinstance(a, str) and a:
                    entries.append(
                        NotificationPreviewEntry(
                            recipient_id=a,
                            recipient_role="approver",
                            reason=f"approver of ChangeRequest '{cr_id}'",
                            source_object_id=cr_id,
                            source_object_type="ChangeRequest",
                        )
                    )
        cr_watchers = cr_obj.get("watchers")
        if isinstance(cr_watchers, list):
            for w in cr_watchers:
                if isinstance(w, str) and w:
                    entries.append(
                        NotificationPreviewEntry(
                            recipient_id=w,
                            recipient_role="watcher",
                            reason=f"explicit watcher on ChangeRequest '{cr_id}'",
                            source_object_id=cr_id,
                            source_object_type="ChangeRequest",
                        )
                    )

    return entries


def preview_notifications(
    model_path: Path,
    cr_id: str | None = None,
    proposal_id: str | None = None,
) -> list[NotificationPreviewEntry]:
    """Compute notification preview for a ChangeRequest or PatchProposal.

    Args:
        model_path: Path to the model directory.
        cr_id: ChangeRequest ID to preview.
        proposal_id: PatchProposal ID to preview.

    Returns:
        List of notification preview entries with recipients and reasons.
    """
    if cr_id is None and proposal_id is None:
        raise ValueError("Either cr_id or proposal_id must be provided.")

    registry = _load_object_registry(model_path)

    affected_objects: list[str] = []
    cr_obj: dict[str, Any] | None = None

    if cr_id is not None:
        cr_obj = load_change_request(model_path, cr_id)
        if cr_obj is None:
            raise ValueError(f"ChangeRequest not found: {cr_id}")
        affected_objects = cr_obj.get("affected_objects") or []
    elif proposal_id is not None:
        proposal_path = model_path / "patch-proposals" / f"{proposal_id}.md"
        if not proposal_path.exists():
            raise ValueError(f"PatchProposal not found: {proposal_id}")
        parsed = parse_file(proposal_path)
        fm = parsed.frontmatter or {}
        affected_objects = fm.get("affected_objects") or []

    entries: list[NotificationPreviewEntry] = []
    seen: set[tuple[str, str, str | None]] = set()

    for obj_id in affected_objects:
        obj = registry.get(obj_id)
        if obj is None:
            continue
        for entry in _collect_recipients(obj, cr_obj):
            key = (entry.recipient_id, entry.recipient_role, entry.source_object_id)
            if key in seen:
                continue
            seen.add(key)
            entries.append(entry)

    # Also include CR-level recipients even if no affected objects
    if cr_obj is not None:
        for entry in _collect_recipients(cr_obj, cr_obj):
            key = (entry.recipient_id, entry.recipient_role, entry.source_object_id)
            if key in seen:
                continue
            seen.add(key)
            entries.append(entry)

    return sorted(entries, key=lambda e: (e.recipient_id, e.recipient_role))
