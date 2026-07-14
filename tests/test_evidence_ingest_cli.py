from pathlib import Path

from typer.testing import CliRunner

from modelops_core.cli import app

runner = CliRunner()


def test_evidence_ingest_cli(sample_repo: Path):
    note = sample_repo.parent / "note.md"
    note.write_text("- Missing owner for ATTR-CUSTOMER-GROUP\n")
    out = sample_repo.parent / "evidence_proposal.md"
    result = runner.invoke(
        app,
        [
            "evidence",
            "ingest",
            "--repo",
            str(sample_repo),
            "--from",
            str(note),
            "--out",
            str(out),
        ],
    )
    assert result.exit_code == 0, result.output
    assert out.exists()


def test_evidence_ingest_cli_from_markdown_fixture(sample_repo: Path):
    note = Path(__file__).parent / "fixtures" / "evidence" / "sample_review_notes.md"
    out = sample_repo.parent / "fixture_evidence_proposal.md"
    result = runner.invoke(
        app,
        [
            "evidence",
            "ingest",
            "--repo",
            str(sample_repo),
            "--from",
            str(note),
            "--out",
            str(out),
        ],
    )
    assert result.exit_code == 0, result.output
    assert out.exists()
    assert "PatchProposal" in result.output
