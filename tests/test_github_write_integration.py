"""Tests for GitHub write integration.

All external API calls are mocked. No live GitHub services are contacted.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from modelops_core.connectors.adapter import ConnectorError
from modelops_core.connectors.github import GitHubConnector
from modelops_core.exports.github_publish_service import (
    publish_issue_from_draft,
    publish_pr_from_bundle,
)

# ---------------------------------------------------------------------------
# GitHubConnector tests
# ---------------------------------------------------------------------------


def test_connector_missing_dependency() -> None:
    """Connector raises a clear error when requests is missing."""
    with patch(
        "modelops_core.connectors.github._check_dependencies",
        side_effect=ConnectorError(
            "missing package",
            connector_type="github",
            action="import",
        ),
    ):
        conn = GitHubConnector(token="fake_token")
        with pytest.raises(ConnectorError) as exc_info:
            conn._get_session()
        assert exc_info.value.connector_type == "github"


def test_connector_create_issue() -> None:
    """create_issue sends correct payload to GitHub API."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "number": 42,
        "html_url": "https://github.com/owner/repo/issues/42",
        "title": "Test Issue",
    }
    mock_response.raise_for_status = MagicMock()

    mock_session = MagicMock()
    mock_session.request.return_value = mock_response

    with patch("modelops_core.connectors.github._check_dependencies") as mock_check:
        mock_check.return_value = MagicMock(Session=lambda: mock_session)
        conn = GitHubConnector(token="fake_token")
        result = conn.create_issue(
            repo="owner/repo",
            title="Test Issue",
            body="Issue body",
            labels=["bug", "model"],
        )

    assert result.issue_number == 42
    assert result.issue_url == "https://github.com/owner/repo/issues/42"
    assert result.title == "Test Issue"

    call_args = mock_session.request.call_args
    assert call_args.kwargs["json"]["title"] == "Test Issue"
    assert call_args.kwargs["json"]["labels"] == ["bug", "model"]


def test_connector_create_pull_request() -> None:
    """create_pull_request sends correct payload to GitHub API."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "number": 7,
        "html_url": "https://github.com/owner/repo/pull/7",
        "title": "Test PR",
    }
    mock_response.raise_for_status = MagicMock()

    mock_session = MagicMock()
    mock_session.request.return_value = mock_response

    with patch("modelops_core.connectors.github._check_dependencies") as mock_check:
        mock_check.return_value = MagicMock(Session=lambda: mock_session)
        conn = GitHubConnector(token="fake_token")
        result = conn.create_pull_request(
            repo="owner/repo",
            title="Test PR",
            body="PR body",
            head="feature-branch",
            base="main",
        )

    assert result.pr_number == 7
    assert result.pr_url == "https://github.com/owner/repo/pull/7"

    call_args = mock_session.request.call_args
    assert call_args.kwargs["json"]["head"] == "feature-branch"
    assert call_args.kwargs["json"]["base"] == "main"


def test_connector_fetch_metadata() -> None:
    """fetch_metadata returns ConnectorSourceInfo for a repo."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "full_name": "owner/repo",
        "html_url": "https://github.com/owner/repo",
        "updated_at": "2026-05-20T10:00:00Z",
        "default_branch": "main",
        "open_issues_count": 5,
    }
    mock_response.raise_for_status = MagicMock()

    mock_session = MagicMock()
    mock_session.request.return_value = mock_response

    with patch("modelops_core.connectors.github._check_dependencies") as mock_check:
        mock_check.return_value = MagicMock(Session=lambda: mock_session)
        conn = GitHubConnector(token="fake_token")
        meta = conn.fetch_metadata("owner/repo")

    assert meta.source_id == "owner/repo"
    assert meta.display_name == "owner/repo"
    assert meta.source_type == "github_repo"


def test_connector_no_token() -> None:
    """Connector raises error when no token is available."""
    with patch("modelops_core.connectors.github._check_dependencies") as mock_check:
        mock_check.return_value = MagicMock(Session=MagicMock)
        with patch.dict("os.environ", {}, clear=True):
            conn = GitHubConnector()
            with pytest.raises(ConnectorError) as exc_info:
                conn._get_session()
            assert exc_info.value.connector_type == "github"
            assert exc_info.value.action == "authenticate"


# ---------------------------------------------------------------------------
# Publish service tests
# ---------------------------------------------------------------------------


def test_publish_issue_from_draft_dry_run(tmp_path: Path) -> None:
    """publish_issue_from_draft dry-run returns preview without creating."""
    draft = tmp_path / "issue.md"
    draft.write_text("# Test Issue\n\nThis is a test issue.")

    result = publish_issue_from_draft(
        repo_root=tmp_path,
        github_repo="owner/repo",
        draft_path=draft,
        dry_run=True,
    )

    assert result["dry_run"] is True
    assert result["title"] == "Test Issue"
    assert "owner/repo" == result["repo"]


def test_publish_issue_from_draft_real(tmp_path: Path) -> None:
    """publish_issue_from_draft creates an issue when not dry-run."""
    draft = tmp_path / "issue.md"
    draft.write_text("# Real Issue\n\nBody text.")

    mock_issue_result = MagicMock()
    mock_issue_result.issue_number = 99
    mock_issue_result.issue_url = "https://github.com/owner/repo/issues/99"
    mock_issue_result.title = "Real Issue"

    with patch("modelops_core.exports.github_publish_service.GitHubConnector") as mock_conn_cls:
        mock_conn = MagicMock()
        mock_conn.create_issue.return_value = mock_issue_result
        mock_conn_cls.return_value = mock_conn

        result = publish_issue_from_draft(
            repo_root=tmp_path,
            github_repo="owner/repo",
            draft_path=draft,
            dry_run=False,
        )

    assert result["dry_run"] is False
    assert result["issue_number"] == 99
    assert result["issue_url"] == "https://github.com/owner/repo/issues/99"


def test_publish_pr_from_bundle_dry_run(tmp_path: Path) -> None:
    """publish_pr_from_bundle dry-run returns preview without creating."""
    model_dir = tmp_path / "model"
    model_dir.mkdir(parents=True)
    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\nname: Test Domain\n---\n"
    )

    with patch("modelops_core.exports.github_publish_service.create_git_bundle") as mock_bundle:
        mock_result = MagicMock()
        mock_result.pr_body_path = tmp_path / "PR_BODY.md"
        mock_result.pr_body_path.write_text("PR body here")
        mock_result.commit_message_path = tmp_path / "COMMIT.txt"
        mock_result.commit_message_path.write_text("feat: test commit")
        mock_result.affected_objects = ["DOMAIN-TEST"]
        mock_result.changed_files_dir = tmp_path / "changed"
        mock_result.changed_files_dir.mkdir(exist_ok=True)
        mock_bundle.return_value = mock_result

        result = publish_pr_from_bundle(
            repo_root=tmp_path,
            github_repo="owner/repo",
            proposal_id="PROP-001",
            head_branch="feature/test",
            dry_run=True,
        )

    assert result["dry_run"] is True
    assert result["title"] == "feat: test commit"
    assert result["head"] == "feature/test"
    assert result["base"] == "main"


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------


def test_cli_publish_issue_command_exists() -> None:
    """The publish-issue CLI command is registered."""
    from typer.testing import CliRunner

    from modelops_core.cli import app

    runner = CliRunner()
    result = runner.invoke(app, ["publish-issue", "--help"])
    assert result.exit_code == 0
    assert "issue" in result.output.lower()


def test_cli_publish_pr_command_exists() -> None:
    """The publish-pr CLI command is registered."""
    from typer.testing import CliRunner

    from modelops_core.cli import app

    runner = CliRunner()
    result = runner.invoke(app, ["publish-pr", "--help"])
    assert result.exit_code == 0
    assert "pull request" in result.output.lower() or "pr" in result.output.lower()


def test_cli_publish_issue_dry_run(tmp_path: Path) -> None:
    """publish-issue --dry-run shows preview without external call."""
    from typer.testing import CliRunner

    from modelops_core.cli import app

    draft = tmp_path / "issue.md"
    draft.write_text("# Test Issue\n\nDescription.")

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "publish-issue",
            str(draft),
            "--repo",
            str(tmp_path),
            "--github-repo",
            "owner/repo",
            "--dry-run",
        ],
    )

    assert result.exit_code == 0
    assert "Dry-run preview" in result.output
    assert "Test Issue" in result.output


def test_cli_publish_pr_dry_run(tmp_path: Path) -> None:
    """publish-pr --dry-run shows preview without external call."""
    from typer.testing import CliRunner

    from modelops_core.cli import app

    model_dir = tmp_path / "model"
    model_dir.mkdir(parents=True)
    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\nname: Test Domain\n---\n"
    )

    runner = CliRunner()

    with patch("modelops_core.cli.publish_pr_from_bundle") as mock_publish:
        mock_publish.return_value = {
            "dry_run": True,
            "title": "feat: test",
            "repo": "owner/repo",
            "head": "feature/test",
            "base": "main",
            "affected_objects": ["DOMAIN-TEST"],
            "body": "PR body",
        }
        result = runner.invoke(
            app,
            [
                "publish-pr",
                "PROP-001",
                "--repo",
                str(tmp_path),
                "--github-repo",
                "owner/repo",
                "--head",
                "feature/test",
                "--dry-run",
            ],
        )

    assert result.exit_code == 0
    assert "Dry-run preview" in result.output
