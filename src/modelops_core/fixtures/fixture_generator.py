"""Generate realistic but non-sensitive model repositories for demos and tests."""

from __future__ import annotations

import json
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
    "enterprise": FixtureProfile(
        name="enterprise",
        domain_count=3,
        attribute_count=18,
        field_endpoint_count=36,
        mapping_count=18,
        value_list_count=3,
        validation_rule_count=18,
        issue_count=3,
        with_gaps=False,
    ),
}


def _write_object(path: Path, obj_id: str, obj_type: str, **fields: Any) -> None:
    frontmatter_lines = [
        f"id: {obj_id}",
        f"type: {obj_type}",
        "status: active",
        'schema_version: "1.0"',
    ]
    for k, v in fields.items():
        if v is None:
            continue
        if isinstance(v, list):
            frontmatter_lines.append(f"{k}:")
            for item in v:
                frontmatter_lines.append(f"  - {item}")
        else:
            frontmatter_lines.append(f"{k}: {v}")
    frontmatter = "\n".join(frontmatter_lines)
    content = f"---\n{frontmatter}\n---\n\n# {obj_id}\n"
    path.write_text(content, encoding="utf-8")


def _generate_enterprise_fixture(output_dir: Path, profile: FixtureProfile) -> dict[str, Any]:
    """Generate a governed, multi-domain portfolio suitable for a realistic demo.

    Unlike the size-oriented profiles, this fixture deliberately contains valid
    cross-domain references, accountable people and teams, and append-only
    synthetic activity.  It is useful for exercising the Workbench's model,
    ownership, lineage, health, and activity views together.
    """
    model_dir = output_dir / "model"
    model_dir.mkdir(parents=True, exist_ok=True)
    generated_dir = output_dir / "generated"
    generated_dir.mkdir(parents=True, exist_ok=True)

    domains = (
        ("CUSTOMER", "Customer", "PERSON-CUSTOMER-OWNER", "TEAM-CUSTOMER-DATA"),
        ("SUPPLIER", "Supplier", "PERSON-SUPPLIER-OWNER", "TEAM-SUPPLIER-DATA"),
        ("PRODUCT", "Product", "PERSON-PRODUCT-OWNER", "TEAM-PRODUCT-DATA"),
    )
    people = (
        ("PERSON-CUSTOMER-OWNER", "Avery Morgan", "Customer Data Owner"),
        ("PERSON-SUPPLIER-OWNER", "Jordan Patel", "Supplier Data Owner"),
        ("PERSON-PRODUCT-OWNER", "Riley Kim", "Product Data Owner"),
        ("PERSON-PLATFORM-OWNER", "Casey Novak", "Integration Platform Owner"),
        ("PERSON-CHIEF-STEWARD", "Morgan Lee", "Chief Data Steward"),
    )
    for person_id, name, role in people:
        _write_object(
            model_dir / f"{person_id}.md",
            person_id,
            "Person",
            name=name,
            role=role,
            email=f"{person_id.lower()}@example.invalid",
            description="Fictional governance participant for the synthetic portfolio.",
        )

    for code, label, _owner, team_id in domains:
        domain_id = f"DOMAIN-{code}"
        _write_object(
            model_dir / f"{domain_id}.md",
            domain_id,
            "MasterDataDomain",
            name=f"{label} Master Data",
            description=f"Synthetic {label.lower()} domain in the governed enterprise portfolio.",
            accountable_team=team_id,
        )
        _write_object(
            model_dir / f"{team_id}.md",
            team_id,
            "Team",
            name=f"{label} Data Council",
            description=f"Fictional accountable team for {label.lower()} model decisions.",
        )
        _write_object(
            model_dir / f"ENTITY-{code}.md",
            f"ENTITY-{code}",
            "BusinessEntity",
            name=f"{label} Record",
            domain=domain_id,
            business_owner=_owner,
            data_steward="PERSON-CHIEF-STEWARD",
            accountable_team=team_id,
            description=f"Canonical business entity for the synthetic {label.lower()} record.",
        )
        _write_object(
            model_dir / f"CTX-{code}-DEFAULT.md",
            f"CTX-{code}-DEFAULT",
            "EntityContext",
            name=f"{label} governed record context",
            domain=domain_id,
            entity=f"ENTITY-{code}",
            context_category="governed_record",
            description=f"Default integration context for synthetic {label.lower()} fields.",
        )

    for system_id, name, system_type in (
        ("SYS-PORTFOLIO-SOURCE", "Portfolio Source Suite", "operational"),
        ("SYS-PORTFOLIO-HUB", "Portfolio Governance Hub", "mdm"),
        ("SYS-PORTFOLIO-ANALYTICS", "Portfolio Analytics", "analytics"),
    ):
        _write_object(
            model_dir / f"{system_id}.md",
            system_id,
            "System",
            name=name,
            system_type=system_type,
            technical_owner="PERSON-PLATFORM-OWNER",
            description="Fictional system used only by the synthetic enterprise portfolio.",
        )

    attribute_count = 0
    endpoint_count = 0
    mapping_count = 0
    rule_count = 0
    for code, label, owner, team_id in domains:
        domain_id = f"DOMAIN-{code}"
        value_list_id = f"VLIST-{code}-STATUS"
        _write_object(
            model_dir / f"{value_list_id}.md",
            value_list_id,
            "ValueList",
            name=f"{label} Lifecycle Status",
            domain=domain_id,
            value_list_type="controlled",
            data_steward="PERSON-CHIEF-STEWARD",
            accountable_team=team_id,
            entries=[
                {"code": "ACTIVE", "label": "Active", "is_active": True},
                {"code": "REVIEW", "label": "In review", "is_active": True},
            ],
            description=f"Controlled synthetic lifecycle values for {label.lower()} records.",
        )
        value_mapping_id = f"VMAP-{code}-SOURCE-TO-HUB"
        _write_object(
            model_dir / f"{value_mapping_id}.md",
            value_mapping_id,
            "ValueMapping",
            name=f"{label} source values to hub values",
            domain=domain_id,
            source_value_list=value_list_id,
            target_value_list=value_list_id,
            entries=[
                {"source_code": "ACTIVE", "target_code": "ACTIVE"},
                {"source_code": "REVIEW", "target_code": "REVIEW"},
            ],
            business_owner=owner,
            data_steward="PERSON-CHIEF-STEWARD",
            description=f"Controlled synthetic value crosswalk for {label.lower()} source values.",
        )
        for suffix, name in (
            ("ID", f"{label} Identifier"),
            ("NAME", f"{label} Name"),
            ("STATUS", f"{label} Lifecycle Status"),
            ("CLASS", f"{label} Classification"),
            ("COUNTRY", f"{label} Country"),
            ("RISK", f"{label} Risk Tier"),
        ):
            attr_id = f"ATTR-{code}-{suffix}"
            rule_id = f"VAL-{code}-{suffix}-PRESENT"
            source_id = f"FEP-SOURCE-{code}-{suffix}"
            hub_id = f"FEP-HUB-{code}-{suffix}"
            mapping_id = f"MAP-{code}-{suffix}-TO-HUB"
            _write_object(
                model_dir / f"{attr_id}.md",
                attr_id,
                "Attribute",
                name=name,
                domain=domain_id,
                entity=f"ENTITY-{code}",
                entity_context=f"CTX-{code}-DEFAULT",
                business_owner=owner,
                technical_owner="PERSON-PLATFORM-OWNER",
                data_steward="PERSON-CHIEF-STEWARD",
                accountable_team=team_id,
                value_list=value_list_id if suffix == "STATUS" else None,
                data_classification="synthetic",
                description=(
                    f"Governed synthetic {name.lower()} used to demonstrate "
                    "ownership and traceability."
                ),
            )
            _write_object(
                model_dir / f"{source_id}.md",
                source_id,
                "FieldEndpoint",
                name=f"Source {name}",
                domain=domain_id,
                system="SYS-PORTFOLIO-SOURCE",
                endpoint_type="application_field",
                technical_name=f"{code.lower()}_{suffix.lower()}",
                business_attribute=attr_id,
                entity_context=f"CTX-{code}-DEFAULT",
                business_owner=owner,
                data_steward="PERSON-CHIEF-STEWARD",
                value_list=value_list_id,
                description=f"Synthetic operational representation of {name.lower()}.",
            )
            _write_object(
                model_dir / f"{hub_id}.md",
                hub_id,
                "FieldEndpoint",
                name=f"Governed {name}",
                domain=domain_id,
                system="SYS-PORTFOLIO-HUB",
                endpoint_type="application_field",
                technical_name=f"golden_{code.lower()}_{suffix.lower()}",
                business_attribute=attr_id,
                entity_context=f"CTX-{code}-DEFAULT",
                business_owner=owner,
                technical_owner="PERSON-PLATFORM-OWNER",
                data_steward="PERSON-CHIEF-STEWARD",
                value_list=value_list_id,
                description=f"Synthetic governed representation of {name.lower()}.",
            )
            _write_object(
                model_dir / f"{mapping_id}.md",
                mapping_id,
                "Mapping",
                name=f"{label} {suffix.title()} Source to Hub",
                domain=domain_id,
                source_endpoint=source_id,
                target_endpoint=hub_id,
                value_mapping=value_mapping_id,
                business_owner=owner,
                technical_owner="PERSON-PLATFORM-OWNER",
                data_steward="PERSON-CHIEF-STEWARD",
                accountable_team=team_id,
                description=(
                    f"Traceable synthetic mapping for {name.lower()} into the governance hub."
                ),
            )
            _write_object(
                model_dir / f"{rule_id}.md",
                rule_id,
                "ValidationRule",
                name=f"{name} required",
                domain=domain_id,
                attribute=attr_id,
                rule_type="required",
                business_owner=owner,
                data_steward="PERSON-CHIEF-STEWARD",
                description=f"Deterministic completeness rule for synthetic {name.lower()}.",
            )
            attribute_count += 1
            endpoint_count += 2
            mapping_count += 1
            rule_count += 1

        issue_id = f"ISS-{code}-CLASSIFICATION-REVIEW"
        decision_id = f"DEC-{code}-STEWARDSHIP-BASELINE"
        _write_object(
            model_dir / f"{issue_id}.md",
            issue_id,
            "Issue",
            name=f"{label} classification review",
            domain=domain_id,
            status="in_progress",
            business_owner=owner,
            data_steward="PERSON-CHIEF-STEWARD",
            related_objects=[f"ATTR-{code}-CLASS"],
            description="Synthetic review item retained to demonstrate a governed work queue.",
        )
        _write_object(
            model_dir / f"{decision_id}.md",
            decision_id,
            "Decision",
            name=f"{label} stewardship baseline",
            domain=domain_id,
            approver="PERSON-CHIEF-STEWARD",
            business_owner=owner,
            related_objects=[f"ATTR-{code}-STATUS", issue_id],
            description="Synthetic decision recording the domain ownership baseline.",
        )

    _write_object(
        model_dir / "FLOW-PORTFOLIO-SOURCE-TO-HUB.md",
        "FLOW-PORTFOLIO-SOURCE-TO-HUB",
        "IntegrationFlow",
        name="Portfolio source to governance hub",
        source_system="SYS-PORTFOLIO-SOURCE",
        target_system="SYS-PORTFOLIO-HUB",
        technical_owner="PERSON-PLATFORM-OWNER",
        description="One synthetic integration flow shared by the three governed domains.",
    )

    (output_dir / "modelops.config.yaml").write_text(
        'schema_version: "1.0"\n'
        "name: Synthetic Enterprise Portfolio Demo\n"
        "description: Governed multi-domain synthetic repository for Workbench demonstrations.\n",
        encoding="utf-8",
    )
    events = [
        {
            "event_id": "audit-demo-001",
            "event_type": "index_rebuilt",
            "timestamp": "2026-07-01T09:00:00Z",
            "actor": "system",
            "status": "success",
            "changed_object_ids": [],
            "metadata": {"synthetic": True},
        },
        {
            "event_id": "audit-demo-002",
            "event_type": "validation_completed",
            "timestamp": "2026-07-01T09:05:00Z",
            "actor": "PERSON-CHIEF-STEWARD",
            "status": "success",
            "validation_status": "passed",
            "changed_object_ids": [
                "ATTR-CUSTOMER-STATUS",
                "ATTR-SUPPLIER-STATUS",
                "ATTR-PRODUCT-STATUS",
            ],
            "metadata": {"synthetic": True},
        },
        {
            "event_id": "audit-demo-003",
            "event_type": "ownership_reviewed",
            "timestamp": "2026-07-01T09:12:00Z",
            "actor": "PERSON-CHIEF-STEWARD",
            "status": "success",
            "changed_object_ids": ["DOMAIN-CUSTOMER", "DOMAIN-SUPPLIER", "DOMAIN-PRODUCT"],
            "metadata": {"synthetic": True},
        },
    ]
    (generated_dir / "audit_events.jsonl").write_text(
        "".join(json.dumps(event) + "\n" for event in events), encoding="utf-8"
    )
    return {
        "profile": profile.name,
        "output_dir": str(output_dir),
        "counts": {
            "domain": 3,
            "attribute": attribute_count,
            "field_endpoint": endpoint_count,
            "mapping": mapping_count,
            "validation_rule": rule_count,
            "issue": 3,
            "person": len(people),
            "team": 3,
            "audit_event": len(events),
        },
        "with_gaps": False,
    }


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

    if p.name == "enterprise":
        return _generate_enterprise_fixture(output_dir, p)

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
