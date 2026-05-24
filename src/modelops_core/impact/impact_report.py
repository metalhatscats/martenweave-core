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
    def downstream_objects(self) -> list[AffectedObject]:
        return [o for o in self.affected_objects if o.direction == "downstream"]

    @property
    def upstream_objects(self) -> list[AffectedObject]:
        return [o for o in self.affected_objects if o.direction == "upstream"]
