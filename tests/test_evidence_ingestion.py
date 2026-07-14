from __future__ import annotations

from pathlib import Path

from modelops_core.evidence.ingest_service import ingest_evidence
from modelops_core.patching.patch_validator import validate_patch_proposal


def test_ingest_markdown_note(sample_repo: Path):
    note = sample_repo.parent / "note.md"
    note.write_text(
        "# Review notes\n\n"
        "- Missing owner for ATTR-CUST-SALES-CUSTOMER-GROUP\n"
        "- Consider renaming ATTR-CUST-SALES-CUSTOMER-GROUP to 'Customer Classification'\n"
    )
    result = ingest_evidence(sample_repo, note, output_format="proposal")
    assert result["type"] == "PatchProposal"
    # Missing owner is surfaced as an Issue, not a placeholder update.
    assert any(
        op.get("object_type") == "Issue"
        and op.get("after", {}).get("issue_type") == "missing_owner"
        for op in result["operations"]
    )
    # Rename suggestion with a quoted target is applied as a name update.
    assert any(
        op.get("op") == "update_object"
        and op.get("target_path") == "name"
        and op.get("after") == "Customer Classification"
        for op in result["operations"]
    )


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


def test_ingest_xlsx_report(sample_repo: Path):
    report = Path(__file__).parent / "fixtures" / "evidence" / "sample_validation_report.xlsx"
    result = ingest_evidence(sample_repo, report, output_format="proposal")
    assert result["type"] == "PatchProposal"
    assert len(result["operations"]) >= 3
    assert any(op.get("object_type") == "Decision" for op in result["operations"])
    assert any(op.get("object_type") == "Issue" for op in result["operations"])
    assert any(
        op.get("op") == "update_object" and op.get("target_path") == "name"
        for op in result["operations"]
    )


def test_validate_generated_proposal_has_no_errors(sample_repo: Path):
    report = Path(__file__).parent / "fixtures" / "evidence" / "sample_validation_report.xlsx"
    result = ingest_evidence(sample_repo, report, output_format="proposal")
    validation_results = validate_patch_proposal(result, repo_model_path=sample_repo)
    errors = [r for r in validation_results if r.severity == "ERROR"]
    assert not errors, [f"{r.code}: {r.message}" for r in errors]
