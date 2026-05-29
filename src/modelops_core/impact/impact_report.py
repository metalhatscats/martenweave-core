"""Impact report dataclasses."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AffectedObject:
    """An object affected by a change to the root object."""

    object_id: str
    object_type: str
    object_name: str | None = None
    relationship_type: str | None = None
    relationship_class: str | None = None
    direction: str | None = None  # "upstream" or "downstream"
    depth: int = 0


@dataclass
class ImpactReport:
    """Result of impact analysis."""

    root_object_id: str
    root_object_type: str | None = None
    root_object_name: str | None = None
    affected_objects: list[AffectedObject] = field(default_factory=list)

    @property
    def grouped_by_type(self) -> dict[str, list[AffectedObject]]:
        groups: dict[str, list[AffectedObject]] = {}
        for obj in self.affected_objects:
            groups.setdefault(obj.object_type, []).append(obj)
        return groups

    @property
    def grouped_by_direction_and_type(self) -> dict[str, dict[str, list[AffectedObject]]]:
        groups: dict[str, dict[str, list[AffectedObject]]] = {}
        for obj in self.affected_objects:
            direction = obj.direction or "unknown"
            groups.setdefault(direction, {}).setdefault(obj.object_type, []).append(obj)
        return groups

    @property
    def affected_relationship_classes(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for obj in self.affected_objects:
            rc = obj.relationship_class or "unknown"
            counts[rc] = counts.get(rc, 0) + 1
        return counts

    @property
    def affected_mappings(self) -> list[AffectedObject]:
        return [o for o in self.affected_objects if o.object_type in ("Mapping", "MappingSet")]

    @property
    def affected_rules(self) -> list[AffectedObject]:
        return [o for o in self.affected_objects if o.object_type == "ValidationRule"]

    @property
    def affected_contexts(self) -> list[AffectedObject]:
        return [o for o in self.affected_objects if o.object_type == "EntityContext"]

    @property
    def downstream_objects(self) -> list[AffectedObject]:
        return [o for o in self.affected_objects if o.direction == "downstream"]

    @property
    def upstream_objects(self) -> list[AffectedObject]:
        return [o for o in self.affected_objects if o.direction == "upstream"]


def render_impact_report_markdown(report: ImpactReport) -> str:
    """Render an ImpactReport as a structured Markdown document."""
    lines: list[str] = [
        f"# Impact Report: {report.root_object_id}",
        "",
        "## Root Object",
        "",
        f"- **ID**: {report.root_object_id}",
        f"- **Type**: {report.root_object_type or 'Unknown'}",
    ]
    if report.root_object_name:
        lines.append(f"- **Name**: {report.root_object_name}")
    lines.append("")
    lines.append(f"- **Total affected objects**: {len(report.affected_objects)}")
    lines.append(f"- **Downstream**: {len(report.downstream_objects)}")
    lines.append(f"- **Upstream**: {len(report.upstream_objects)}")
    lines.append("")

    if report.affected_objects:
        lines.append("## Affected Objects")
        lines.append("")
        lines.append("| Object ID | Type | Name | Direction | Depth |")
        lines.append("|-----------|------|------|-----------|-------|")
        for obj in report.affected_objects:
            name = obj.object_name or "—"
            lines.append(
                f"| {obj.object_id} | {obj.object_type} | {name} | "
                f"{obj.direction or '—'} | {obj.depth} |"
            )
        lines.append("")

        # Relationship summary by type
        rel_counts: dict[str, int] = {}
        for obj in report.affected_objects:
            rel = obj.relationship_type or "Unknown"
            rel_counts[rel] = rel_counts.get(rel, 0) + 1
        if rel_counts:
            lines.append("## Relationship Summary")
            lines.append("")
            for rel, count in sorted(rel_counts.items()):
                lines.append(f"- **{rel}**: {count}")
            lines.append("")

        # Relationship class summary
        if report.affected_relationship_classes:
            lines.append("## Relationship Classes")
            lines.append("")
            for rc, count in sorted(report.affected_relationship_classes.items()):
                lines.append(f"- **{rc}**: {count}")
            lines.append("")

        # Grouped by direction and type
        grouped = report.grouped_by_direction_and_type
        if grouped:
            lines.append("## Grouped by Direction and Type")
            lines.append("")
            for direction in ("downstream", "upstream"):
                type_groups = grouped.get(direction, {})
                if not type_groups:
                    continue
                lines.append(f"### {direction.capitalize()}")
                lines.append("")
                for obj_type, objs in sorted(type_groups.items()):
                    lines.append(f"- **{obj_type}** ({len(objs)})")
                    for obj in objs:
                        name = obj.object_name or "—"
                        lines.append(f"  - {obj.object_id} — {name}")
                lines.append("")
    else:
        lines.append("*No related objects found.*")
        lines.append("")

    return "\n".join(lines)
