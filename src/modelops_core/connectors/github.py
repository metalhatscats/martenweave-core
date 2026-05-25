"""GitHub connector adapter for controlled write operations.

This module requires ``requests``. Install it with::

    pip install modelops_core[github]

or::

    pip install requests
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from modelops_core.connectors.adapter import (
    ConnectorError,
    ConnectorSourceInfo,
)
from modelops_core.schemas.source_registry import SourceEntry


def _check_dependencies() -> Any:
    """Import requests or raise a clear error."""
    try:
        import requests  # type: ignore[import-untyped]

        return requests
    except ImportError as exc:
        raise ConnectorError(
            "GitHub integration requires 'requests'. "
            "Install with: pip install modelops_core[github]",
            connector_type="github",
            action="import",
            details={"missing_package": "requests"},
        ) from exc


@dataclass
class GitHubIssueResult:
    """Result of creating a GitHub issue."""

    issue_number: int
    issue_url: str
    title: str


@dataclass
class GitHubPullRequestResult:
    """Result of creating a GitHub pull request."""

    pr_number: int
    pr_url: str
    title: str


class GitHubConnector:
    """Connector adapter for GitHub write operations.

    All writes are explicit and require user invocation. No automatic
    background operations are performed.
    """

    def __init__(
        self,
        token: str | None = None,
        base_url: str = "https://api.github.com",
    ) -> None:
        self.token = token
        self.base_url = base_url.rstrip("/")
        self._session: Any | None = None

    @property
    def connector_type(self) -> str:
        return "github"

    def _get_session(self) -> Any:
        """Return a cached requests session with auth headers."""
        if self._session is not None:
            return self._session

        requests = _check_dependencies()
        session = requests.Session()
        token = self.token
        if token is None:
            token = self._get_token_from_env()
        if not token:
            raise ConnectorError(
                "No GitHub token provided. Set GITHUB_TOKEN or pass token explicitly.",
                connector_type=self.connector_type,
                action="authenticate",
            )
        session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        )
        self._session = session
        return session

    def _get_token_from_env(self) -> str | None:
        import os

        return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

    def _request(
        self, method: str, endpoint: str, payload: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Make an authenticated request to the GitHub API."""
        session = self._get_session()
        url = f"{self.base_url}{endpoint}"
        try:
            response = session.request(
                method, url, json=payload, timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            raise ConnectorError(
                f"GitHub API request failed: {exc}",
                connector_type=self.connector_type,
                action=method.lower(),
                details={"endpoint": endpoint},
            ) from exc

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def fetch_metadata(self, source_id: str) -> ConnectorSourceInfo:
        """Fetch repository metadata.

        ``source_id`` is expected as ``owner/repo``.
        """
        data = self._request("GET", f"/repos/{source_id}")
        return ConnectorSourceInfo(
            source_id=source_id,
            source_type="github_repo",
            display_name=data.get("full_name", source_id),
            external_reference=data.get("html_url", ""),
            modified_at=data.get("updated_at", ""),
            metadata={
                "default_branch": data.get("default_branch", "main"),
                "open_issues_count": data.get("open_issues_count", 0),
            },
        )

    def list_sources(self, prefix: str = "") -> list[ConnectorSourceInfo]:
        """List repositories for the authenticated user.

        ``prefix`` filters by owner/repo name contains.
        """
        data = self._request("GET", "/user/repos?per_page=100")
        results: list[ConnectorSourceInfo] = []
        for repo in data:
            repo_id = repo.get("full_name", "")
            if prefix and prefix.lower() not in repo_id.lower():
                continue
            results.append(
                ConnectorSourceInfo(
                    source_id=repo_id,
                    source_type="github_repo",
                    display_name=repo.get("name", ""),
                    external_reference=repo.get("html_url", ""),
                    modified_at=repo.get("updated_at", ""),
                )
            )
        return results

    def fetch_content(self, source_id: str) -> bytes:
        """Fetch raw file content from a repository.

        ``source_id`` is expected as ``owner/repo/path/to/file``.
        """
        parts = source_id.split("/", 2)
        if len(parts) != 3:
            raise ConnectorError(
                f"Invalid source_id format: {source_id}. Expected owner/repo/path",
                connector_type=self.connector_type,
                action="fetch_content",
            )
        owner, repo, path = parts
        data = self._request(
            "GET", f"/repos/{owner}/{repo}/contents/{path}"
        )
        import base64

        content = data.get("content", "")
        return base64.b64decode(content)

    def write_content(self, source_id: str, content: bytes) -> bool:
        """Write content to a GitHub repository file.

        Not supported in this minimal connector.
        """
        raise ConnectorError(
            "GitHub file write is not supported by this connector. "
            "Use git operations for file changes.",
            connector_type=self.connector_type,
            action="write_content",
        )

    def to_source_entry(self, source_id: str) -> SourceEntry:
        """Produce a SourceEntry for the source registry."""
        meta = self.fetch_metadata(source_id)
        return SourceEntry(
            source_id=source_id,
            source_type=self.connector_type,
            display_name=meta.display_name,
            file_path=meta.external_reference,
            registered_at=datetime.now(UTC).isoformat(),
            last_seen_at=datetime.now(UTC).isoformat(),
            status="ok",
            metadata={
                "default_branch": meta.metadata.get("default_branch")
                if meta.metadata
                else None,
            },
        )

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def create_issue(
        self,
        repo: str,
        title: str,
        body: str,
        labels: list[str] | None = None,
    ) -> GitHubIssueResult:
        """Create a GitHub issue in the specified repository.

        Args:
            repo: Repository in ``owner/name`` format.
            title: Issue title.
            body: Issue body (Markdown).
            labels: Optional list of label names.

        Returns:
            ``GitHubIssueResult`` with issue number and URL.
        """
        payload: dict[str, Any] = {"title": title, "body": body}
        if labels:
            payload["labels"] = labels

        data = self._request("POST", f"/repos/{repo}/issues", payload)
        return GitHubIssueResult(
            issue_number=data.get("number", 0),
            issue_url=data.get("html_url", ""),
            title=data.get("title", title),
        )

    def create_pull_request(
        self,
        repo: str,
        title: str,
        body: str,
        head: str,
        base: str = "main",
    ) -> GitHubPullRequestResult:
        """Create a GitHub pull request in the specified repository.

        Args:
            repo: Repository in ``owner/name`` format.
            title: PR title.
            body: PR body (Markdown).
            head: The branch containing changes.
            base: The branch to merge into. Defaults to ``main``.

        Returns:
            ``GitHubPullRequestResult`` with PR number and URL.
        """
        payload = {
            "title": title,
            "body": body,
            "head": head,
            "base": base,
        }
        data = self._request("POST", f"/repos/{repo}/pulls", payload)
        return GitHubPullRequestResult(
            pr_number=data.get("number", 0),
            pr_url=data.get("html_url", ""),
            title=data.get("title", title),
        )
