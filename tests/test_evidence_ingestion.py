from pathlib import Path

from modelops_core.evidence.ingest_service import ingest_evidence


def test_ingest_markdown_note(sample_repo: Path):
    note = sample_repo.parent / "note.md"
    note.write_text(
        "# Review notes\n\n"
        "- Missing owner for ATTR-CUST-SALES-CUSTOMER-GROUP\n"
        "- Consider renaming 'Customer Group' to 'Customer Classification'\n"
    )
    result = ingest_evidence(sample_repo, note, output_format="proposal")
    assert result["type"] == "PatchProposal"
    assert any("owner" in (op.get("target_path") or "").lower() for op in result["operations"])


def test_ingest_csv_validation_report(sample_repo: Path):
    report = sample_repo.parent / "report.csv"
    report.write_text(
        "object_id,severity,message\n"
        "ATTR-CUST-SALES-CUSTOMER-GROUP,error,Missing mapping to FEP\n"
        "DOMAIN-CUSTOMER-BP,warning,No business owner assigned\n"
    )
    result = ingest_evidence(sample_repo, report, output_format="proposal")
    assert result["type"] == "PatchProposal"
    assert len(result["operations"]) >= 1


def test_ingest_sample_csv_report(sample_repo: Path):
    report = Path(__file__).parent / "fixtures" / "evidence" / "sample_validation_report.csv"
    result = ingest_evidence(sample_repo, report, output_format="proposal")
    assert result["type"] == "PatchProposal"
    assert result["source_evidence"] == str(report)
    assert len(result["operations"]) >= 2
