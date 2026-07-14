"""Generate a pilot outcome report from reviewed assessment findings.

Produces a deterministic recommendation (continue, pivot, or
insufficient_evidence) plus Markdown and JSON summaries for design-partner
demos and stakeholder reviews.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from modelops_core import __version__

_ALLOWED_DISPOSITIONS: frozenset[str] = frozenset(
    {"confirmed", "false_positive", "accepted_risk", "deferred", "resolved"}
)


@dataclass
class PilotOutcome:
    """Structured pilot outcome metrics and recommendation."""

    repo_name: str
    generated_at: str
    total_findings: int
    confirmed_findings: int
    false_positives: int
    accepted_risks: int
    deferred: int
    resolved: int
    unreviewed: int
    false_positive_rate: float
    confirmation_rate: float
    recommendation: str
    baselines: dict[str, Any] = field(default_factory=dict)
    unavailable_baselines: list[str] = field(default_factory=list)


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _compute_outcome(
    manifest: dict[str, Any],
    findings_data: dict[str, Any],
    reviews_data: dict[str, Any],
    baselines: dict[str, Any] | None,
) -> PilotOutcome:
    """Count dispositions and derive a deterministic recommendation."""
    findings = findings_data.get("findings", [])
    total = len(findings)

    reviews = reviews_data.get("reviews", {})

    counts: dict[str, int] = {
        "confirmed": 0,
        "false_positive": 0,
        "accepted_risk": 0,
        "deferred": 0,
        "resolved": 0,
    }
    reviewed_ids: set[str] = set()
    for finding_id, record in reviews.items():
        disposition = record.get("disposition", "")
        if disposition in _ALLOWED_DISPOSITIONS:
            reviewed_ids.add(finding_id)
            counts[disposition] = counts.get(disposition, 0) + 1

    unreviewed = total - len(reviewed_ids)

    confirmed = counts["confirmed"]
    false_positives = counts["false_positive"]
    accepted_risks = counts["accepted_risk"]
    deferred = counts["deferred"]
    resolved = counts["resolved"]

    fp_rate = round(false_positives / total, 4) if total > 0 else 0.0
    confirmation_rate = round(confirmed / total, 4) if total > 0 else 0.0

    if total == 0 or not reviews:
        recommendation = "insufficient_evidence"
    elif fp_rate >= 0.5:
        recommendation = "pivot"
    elif confirmation_rate >= 0.5:
        recommendation = "continue"
    else:
        recommendation = "insufficient_evidence"

    effective_baselines = baselines or {}
    unavailable: list[str] = []
    for name, label in (
        ("prior_trace_hours", "prior trace time"),
        ("review_hours", "review effort"),
        ("onboarding_days", "onboarding time"),
    ):
        if name not in effective_baselines:
            unavailable.append(label)

    return PilotOutcome(
        repo_name=manifest.get("repo_name", "Unknown"),
        generated_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        total_findings=total,
        confirmed_findings=confirmed,
        false_positives=false_positives,
        accepted_risks=accepted_risks,
        deferred=deferred,
        resolved=resolved,
        unreviewed=unreviewed,
        false_positive_rate=fp_rate,
        confirmation_rate=confirmation_rate,
        recommendation=recommendation,
        baselines=effective_baselines,
        unavailable_baselines=unavailable,
    )


def generate_pilot_outcome(
    manifest_path: Path,
    baselines: dict[str, Any] | None = None,
) -> PilotOutcome:
    """Generate a pilot outcome from an assessment manifest.

    Args:
        manifest_path: Path to ``manifest.json`` from an assessment run.
        baselines: Optional manual baseline metrics. Supported keys:
            ``prior_trace_hours``, ``review_hours``, ``onboarding_days``.

    Returns:
        ``PilotOutcome`` with counts, rates, and recommendation.
    """
    manifest_path = manifest_path.resolve()
    assessment_dir = manifest_path.parent

    manifest = _load_json(manifest_path)
    findings_data = _load_json(assessment_dir / "findings.json")
    reviews_data = _load_json(assessment_dir / "finding-reviews.json")

    return _compute_outcome(manifest, findings_data, reviews_data, baselines)


def pilot_outcome_to_dict(outcome: PilotOutcome) -> dict[str, Any]:
    """Convert a ``PilotOutcome`` to a JSON-serializable dict."""
    return {
        "tool": "martenweave",
        "version": __version__,
        "repo_name": outcome.repo_name,
        "generated_at": outcome.generated_at,
        "total_findings": outcome.total_findings,
        "confirmed_findings": outcome.confirmed_findings,
        "false_positives": outcome.false_positives,
        "accepted_risks": outcome.accepted_risks,
        "deferred": outcome.deferred,
        "resolved": outcome.resolved,
        "unreviewed": outcome.unreviewed,
        "false_positive_rate": outcome.false_positive_rate,
        "confirmation_rate": outcome.confirmation_rate,
        "recommendation": outcome.recommendation,
        "baselines": outcome.baselines,
        "unavailable_baselines": outcome.unavailable_baselines,
    }


def render_pilot_outcome_markdown(outcome: PilotOutcome) -> str:
    """Render a pilot outcome as Markdown."""
    lines: list[str] = [
        "# Pilot Outcome Report",
        "",
        f"**Repository**: {outcome.repo_name}",
        f"**Generated**: {outcome.generated_at}",
        "",
        "## Finding Review Summary",
        "",
        "| Metric | Count |",
        "|--------|-------|",
        f"| Total findings | {outcome.total_findings} |",
        f"| Confirmed | {outcome.confirmed_findings} |",
        f"| False positives | {outcome.false_positives} |",
        f"| Accepted risks | {outcome.accepted_risks} |",
        f"| Deferred | {outcome.deferred} |",
        f"| Resolved | {outcome.resolved} |",
        f"| Unreviewed | {outcome.unreviewed} |",
        "",
        "## Rates",
        "",
        f"- **Confirmation rate**: {outcome.confirmation_rate:.1%}",
        f"- **False-positive rate**: {outcome.false_positive_rate:.1%}",
        "",
        "## Recommendation",
        "",
        f"**{outcome.recommendation}**",
        "",
    ]

    if outcome.recommendation == "continue":
        lines.append(
            "The majority of findings were confirmed or accepted, indicating the "
            "pilot scope is well-aligned with the migration target. Continue to the "
            "next phase."
        )
    elif outcome.recommendation == "pivot":
        lines.append(
            "A high false-positive rate suggests the current mapping or dataset "
            "assumptions do not match reality. Pivot the pilot scope before "
            "investing further."
        )
    else:
        lines.append(
            "There is not enough reviewed evidence to make a confident pilot "
            "decision. Complete the finding review or provide baseline metrics."
        )
    lines.append("")

    lines.extend(["## Baselines", ""])
    if outcome.baselines:
        for key, value in sorted(outcome.baselines.items()):
            lines.append(f"- **{key}**: {value}")
    else:
        lines.append("_No baseline metrics provided._")

    if outcome.unavailable_baselines:
        lines.append("")
        lines.append("### Unavailable baselines")
        for label in outcome.unavailable_baselines:
            lines.append(f"- {label}: unavailable")
    lines.append("")

    return "\n".join(lines)


def write_pilot_outcome(
    outcome: PilotOutcome,
    out_path: Path,
    json_out_path: Path | None = None,
) -> tuple[Path, Path | None]:
    """Write Markdown and optional JSON outcome reports.

    Args:
        outcome: The outcome to persist.
        out_path: Output path. A sibling ``.md`` and ``.json`` are written.
        json_out_path: Optional explicit JSON output path.

    Returns:
        Tuple of (markdown_path, json_path).
    """
    out_path = out_path.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if out_path.is_dir() or out_path.suffix == "":
        md_path = out_path / "pilot-outcome.md"
    else:
        md_path = out_path.with_suffix(".md")

    md_path.write_text(render_pilot_outcome_markdown(outcome), encoding="utf-8")

    json_path: Path | None = None
    if json_out_path is not None:
        json_path = json_out_path.resolve()
    elif out_path.suffix != "" and not out_path.is_dir():
        json_path = out_path.with_suffix(".json")

    if json_path is not None:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(
            json.dumps(pilot_outcome_to_dict(outcome), indent=2, sort_keys=True),
            encoding="utf-8",
        )

    return md_path, json_path
