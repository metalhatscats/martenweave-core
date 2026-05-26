"""Tests for the proposal lifecycle report command."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from modelops_core.cli import app
from modelops_core.reports.audit_service import AuditEventService, create_audit_event

runner = CliRunner()


def _write_proposal(tmp_path: Path, proposal_id: str, frontmatter: str) -> None:
    proposals_dir = tmp_path / "model" / "patch-proposals"
    proposals_dir.mkdir(parents=True, exist_ok=True)
    content = f"---\n{frontmatter}---\n\n# Patch Proposal: {proposal_id}\n"
    (proposals_dir / f"{proposal_id}.md").write_text(content, encoding="utf-8")


def test_proposal_report_empty(tmp_path: Path) -> None:
    (tmp_path / "modelops.config.yaml").write_text(
        "model_dir: model\ngenerated_dir: generated\n", encoding="utf-8"
    )
    (tmp_path / "model").mkdir()
    result = runner.invoke(app, ["proposal", "report", "--repo", str(tmp_path), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["proposals_total"] == 0
    assert data["by_status"] == {
        "pending": 0,
        "accepted": 0,
        "rejected": 0,
        "applied": 0,
        "stale": 0,
    }


def test_proposal_report_pending_proposal(tmp_path: Path) -> None:
    (tmp_path / "modelops.config.yaml").write_text(
        "model_dir: model\ngenerated_dir: generated\n", encoding="utf-8"
    )
    _write_proposal(
        tmp_path,
        "PP-001",
        "id: PP-001\ntype: PatchProposal\nstatus: pending_review\n"
        "created_at: 2026-01-01T00:00:00Z\noperations: []\n",
    )
    result = runner.invoke(app, ["proposal", "report", "--repo", str(tmp_path), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["proposals_total"] == 1
    assert data["by_status"]["pending"] == 1
    proposal = data["proposals"][0]
    assert proposal["id"] == "PP-001"
    assert proposal["effective_status"] == "pending_review"


def test_proposal_report_rejected_proposal(tmp_path: Path) -> None:
    (tmp_path / "modelops.config.yaml").write_text(
        "model_dir: model\ngenerated_dir: generated\n", encoding="utf-8"
    )
    _write_proposal(
        tmp_path,
        "PP-002",
        "id: PP-002\ntype: PatchProposal\nstatus: rejected\n"
        "created_at: 2026-01-01T00:00:00Z\n"
        "reviewer: alice\nreviewed_at: 2026-01-02T00:00:00Z\n"
        "rejection_reason: insufficient_evidence\noperations: []\n",
    )
    result = runner.invoke(app, ["proposal", "report", "--repo", str(tmp_path), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["proposals_total"] == 1
    assert data["by_status"]["rejected"] == 1
    assert data["rejected_analysis"]["total_rejected"] == 1
    assert data["rejected_analysis"]["rejection_reason_frequencies"] == {
        "insufficient_evidence": 1
    }
    assert data["rejected_analysis"]["rejected_by_reviewer"] == {"alice": 1}


def test_proposal_report_applied_proposal(tmp_path: Path) -> None:
    (tmp_path / "modelops.config.yaml").write_text(
        "model_dir: model\ngenerated_dir: generated\n", encoding="utf-8"
    )
    _write_proposal(
        tmp_path,
        "PP-003",
        "id: PP-003\ntype: PatchProposal\nstatus: accepted\n"
        "created_at: 2026-01-01T00:00:00Z\n"
        "applied_at: 2026-01-03T00:00:00Z\n"
        "application_status: applied\noperations: []\n",
    )
    result = runner.invoke(app, ["proposal", "report", "--repo", str(tmp_path), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["proposals_total"] == 1
    assert data["by_status"]["applied"] == 1
    proposal = data["proposals"][0]
    assert proposal["effective_status"] == "applied"


def test_proposal_report_stale_by_expires_at(tmp_path: Path) -> None:
    (tmp_path / "modelops.config.yaml").write_text(
        "model_dir: model\ngenerated_dir: generated\n", encoding="utf-8"
    )
    _write_proposal(
        tmp_path,
        "PP-004",
        "id: PP-004\ntype: PatchProposal\nstatus: pending_review\n"
        "created_at: 2026-01-01T00:00:00Z\n"
        "expires_at: 2020-01-01T00:00:00Z\noperations: []\n",
    )
    result = runner.invoke(app, ["proposal", "report", "--repo", str(tmp_path), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["stale_summary"]["stale_count"] == 1
    assert data["by_status"]["stale"] == 1
    assert data["stale_summary"]["oldest_stale_proposal_id"] == "PP-004"


def test_proposal_report_stale_by_days(tmp_path: Path) -> None:
    (tmp_path / "modelops.config.yaml").write_text(
        "model_dir: model\ngenerated_dir: generated\n", encoding="utf-8"
    )
    _write_proposal(
        tmp_path,
        "PP-005",
        "id: PP-005\ntype: PatchProposal\nstatus: pending_review\n"
        "created_at: 2020-01-01T00:00:00Z\noperations: []\n",
    )
    result = runner.invoke(
        app, ["proposal", "report", "--repo", str(tmp_path), "--json", "--stale-days", "1"]
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["stale_summary"]["stale_count"] == 1
    assert data["stale_threshold_days"] == 1


def test_proposal_report_audit_summary(tmp_path: Path) -> None:
    (tmp_path / "modelops.config.yaml").write_text(
        "model_dir: model\ngenerated_dir: generated\n", encoding="utf-8"
    )
    _write_proposal(
        tmp_path,
        "PP-006",
        "id: PP-006\ntype: PatchProposal\nstatus: pending_review\n"
        "created_at: 2026-01-01T00:00:00Z\noperations: []\n",
    )
    service = AuditEventService(tmp_path)
    event = create_audit_event(
        event_type="proposal_validated",
        proposal_id="PP-006",
        actor="system",
        status="success",
    )
    service.emit(event)

    result = runner.invoke(app, ["proposal", "report", "--repo", str(tmp_path), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["audit_summary"]["events_total"] == 1
    assert data["audit_summary"]["proposal_events_total"] == 1
    assert len(data["audit_summary"]["recent_events"]) == 1
    assert data["audit_summary"]["recent_events"][0]["event_type"] == "proposal_validated"


def test_proposal_report_human_output(tmp_path: Path) -> None:
    (tmp_path / "modelops.config.yaml").write_text(
        "model_dir: model\ngenerated_dir: generated\n", encoding="utf-8"
    )
    _write_proposal(
        tmp_path,
        "PP-007",
        "id: PP-007\ntype: PatchProposal\nstatus: pending_review\n"
        "created_at: 2026-01-01T00:00:00Z\noperations: []\n",
    )
    result = runner.invoke(app, ["proposal", "report", "--repo", str(tmp_path)])
    assert result.exit_code == 0
    assert "Proposal Lifecycle Report" in result.output
    assert "PP-007" in result.output
    assert "pending_review" in result.output


def test_proposal_report_does_not_mutate_files(tmp_path: Path) -> None:
    (tmp_path / "modelops.config.yaml").write_text(
        "model_dir: model\ngenerated_dir: generated\n", encoding="utf-8"
    )
    _write_proposal(
        tmp_path,
        "PP-008",
        "id: PP-008\ntype: PatchProposal\nstatus: pending_review\n"
        "created_at: 2026-01-01T00:00:00Z\noperations: []\n",
    )
    proposal_path = tmp_path / "model" / "patch-proposals" / "PP-008.md"
    mtime_before = proposal_path.stat().st_mtime
    result = runner.invoke(app, ["proposal", "report", "--repo", str(tmp_path), "--json"])
    assert result.exit_code == 0
    mtime_after = proposal_path.stat().st_mtime
    assert mtime_before == mtime_after
