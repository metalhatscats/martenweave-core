"""Tests for the API workspace boundary."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import HTTPException

from modelops_core.api.workspace import (
    _is_safe_path,
    _redact_path,
    create_workspace,
    get_workspace,
    require_write_access,
)


@pytest.fixture
def valid_repo(tmp_path: Path) -> Path:
    """Create a minimal valid repository layout."""
    repo = tmp_path / "repo"
    model_dir = repo / "model"
    model_dir.mkdir(parents=True)
    data_dir = repo / "data"
    data_dir.mkdir(parents=True)
    (repo / "modelops.config.yaml").write_text(
        'schema_version: "1.0"\nworkspace_name: Test Repo\n',
        encoding="utf-8",
    )
    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\nname: Test\n---\n",
        encoding="utf-8",
    )
    return repo


class TestWorkspaceContext:
    def test_create_workspace_binds_paths(self, valid_repo: Path) -> None:
        ws = create_workspace(valid_repo)
        assert ws.repo_root == valid_repo.resolve()
        assert ws.model_path == (valid_repo / "model").resolve()
        assert ws.generated_path == (valid_repo / "generated").resolve()
        assert ws.read_only is False
        assert ws.session_token
        assert len(ws.session_token) == 64  # 32 bytes hex

    def test_create_workspace_read_only(self, valid_repo: Path) -> None:
        ws = create_workspace(valid_repo, read_only=True)
        assert ws.read_only is True

    def test_create_workspace_allows_origins(self, valid_repo: Path) -> None:
        ws = create_workspace(valid_repo, allowed_origins=["http://localhost:3000"])
        assert ws.allowed_origins == ["http://localhost:3000"]

    def test_create_workspace_rejects_missing_model_dir(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "modelops.config.yaml").write_text(
            'schema_version: "1.0"\n', encoding="utf-8"
        )
        with pytest.raises(ValueError, match="model directory not found"):
            create_workspace(repo)


class TestPathSafety:
    def test_safe_path_inside_model_dir(self, valid_repo: Path) -> None:
        ws = create_workspace(valid_repo)
        target = valid_repo / "model" / "DOMAIN-TEST.md"
        assert _is_safe_path(target, ws.allowed_roots) is True

    def test_safe_path_inside_data_dir(self, valid_repo: Path) -> None:
        ws = create_workspace(valid_repo)
        target = valid_repo / "data" / "sample.csv"
        assert _is_safe_path(target, ws.allowed_roots) is True

    def test_traversal_outside_repo_rejected(self, valid_repo: Path) -> None:
        ws = create_workspace(valid_repo)
        target = valid_repo / "model" / ".." / ".." / "etc" / "passwd"
        assert _is_safe_path(target, ws.allowed_roots) is False

    def test_absolute_path_outside_repo_rejected(self, valid_repo: Path) -> None:
        ws = create_workspace(valid_repo)
        target = Path("/etc/passwd")
        assert _is_safe_path(target, ws.allowed_roots) is False

    def test_blocked_segment_rejected(self, valid_repo: Path) -> None:
        ws = create_workspace(valid_repo)
        target = valid_repo / "model" / ".git" / "config"
        assert _is_safe_path(target, ws.allowed_roots) is False

    def test_symlink_outside_repo_rejected(self, valid_repo: Path, tmp_path: Path) -> None:
        ws = create_workspace(valid_repo)
        outside = tmp_path / "outside.txt"
        outside.write_text("secret", encoding="utf-8")
        link = valid_repo / "data" / "link.csv"
        link.symlink_to(outside)
        assert _is_safe_path(link, ws.allowed_roots) is False

    def test_symlink_inside_repo_allowed(self, valid_repo: Path) -> None:
        ws = create_workspace(valid_repo)
        real = valid_repo / "data" / "real.csv"
        real.write_text("x", encoding="utf-8")
        link = valid_repo / "data" / "link.csv"
        link.symlink_to(real)
        assert _is_safe_path(link, ws.allowed_roots) is True


class TestPathRedaction:
    def test_redact_path_inside_repo(self, valid_repo: Path) -> None:
        ws = create_workspace(valid_repo)
        target = valid_repo / "model" / "DOMAIN-TEST.md"
        assert _redact_path(target, ws.repo_root) == "model/DOMAIN-TEST.md"

    def test_redact_path_outside_repo(self, valid_repo: Path) -> None:
        ws = create_workspace(valid_repo)
        target = Path("/etc/passwd")
        assert _redact_path(target, ws.repo_root) == "<outside-workspace>"


class TestDependencies:
    def test_get_workspace_returns_context(self, valid_repo: Path) -> None:
        ws = create_workspace(valid_repo)
        dependency = get_workspace(ws)
        assert dependency() is ws

    def test_require_write_access_blocks_read_only(self, valid_repo: Path) -> None:
        ws = create_workspace(valid_repo, read_only=True)
        dependency = require_write_access(ws)
        with pytest.raises(HTTPException) as exc_info:
            dependency("")
        assert exc_info.value.status_code == 403

    def test_require_write_access_blocks_missing_token(self, valid_repo: Path) -> None:
        ws = create_workspace(valid_repo)
        dependency = require_write_access(ws)
        with pytest.raises(HTTPException) as exc_info:
            dependency("")
        assert exc_info.value.status_code == 403

    def test_require_write_access_blocks_wrong_token(self, valid_repo: Path) -> None:
        ws = create_workspace(valid_repo)
        dependency = require_write_access(ws)
        with pytest.raises(HTTPException) as exc_info:
            dependency("wrong-token")
        assert exc_info.value.status_code == 403

    def test_require_write_access_allows_valid_token(self, valid_repo: Path) -> None:
        ws = create_workspace(valid_repo)
        dependency = require_write_access(ws)
        result = dependency(ws.session_token)
        assert result is ws
