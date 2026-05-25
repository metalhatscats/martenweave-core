"""Publish model artifacts to GitHub (issues and pull requests)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from modelops_core.bundle.git_bundle_service import create_git_bundle
from modelops_core.connectors.github import GitHubConnector
from modelops_core.reports.audit_service import AuditEventService, create_audit_event


def publish_issue_from_draft(
    repo_root: Path,
    github_repo: str,
    draft_path: Path,
    labels: list[str] | None = None,
    token: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Create a GitHub issue from an issue draft file.

    Args:
        repo_root: Path to the model repository root.
        github_repo: Target GitHub repo in ``owner/name`` format.
        draft_path: Path to the issue draft Markdown file.
        labels: Optional GitHub labels.
        token: Optional GitHub PAT.
        dry_run: If ``True``, only preview the issue without creating it.

    Returns:
        Dict with ``dry_run``, ``title``, ``body``, and ``result`` keys.
    """
    if not draft_path.exists():
        raise FileNotFoundError(f"Draft file not found: {draft_path}")

    draft_text = draft_path.read_text(encoding="utf-8")
    lines = draft_text.splitlines()
    title = lines[0].lstrip("# ").strip() if lines else "Model Issue"
    body = draft_text if len(lines) > 1 else title

    if dry_run:
        return {
            "dry_run": True,
            "title": title,
            "body": body[:500] + ("..." if len(body) > 500 else ""),
            "repo": github_repo,
            "labels": labels or [],
        }

    connector = GitHubConnector(token=token)
    result = connector.create_issue(
        repo=github_repo,
        title=title,
        body=body,
        labels=labels,
    )

    # Audit log
    audit = AuditEventService(repo_root)
    audit.emit(
        create_audit_event(
            event_type="github_issue_created",
            actor="system",
            status="success",
            command="publish-issue",
            changed_files=[str(draft_path)],
            outputs={
                "issue_number": result.issue_number,
                "issue_url": result.issue_url,
                "repo": github_repo,
            },
        )
    )

    return {
        "dry_run": False,
        "title": result.title,
        "issue_number": result.issue_number,
        "issue_url": result.issue_url,
        "repo": github_repo,
    }


def publish_pr_from_bundle(
    repo_root: Path,
    github_repo: str,
    proposal_id: str,
    head_branch: str,
    base_branch: str = "main",
    token: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Create a GitHub pull request from a git bundle.

    Args:
        repo_root: Path to the model repository root.
        github_repo: Target GitHub repo in ``owner/name`` format.
        proposal_id: PatchProposal ID to bundle.
        head_branch: The branch containing changes.
        base_branch: The branch to merge into. Defaults to ``main``.
        token: Optional GitHub PAT.
        dry_run: If ``True``, only preview the PR without creating it.

    Returns:
        Dict with ``dry_run``, ``title``, ``body``, and ``result`` keys.
    """
    bundle = create_git_bundle(repo_root, proposal_id)
    pr_body_path = bundle.pr_body_path
    pr_body = pr_body_path.read_text(encoding="utf-8") if pr_body_path.exists() else ""
    commit_message = (
        bundle.commit_message_path.read_text(encoding="utf-8")
        if bundle.commit_message_path.exists()
        else proposal_id
    )
    title = commit_message.splitlines()[0].strip()

    if dry_run:
        return {
            "dry_run": True,
            "title": title,
            "body": pr_body[:500] + ("..." if len(pr_body) > 500 else ""),
            "head": head_branch,
            "base": base_branch,
            "repo": github_repo,
            "affected_objects": bundle.affected_objects,
        }

    connector = GitHubConnector(token=token)
    result = connector.create_pull_request(
        repo=github_repo,
        title=title,
        body=pr_body,
        head=head_branch,
        base=base_branch,
    )

    # Audit log
    audit = AuditEventService(repo_root)
    audit.emit(
        create_audit_event(
            event_type="github_pr_created",
            actor="system",
            status="success",
            command="publish-pr",
            changed_files=[str(f) for f in bundle.changed_files_dir.iterdir()]
            if bundle.changed_files_dir.exists()
            else [],
            outputs={
                "pr_number": result.pr_number,
                "pr_url": result.pr_url,
                "repo": github_repo,
                "proposal_id": proposal_id,
            },
        )
    )

    return {
        "dry_run": False,
        "title": result.title,
        "pr_number": result.pr_number,
        "pr_url": result.pr_url,
        "head": head_branch,
        "base": base_branch,
        "repo": github_repo,
    }
