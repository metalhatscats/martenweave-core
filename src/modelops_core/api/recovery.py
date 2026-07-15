"""Stable, machine-readable recovery guidance for local API failures."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RecoveryAction:
    """A safe next action the caller may present without guessing from prose."""

    code: str
    label: str
    command: str | None = None
    requires_confirmation: bool = False

    def as_dict(self) -> dict[str, str | bool | None]:
        return {
            "code": self.code,
            "label": self.label,
            "command": self.command,
            "requires_confirmation": self.requires_confirmation,
        }


BUILD_INDEX = RecoveryAction(
    code="BUILD_INDEX",
    label="Build the disposable local index",
    command="martenweave build-index --repo .",
)
RETRY_CONNECTION = RecoveryAction(code="RETRY_CONNECTION", label="Retry the local API connection")
INSPECT_READ_ONLY = RecoveryAction(
    code="INSPECT_READ_ONLY",
    label="Continue with read-only inspection",
)
CHECK_MUTATION_TOKEN = RecoveryAction(
    code="CHECK_MUTATION_TOKEN",
    label="Provide the configured local mutation token",
)
CHOOSE_WORKSPACE_FILE = RecoveryAction(
    code="CHOOSE_WORKSPACE_FILE",
    label="Choose a dataset inside the bound workspace",
)
REVIEW_PROPOSAL = RecoveryAction(
    code="REVIEW_PROPOSAL",
    label="Review and correct the proposal before applying it",
)


def recovery_for_error(status_code: int, detail: object) -> tuple[str, RecoveryAction | None]:
    """Map established API failures to stable codes without changing ``detail`` compatibility."""
    message = str(detail).lower()
    if "index not found" in message or "build-index" in message:
        return "INDEX_MISSING", BUILD_INDEX
    if "bound to its configured workspace" in message:
        return "WORKSPACE_CONFLICT", INSPECT_READ_ONLY
    if "input file must be inside" in message:
        return "BLOCKED_IMPORT", CHOOSE_WORKSPACE_FILE
    if "mutations are disabled" in message:
        return "READ_ONLY_WORKSPACE", INSPECT_READ_ONLY
    if "x-martenweave-token" in message:
        return "MUTATION_AUTH_REQUIRED", CHECK_MUTATION_TOKEN
    if "proposal" in message and ("invalid" in message or "not approved" in message):
        return "INVALID_PROPOSAL", REVIEW_PROPOSAL
    if status_code == 404:
        return "NOT_FOUND", None
    if status_code == 400:
        return "INVALID_REQUEST", None
    if status_code == 401:
        return "UNAUTHORIZED", CHECK_MUTATION_TOKEN
    if status_code == 403:
        return "FORBIDDEN", INSPECT_READ_ONLY
    return "API_ERROR", RETRY_CONNECTION
