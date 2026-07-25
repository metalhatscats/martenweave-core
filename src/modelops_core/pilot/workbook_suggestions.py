"""Governed workbook suggestion records derived from structural scan evidence."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from modelops_core.pilot.structural_scan import WorkbookStructuralManifest

_CONFIDENCE_SCORES = {
    "high": 0.92,
    "medium": 0.74,
    "low": 0.55,
    "unknown": 0.3,
}


@dataclass
class WorkbookSuggestion:
    """A governed workbook interpretation suggestion."""

    suggestion_id: str
    suggestion_type: str
    suggestion_value: str
    confidence_label: str
    confidence_score: float
    evidence: dict[str, Any]
    explanation: str
    deterministic_context: dict[str, Any]
    input_fingerprint: str
    status: str = "unresolved"
    agent_identity: str | None = None
    model_identity: str | None = None


@dataclass
class WorkbookSuggestionSet:
    """Collection of governed workbook suggestions."""

    generator: str
    input_fingerprint: str
    suggestions: list[WorkbookSuggestion] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def counts_by_type(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for suggestion in self.suggestions:
            counts[suggestion.suggestion_type] = counts.get(suggestion.suggestion_type, 0) + 1
        return dict(sorted(counts.items()))

    def counts_by_status(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for suggestion in self.suggestions:
            counts[suggestion.status] = counts.get(suggestion.status, 0) + 1
        return dict(sorted(counts.items()))


def _make_id(input_fingerprint: str, suggestion_type: str, *parts: Any) -> str:
    payload = {
        "input_fingerprint": input_fingerprint,
        "suggestion_type": suggestion_type,
        "parts": [str(part) for part in parts],
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"WSUG-{digest[:16].upper()}"


def _score(label: str) -> float:
    return _CONFIDENCE_SCORES.get(label, _CONFIDENCE_SCORES["unknown"])


def generate_workbook_suggestions(
    manifest: WorkbookStructuralManifest,
) -> WorkbookSuggestionSet:
    """Derive deterministic governed suggestions from a workbook structural manifest."""
    suggestions: list[WorkbookSuggestion] = []
    input_fingerprint = manifest.file_hash

    for sheet in manifest.sheets:
        if sheet.purpose != "unknown":
            confidence_label = sheet.purpose_confidence
            suggestions.append(
                WorkbookSuggestion(
                    suggestion_id=_make_id(
                        input_fingerprint,
                        "sheet_role",
                        sheet.name,
                        sheet.purpose,
                    ),
                    suggestion_type="sheet_role",
                    suggestion_value=sheet.purpose,
                    confidence_label=confidence_label,
                    confidence_score=_score(confidence_label),
                    evidence={
                        "sheet": sheet.name,
                        "probable_header_rows": sheet.probable_header_rows,
                        "table_count": len(sheet.tables),
                    },
                    explanation=(
                        f"Sheet '{sheet.name}' looks like {sheet.purpose.replace('_', ' ')} "
                        "based on sheet name and detected table structure."
                    ),
                    deterministic_context={
                        "scanner_version": manifest.scanner_version,
                        "sheet_fingerprint": sheet.fingerprint,
                    },
                    input_fingerprint=input_fingerprint,
                )
            )

        for table in sheet.tables:
            if table.repeated_header:
                suggestions.append(
                    WorkbookSuggestion(
                        suggestion_id=_make_id(
                            input_fingerprint,
                            "table_split",
                            sheet.name,
                            table.table_id,
                        ),
                        suggestion_type="table_split",
                        suggestion_value="repeated_section",
                        confidence_label="high",
                        confidence_score=_score("high"),
                        evidence={
                            "sheet": sheet.name,
                            "table_id": table.table_id,
                            "header_row": table.header_row,
                            "start_row": table.start_row,
                            "end_row": table.end_row,
                        },
                        explanation=(
                            f"Table section '{table.table_id}' starts after a repeated header "
                            "and should be reviewed as a distinct section."
                        ),
                        deterministic_context={
                            "scanner_version": manifest.scanner_version,
                            "table_fingerprint": table.fingerprint,
                        },
                        input_fingerprint=input_fingerprint,
                    )
                )

            for column in table.detected_columns:
                if column.role == "unknown":
                    continue
                suggestions.append(
                    WorkbookSuggestion(
                        suggestion_id=_make_id(
                            input_fingerprint,
                            "column_role",
                            sheet.name,
                            table.table_id,
                            column.normalized_name,
                            column.role,
                        ),
                        suggestion_type="column_role",
                        suggestion_value=column.role,
                        confidence_label=column.confidence,
                        confidence_score=_score(column.confidence),
                        evidence={
                            "sheet": sheet.name,
                            "table_id": table.table_id,
                            "header_row": table.header_row,
                            "column_name": column.name,
                        },
                        explanation=(
                            f"Column '{column.name}' is a likely {column.role.replace('_', ' ')} "
                            "based on deterministic header matching."
                        ),
                        deterministic_context={
                            "scanner_version": manifest.scanner_version,
                            "table_fingerprint": table.fingerprint,
                        },
                        input_fingerprint=input_fingerprint,
                    )
                )

    return WorkbookSuggestionSet(
        generator="deterministic_rules",
        input_fingerprint=input_fingerprint,
        suggestions=suggestions,
    )


def summarize_workbook_suggestions(
    suggestion_set: WorkbookSuggestionSet,
    *,
    max_items: int = 8,
) -> list[str]:
    """Render a compact metadata-only summary suitable for AI note context."""
    lines: list[str] = []
    for suggestion in suggestion_set.suggestions[:max_items]:
        if suggestion.suggestion_type == "sheet_role":
            lines.append(
                f"- Suggestion {suggestion.suggestion_id}: sheet '{suggestion.evidence['sheet']}' "
                f"role -> {suggestion.suggestion_value} "
                f"({suggestion.confidence_label}, {suggestion.confidence_score:.2f})"
            )
        elif suggestion.suggestion_type == "table_split":
            lines.append(
                f"- Suggestion {suggestion.suggestion_id}: table section "
                f"'{suggestion.evidence['table_id']}' is a repeated section "
                f"({suggestion.confidence_label}, {suggestion.confidence_score:.2f})"
            )
        else:
            lines.append(
                f"- Suggestion {suggestion.suggestion_id}: column "
                f"'{suggestion.evidence['column_name']}' -> {suggestion.suggestion_value} "
                f"({suggestion.confidence_label}, {suggestion.confidence_score:.2f})"
            )
    return lines


def write_workbook_suggestions_json(
    suggestion_set: WorkbookSuggestionSet,
    path: Path,
) -> Path:
    """Write governed workbook suggestions as deterministic JSON."""
    payload = suggestion_set.to_dict()
    payload["summary"] = {
        "suggestion_count": len(suggestion_set.suggestions),
        "counts_by_type": suggestion_set.counts_by_type(),
        "counts_by_status": suggestion_set.counts_by_status(),
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def render_workbook_suggestions_markdown(suggestion_set: WorkbookSuggestionSet) -> str:
    """Render governed workbook suggestions as a reviewable Markdown artifact."""
    lines = [
        "# Workbook suggestions",
        "",
        f"- Generator: `{suggestion_set.generator}`",
        f"- Input fingerprint: `{suggestion_set.input_fingerprint}`",
        f"- Suggestion count: {len(suggestion_set.suggestions)}",
        "",
        "## Summary",
        "",
        "| Type | Count |",
        "|---|---:|",
    ]
    for suggestion_type, count in suggestion_set.counts_by_type().items():
        lines.append(f"| `{suggestion_type}` | {count} |")
    lines.extend(["", "## Suggestions", ""])
    if not suggestion_set.suggestions:
        lines.append("No deterministic workbook suggestions were generated.")
        return "\n".join(lines) + "\n"

    for suggestion in suggestion_set.suggestions:
        lines.append(f"### {suggestion.suggestion_id}")
        lines.append("")
        lines.append(f"- Type: `{suggestion.suggestion_type}`")
        lines.append(f"- Value: `{suggestion.suggestion_value}`")
        lines.append(
            "- Confidence: "
            f"`{suggestion.confidence_label}` ({suggestion.confidence_score:.2f})"
        )
        lines.append(f"- Status: `{suggestion.status}`")
        lines.append(f"- Explanation: {suggestion.explanation}")
        lines.append("- Evidence:")
        for key, value in sorted(suggestion.evidence.items()):
            lines.append(f"  - {key}: `{value}`")
        lines.append("- Deterministic context:")
        for key, value in sorted(suggestion.deterministic_context.items()):
            lines.append(f"  - {key}: `{value}`")
        if suggestion.agent_identity:
            lines.append(f"- Agent identity: `{suggestion.agent_identity}`")
        if suggestion.model_identity:
            lines.append(f"- Model identity: `{suggestion.model_identity}`")
        lines.append("")
    return "\n".join(lines)


def write_workbook_suggestions_markdown(
    suggestion_set: WorkbookSuggestionSet,
    path: Path,
) -> Path:
    """Write governed workbook suggestions as a deterministic Markdown review artifact."""
    path.write_text(render_workbook_suggestions_markdown(suggestion_set), encoding="utf-8")
    return path
