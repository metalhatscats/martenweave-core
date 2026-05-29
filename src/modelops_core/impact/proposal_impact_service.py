"""Impact analysis for PatchProposal operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from modelops_core.impact.impact_report import AffectedObject, ImpactReport
from modelops_core.impact.impact_service import generate_impact_report
from modelops_core.schemas.registry import get_relationship_fields


@dataclass
class ProposalImpactReport:
    """Combined impact report for all operations in a PatchProposal."""

    proposal_id: str
    operation_reports: list[OperationImpactReport] = field(default_factory=list)
    high_risk: bool = False

    @property
    def all_affected_objects(self) -> list[AffectedObject]:
        """Deduplicated list of all affected objects across operations."""
        seen: set[str] = set()
        result: list[AffectedObject] = []
        for report in self.operation_reports:
            for obj in report.impact_report.affected_objects:
                if obj.object_id not in seen:
                    seen.add(obj.object_id)
                    result.append(obj)
        return result

    @property
    def affected_object_ids(self) -> list[str]:
        return sorted({obj.object_id for obj in self.all_affected_objects})


@dataclass
class OperationImpactReport:
    """Impact report for a single proposal operation."""

    op: str
    object_id: str
    object_type: str | None
    impact_report: ImpactReport
    synthetic_affected: list[AffectedObject] = field(default_factory=list)


def _extract_reference_ids(
    frontmatter: dict[str, Any], object_type: str
) -> list[tuple[str, str, str]]:
    """Extract (field_name, relationship_type, target_id) tuples from frontmatter."""
    rel_fields = get_relationship_fields(object_type)
    results: list[tuple[str, str, str]] = []
    for field_name, rel_type in rel_fields.items():
        value = frontmatter.get(field_name)
        if value is None:
            continue
        if isinstance(value, str):
            results.append((field_name, rel_type, value))
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    results.append((field_name, rel_type, item))
    return results


def generate_proposal_impact_report(
    db_path: Path,
    proposal_id: str,
    operations: list[dict[str, Any]],
    max_depth: int = 2,
) -> ProposalImpactReport:
    """Compute impact for each operation in a PatchProposal.

    For update_object operations, baseline impact is computed from the existing
    object in the index. For create_object operations, synthetic affected objects
    are derived from reference fields in the proposed frontmatter.
    """
    operation_reports: list[OperationImpactReport] = []
    high_risk = False

    for op in operations:
        op_type = op.get("op")
        obj_id = op.get("object_id")
        obj_type = op.get("object_type")

        if not obj_id or op_type not in {"update_object", "create_object"}:
            continue

        # Baseline impact from the index
        baseline = generate_impact_report(db_path, obj_id, max_depth=max_depth)

        synthetic: list[AffectedObject] = []

        if op_type == "create_object" and isinstance(op.get("after"), dict):
            refs = _extract_reference_ids(op["after"], obj_type or "")
            for _field_name, rel_type, target_id in refs:
                synthetic.append(
                    AffectedObject(
                        object_id=target_id,
                        object_type="Unknown",
                        object_name=None,
                        relationship_type=rel_type,
                        direction="downstream",
                        depth=1,
                    )
                )
        elif op_type == "update_object" and op.get("target_path"):
            # If updating a reference field, add synthetic impact for the new value
            target_path = op.get("target_path", "")
            after = op.get("after")
            rel_fields = get_relationship_fields(baseline.root_object_type or obj_type or "")
            if target_path in rel_fields and after is not None:
                values = [after] if isinstance(after, str) else []
                if isinstance(after, list):
                    values = [str(v) for v in after if isinstance(v, str)]
                for val in values:
                    synthetic.append(
                        AffectedObject(
                            object_id=val,
                            object_type="Unknown",
                            object_name=None,
                            relationship_type=rel_fields[target_path],
                            direction="downstream",
                            depth=1,
                        )
                    )

        # Mark high-risk if touching active objects, mappings, rules, or LoV
        if obj_type in {"Mapping", "ValidationRule", "ValueList", "ValueMapping"}:
            high_risk = True
        if baseline.root_object_type in {"Mapping", "ValidationRule", "ValueList", "ValueMapping"}:
            high_risk = True

        operation_reports.append(
            OperationImpactReport(
                op=op_type,
                object_id=obj_id,
                object_type=obj_type or baseline.root_object_type,
                impact_report=baseline,
                synthetic_affected=synthetic,
            )
        )

    return ProposalImpactReport(
        proposal_id=proposal_id,
        operation_reports=operation_reports,
        high_risk=high_risk,
    )
