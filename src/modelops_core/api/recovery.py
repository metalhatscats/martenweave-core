"""Stable, machine-readable recovery guidance for local API failures."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


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
OPEN_PARTIAL_RESULTS = RecoveryAction(
    code="OPEN_PARTIAL_RESULTS",
    label="Open the partial assessment results that were generated",
)
VALIDATE_WORKSPACE = RecoveryAction(
    code="VALIDATE_WORKSPACE",
    label="Validate the repository path and configuration",
    command="martenweave doctor --repo .",
)


@dataclass(frozen=True)
class RecoveryState:
    """A structured degraded state with a safe next action for the workbench."""

    code: str
    severity: str  # critical, warning, info
    label: str
    message: str
    actions: list[RecoveryAction]
    more_info: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity,
            "label": self.label,
            "message": self.message,
            "actions": [action.as_dict() for action in self.actions],
            "more_info": self.more_info,
        }


BACKEND_UNAVAILABLE = RecoveryState(
    code="BACKEND_UNAVAILABLE",
    severity="critical",
    label="Local API unreachable",
    message="The Martenweave backend is not responding. Workbench is showing demo data.",
    actions=[RETRY_CONNECTION, INSPECT_READ_ONLY],
)
INVALID_REPOSITORY = RecoveryState(
    code="INVALID_REPOSITORY",
    severity="critical",
    label="Repository is invalid",
    message="The configured path does not look like a Martenweave repository.",
    actions=[VALIDATE_WORKSPACE, INSPECT_READ_ONLY],
)
MISSING_INDEX = RecoveryState(
    code="MISSING_INDEX",
    severity="warning",
    label="Index is missing",
    message="The disposable SQLite index has not been built yet.",
    actions=[BUILD_INDEX, INSPECT_READ_ONLY],
)
STALE_INDEX = RecoveryState(
    code="STALE_INDEX",
    severity="warning",
    label="Index may be stale",
    message="The local index exists but may be out of date with canonical files.",
    actions=[BUILD_INDEX, INSPECT_READ_ONLY],
)
READ_ONLY_REPOSITORY = RecoveryState(
    code="READ_ONLY_REPOSITORY",
    severity="info",
    label="Workspace is read-only",
    message=(
        "Mutations are disabled for this workspace. Search, reports, and inspection still work."
    ),
    actions=[INSPECT_READ_ONLY],
)
INCOMPATIBLE_API = RecoveryState(
    code="INCOMPATIBLE_API",
    severity="critical",
    label="API contract is incompatible",
    message="The running API version is not supported by this Workbench.",
    actions=[RETRY_CONNECTION],
)
BLOCKED_IMPORT = RecoveryState(
    code="BLOCKED_IMPORT",
    severity="warning",
    label="Import blocked by workspace boundary",
    message="The selected file is outside the bound workspace. Choose a file inside the workspace.",
    actions=[CHOOSE_WORKSPACE_FILE],
)
PARTIAL_ASSESSMENT = RecoveryState(
    code="PARTIAL_ASSESSMENT",
    severity="warning",
    label="Assessment completed partially",
    message=(
        "Some assessment stages failed, but generated artifacts are still available for review."
    ),
    actions=[OPEN_PARTIAL_RESULTS, INSPECT_READ_ONLY],
)
INVALID_PROPOSAL = RecoveryState(
    code="INVALID_PROPOSAL",
    severity="warning",
    label="Proposal cannot be applied",
    message="The proposal failed validation or is not approved. Review it before retrying.",
    actions=[REVIEW_PROPOSAL],
)
FAILED_APPLY = RecoveryState(
    code="FAILED_APPLY",
    severity="warning",
    label="Apply failed",
    message="The proposal could not be applied. No canonical files were changed.",
    actions=[REVIEW_PROPOSAL],
)
AI_UNAVAILABLE = RecoveryState(
    code="AI_UNAVAILABLE",
    severity="info",
    label="AI provider is not configured",
    message=(
        "Deterministic workflows still work. To use AI proposals, configure an AI provider."
    ),
    actions=[INSPECT_READ_ONLY],
)
AI_UNAVAILABLE_ACTION = RecoveryAction(
    code="AI_UNAVAILABLE",
    label="AI unavailable — deterministic workflows still work",
)
MUTATION_AUTH_REQUIRED = RecoveryState(
    code="MUTATION_AUTH_REQUIRED",
    severity="warning",
    label="Mutation token required",
    message="Provide the configured X-Martenweave-Token to make changes.",
    actions=[CHECK_MUTATION_TOKEN],
)


def recovery_for_error(status_code: int, detail: object) -> tuple[str, RecoveryAction | None]:
    """Map established API failures to stable codes without changing ``detail`` compatibility."""
    message = str(detail).lower()
    if "index not found" in message or "build-index" in message:
        return "MISSING_INDEX", BUILD_INDEX
    if "bound to its configured workspace" in message:
        return "WORKSPACE_CONFLICT", INSPECT_READ_ONLY
    if "input file must be inside" in message:
        return "BLOCKED_IMPORT", CHOOSE_WORKSPACE_FILE
    if "mutations are disabled" in message:
        return "READ_ONLY_REPOSITORY", INSPECT_READ_ONLY
    if "x-martenweave-token" in message:
        return "MUTATION_AUTH_REQUIRED", CHECK_MUTATION_TOKEN
    if "proposal" in message and ("invalid" in message or "not approved" in message):
        return "INVALID_PROPOSAL", REVIEW_PROPOSAL
    if "apply" in message and status_code == 400:
        return "FAILED_APPLY", REVIEW_PROPOSAL
    if status_code == 404:
        return "NOT_FOUND", None
    if status_code == 400:
        return "INVALID_REQUEST", None
    if status_code == 401:
        return "UNAUTHORIZED", CHECK_MUTATION_TOKEN
    if status_code == 403:
        return "FORBIDDEN", INSPECT_READ_ONLY
    return "API_ERROR", RETRY_CONNECTION


def workspace_recovery_states(
    repo_root: Path,
    indexed: bool,
    read_only: bool,
    ai_configured: bool,
    api_error: RecoveryState | None = None,
) -> list[RecoveryState]:
    """Return the set of degraded states that apply to the current workspace."""
    states: list[RecoveryState] = []
    if api_error is not None:
        states.append(api_error)

    if not repo_root.exists() or not (repo_root / "model").exists():
        states.append(INVALID_REPOSITORY)
        return states

    if not indexed:
        states.append(MISSING_INDEX)
    elif _index_is_stale(repo_root):
        states.append(STALE_INDEX)

    if read_only:
        states.append(READ_ONLY_REPOSITORY)

    if not ai_configured:
        states.append(AI_UNAVAILABLE)

    return states


def _index_is_stale(repo_root: Path) -> bool:
    """Best-effort stale check comparing index mtime to newest canonical file."""

    db_path = repo_root / "generated" / "modelops.db"
    model_path = repo_root / "model"
    if not db_path.exists() or not model_path.exists():
        return False
    try:
        index_mtime = db_path.stat().st_mtime
        newest_model = max(
            (p.stat().st_mtime for p in model_path.rglob("*") if p.is_file()),
            default=index_mtime,
        )
        # Stale if canonical files changed more than 5 minutes after the index.
        return newest_model > index_mtime + 300
    except OSError:
        return False


def assessment_recovery_state(stage_statuses: list[dict[str, Any]]) -> RecoveryState | None:
    """Return a partial-assessment state if any stage failed while others succeeded."""
    if not stage_statuses:
        return None
    statuses = {s.get("status") for s in stage_statuses}
    has_success = "success" in statuses or "skipped" in statuses
    has_failure = "failed" in statuses
    if has_success and has_failure:
        return PARTIAL_ASSESSMENT
    return None
