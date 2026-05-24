"""Generate realistic but non-sensitive model repositories for demos and tests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class FixtureProfile:
    """Size profile for generated fixtures."""

    name: str
    domain_count: int = 1
    attribute_count: int = 5
    field_endpoint_count: int = 5
    mapping_count: int = 5
    value_list_count: int = 2
    validation_rule_count: int = 2
    issue_count: int = 1
    with_gaps: bool = True


_PROFILES: dict[str, FixtureProfile] = {
    "small": FixtureProfile(
        name="small",
        domain_count=1,
        attribute_count=5,
        field_endpoint_count=5,
        mapping_count=5,
        value_list_count=1,
        validation_rule_count=1,
        issue_count=1,
        with_gaps=True,
    ),
    "medium": FixtureProfile(
        name="medium",
        domain_count=2,
        attribute_count=20,
        field_endpoint_count=20,
        mapping_count=15,
        value_list_count=3,
        validation_rule_count=5,
        issue_count=3,
        with_gaps=True,
    ),
    "large": FixtureProfile(
        name="large",
        domain_count=3,
        attribute_count=50,
        field_endpoint_count=50,
        mapping_count=40,
        value_list_count=8,
        validation_rule_count=12,
        issue_count=5,
        with_gaps=False,
    ),
}


def _write_object(path: Path, obj_id: str, obj_type: str, **fields: Any) -> None:
    frontmatter_lines = [f"id: {obj_id}", f"type: {obj_type}", "status: active"]
    for k, v in fields.items():
        if isinstance(v, list):
            frontmatter_lines.append(f"{k}:")
            for item in v:
                frontmatter_lines.append(f"  - {item}")
        else:
            frontmatter_lines.append(f"{k}: {v}")
    frontmatter = "\n".join(frontmatter_lines)
    content = f"---\n{frontmatter}\n---\n\n# {obj_id}\n"
    path.write_text(content, encoding="utf-8")


def generate_fixture_repo(
    output_dir: Path,
    profile: str | FixtureProfile = "small",
) -> dict[str, Any]:
    """Generate a synthetic model repository.

    Args:
        output_dir: Directory to write the model repository.
        profile: Size profile name (small/medium/large) or a FixtureProfile.

    Returns:
        Summary dict with counts of generated objects.
    """
    if isinstance(profile, str):
        p = _PROFILES.get(profile, _PROFILES["small"])
    else:
        p = profile

    model_dir = output_dir / "model"
    model_dir.mkdir(parents=True, exist_ok=True)
    generated_dir = output_dir / "generated"
    generated_dir.mkdir(parents=True, exist_ok=True)

    counts: dict[str, int] = {}

    # Domains
    domains: list[str] = []
    for i in range(p.domain_count):
        domain_id = f"DOMAIN-{(i + 1):03d}"
        domains.append(domain_id)
        _write_object(
            model_dir / f"{domain_id}.md",
            domain_id,
            "MasterDataDomain",
            name=f"Domain {i + 1}",
            description=f"Synthetic domain {i + 1} for testing.",
        )
    counts["domain"] = len(domains)

    # Attributes
    attrs: list[str] = []
    for i in range(p.attribute_count):
        attr_id = f"ATTR-{(i + 1):03d}"
        attrs.append(attr_id)
        domain = domains[i % len(domains)]
        owner = None if (p.with_gaps and i % 7 == 0) else f"PERSON-{(i % 5) + 1:03d}"
        kwargs: dict[str, Any] = {
            "name": f"Attribute {i + 1}",
            "domain": domain,
            "description": f"Synthetic attribute {i + 1}.",
        }
        if owner:
            kwargs["business_owner"] = owner
        _write_object(model_dir / f"{attr_id}.md", attr_id, "Attribute", **kwargs)
    counts["attribute"] = len(attrs)

    # FieldEndpoints
    feps: list[str] = []
    for i in range(p.field_endpoint_count):
        fep_id = f"FEP-{(i + 1):03d}"
        feps.append(fep_id)
        attr = attrs[i % len(attrs)] if attrs else None
        kwargs = {"name": f"Field {i + 1}"}
        if attr and not (p.with_gaps and i % 5 == 0):
            kwargs["business_attribute"] = attr
        if p.with_gaps and i % 3 == 0:
            kwargs["value_list"] = f"VLIST-{(i % p.value_list_count) + 1:03d}"
        _write_object(model_dir / f"{fep_id}.md", fep_id, "FieldEndpoint", **kwargs)
    counts["field_endpoint"] = len(feps)

    # AttributeUsages (link attrs to feps)
    usages: list[str] = []
    for i in range(min(p.attribute_count, p.field_endpoint_count)):
        usage_id = f"USE-{(i + 1):03d}"
        usages.append(usage_id)
        _write_object(
            model_dir / f"{usage_id}.md",
            usage_id,
            "AttributeUsage",
            attribute=attrs[i],
            field_endpoint=feps[i],
            name=f"Usage {i + 1}",
        )
    counts["attribute_usage"] = len(usages)

    # Mappings
    maps: list[str] = []
    for i in range(p.mapping_count):
        map_id = f"MAP-{(i + 1):03d}"
        maps.append(map_id)
        kwargs = {"name": f"Mapping {i + 1}"}
        if not (p.with_gaps and i % 4 == 0):
            kwargs["value_mapping"] = f"VMAP-{(i % 3) + 1:03d}"
        _write_object(model_dir / f"{map_id}.md", map_id, "Mapping", **kwargs)
    counts["mapping"] = len(maps)

    # ValueLists
    vlists: list[str] = []
    for i in range(p.value_list_count):
        vlist_id = f"VLIST-{(i + 1):03d}"
        vlists.append(vlist_id)
        _write_object(
            model_dir / f"{vlist_id}.md",
            vlist_id,
            "ValueList",
            name=f"Value List {i + 1}",
            entries=[f"CODE-{j}" for j in range(3)],
        )
    counts["value_list"] = len(vlists)

    # ValidationRules
    rules: list[str] = []
    for i in range(p.validation_rule_count):
        rule_id = f"RULE-{(i + 1):03d}"
        rules.append(rule_id)
        attr = attrs[i % len(attrs)] if attrs else None
        kwargs = {"name": f"Rule {i + 1}"}
        if attr:
            kwargs["attribute"] = attr
        _write_object(model_dir / f"{rule_id}.md", rule_id, "ValidationRule", **kwargs)
    counts["validation_rule"] = len(rules)

    # Issues
    issues: list[str] = []
    for i in range(p.issue_count):
        issue_id = f"ISS-{(i + 1):03d}"
        issues.append(issue_id)
        _write_object(
            model_dir / f"{issue_id}.md",
            issue_id,
            "Issue",
            name=f"Issue {i + 1}",
            severity="warning",
        )
    counts["issue"] = len(issues)

    # Config
    config_path = output_dir / "modelops.config.yaml"
    config_path.write_text(
        "# Synthetic fixture repository\ngenerated_dir: generated\nmodel_dir: model\n",
        encoding="utf-8",
    )

    return {
        "profile": p.name,
        "output_dir": str(output_dir),
        "counts": counts,
        "with_gaps": p.with_gaps,
    }
