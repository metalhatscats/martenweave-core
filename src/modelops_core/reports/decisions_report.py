"""Decision evidence coverage and category breakdown report."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class DecisionEntry:
    """A single Decision with evidence status."""

    object_id: str
    object_name: str | None
    status: str
    domain: str | None
    evidence: list[str] = field(default_factory=list)
    has_evidence: bool = False


@dataclass
class DomainEvidenceCoverage:
    """Evidence coverage for a single domain."""

    domain: str | None
    total_decisions: int = 0
    decisions_with_evidence: int = 0
    coverage_percent: float = 0.0


@dataclass
class CategoryBreakdown:
    """Count of decisions per category."""

    category: str | None
    count: int = 0


@dataclass
class DecisionsReport:
    """Decision evidence coverage and governance report."""

    evidence_coverage: list[DomainEvidenceCoverage] = field(default_factory=list)
    uncovered_decisions: list[DecisionEntry] = field(default_factory=list)
    deprecated_evidence_decisions: list[DecisionEntry] = field(default_factory=list)
    category_breakdown: list[CategoryBreakdown] = field(default_factory=list)
    total_decisions: int = 0
    total_with_evidence: int = 0
    overall_coverage_percent: float = 0.0


def generate_decisions_report(db_path: Path, _repo_root: Path) -> DecisionsReport:
    """Generate a decisions evidence report from the SQLite index."""
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            "SELECT id, name, status, domain, frontmatter_json FROM objects WHERE type = ?",
            ("Decision",),
        ).fetchall()

        # Also query all Evidence objects for status lookup
        evidence_rows = conn.execute(
            "SELECT id, status FROM objects WHERE type = ?",
            ("Evidence",),
        ).fetchall()
    finally:
        conn.close()

    evidence_status: dict[str, str] = {eid: status for eid, status in evidence_rows}

    decisions: list[DecisionEntry] = []
    for obj_id, obj_name, status, domain, fm_json in rows:
        fm = json.loads(fm_json or "{}")
        raw_evidence = fm.get("evidence")
        evidence_refs: list[str] = []
        if isinstance(raw_evidence, str):
            evidence_refs = [raw_evidence]
        elif isinstance(raw_evidence, list):
            evidence_refs = [str(v) for v in raw_evidence if v]

        entry = DecisionEntry(
            object_id=obj_id,
            object_name=obj_name or None,
            status=str(status or ""),
            domain=domain or None,
            evidence=evidence_refs,
            has_evidence=bool(evidence_refs),
        )
        decisions.append(entry)

    # Domain coverage
    domain_stats: dict[str | None, dict[str, Any]] = {}
    for d in decisions:
        stats = domain_stats.setdefault(d.domain, {"total": 0, "with_evidence": 0})
        stats["total"] += 1
        if d.has_evidence:
            stats["with_evidence"] += 1

    evidence_coverage = []
    for domain, stats in sorted(domain_stats.items(), key=lambda x: x[0] or ""):
        total = stats["total"]
        with_ev = stats["with_evidence"]
        evidence_coverage.append(
            DomainEvidenceCoverage(
                domain=domain,
                total_decisions=total,
                decisions_with_evidence=with_ev,
                coverage_percent=round(with_ev / total * 100, 1) if total else 0.0,
            )
        )

    # Uncovered decisions
    uncovered = [d for d in decisions if not d.has_evidence]

    # Decisions pointing to deprecated evidence
    deprecated: list[DecisionEntry] = []
    for d in decisions:
        for ref in d.evidence:
            ref_status = str(evidence_status.get(ref, "")).lower()
            if ref_status in ("retired", "deprecated"):
                deprecated.append(d)
                break

    # Category breakdown
    category_counts: dict[str | None, int] = {}
    for d in decisions:
        fm = json.loads(
            next(
                (r[4] for r in rows if r[0] == d.object_id),
                "{}",
            )
        )
        category = fm.get("decision_category") or fm.get("category")
        category_counts[category] = category_counts.get(category, 0) + 1

    category_breakdown = [
        CategoryBreakdown(category=cat, count=count)
        for cat, count in sorted(category_counts.items(), key=lambda x: x[0] or "")
    ]

    total_decisions = len(decisions)
    total_with_evidence = sum(1 for d in decisions if d.has_evidence)
    overall_coverage_percent = (
        round(total_with_evidence / total_decisions * 100, 1) if total_decisions else 0.0
    )

    return DecisionsReport(
        evidence_coverage=evidence_coverage,
        uncovered_decisions=uncovered,
        deprecated_evidence_decisions=deprecated,
        category_breakdown=category_breakdown,
        total_decisions=total_decisions,
        total_with_evidence=total_with_evidence,
        overall_coverage_percent=overall_coverage_percent,
    )
