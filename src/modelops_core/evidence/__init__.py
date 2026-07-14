"""Evidence ingestion package for notes and validation reports."""

from __future__ import annotations

from modelops_core.evidence.ingest_service import ingest_evidence
from modelops_core.evidence.models import EvidenceFinding, EvidenceFindingKind
from modelops_core.evidence.parsers import (
    parse_csv_report,
    parse_markdown_note,
    parse_xlsx_report,
)

__all__ = [
    "EvidenceFinding",
    "EvidenceFindingKind",
    "ingest_evidence",
    "parse_csv_report",
    "parse_markdown_note",
    "parse_xlsx_report",
]
