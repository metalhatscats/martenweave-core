# Domain Packs

> Optional domain-specific modeling rules, validation, and conventions that extend Martenweave core without changing its generic concepts.

---

## Principle

Martenweave core is generic. It knows about objects, relationships, validation layers, and proposals — but it does not require any vendor-specific metadata.

**Domain packs** add optional knowledge for specific business domains:
- SAP master data and migration rules
- Analytics / BI semantic layers
- Finance / procurement / HR data models
- Product catalog structures
- Custom enterprise datasets

A repository enables the packs it needs. Packs it does not enable are completely inactive.

---

## Enabling a Domain Pack

Add `enabled_domain_packs` to your `modelops.config.yaml`:

```yaml
name: "My Repository"
model_path: "model"
generated_path: "generated"
enabled_domain_packs:
  - sap
```

Without this key, no domain packs run and only generic validation applies.

---

## Built-in Packs

### `sap`

Validates SAP-specific context rules for `FieldEndpoint` objects:

| SAP Table | Required `context_category` |
|---|---|
| `KNVV` | `customer_sales_area` |
| `KNB1` | `customer_company_code` |
| `KNVP` | `customer_partner_function` |
| `BUT000` | `bp_central` |

A `FieldEndpoint` with `endpoint_type: sap_table_field` and `sap_table: KNVV` must reference an `EntityContext` whose `context_category` is `customer_sales_area`.

If the `sap` pack is not enabled, these rules are skipped.

---

## Architecture

### Pack Interface

Every domain pack subclasses `DomainPack`:

```python
from modelops_core.domain_packs.base import DomainPack

class MyDomainPack(DomainPack):
    name = "my_domain"
    description = "Rules for my domain."

    def validate(self, objects, registry):
        results = []
        for obj in objects:
            # ... domain-specific checks ...
            results.append({
                "severity": "ERROR",
                "code": "MY_DOMAIN_RULE_001",
                "message": "...",
                "object_id": obj.frontmatter.get("id"),
                "suggested_fix": "...",
            })
        return results
```

### Registration

Register the pack in `modelops_core/domain_packs/__init__.py`:

```python
_REGISTERED_PACKS: dict[str, type[DomainPack]] = {
    "sap": SAPDomainPack,
    "my_domain": MyDomainPack,
}
```

### Validation Pipeline Integration

Domain packs run as **Layer 3** validation, after:
1. Layer 1 — individual object validation
2. Layer 2 — cross-object references and duplicates

Packs receive:
- `objects`: list of `ParsedObject` instances
- `registry`: ID-to-type lookup mapping

Results are appended to the same `ValidationSummary` as generic rules.

---

## Core Remains Generic

Enabling or disabling a domain pack never changes:
- The canonical file format
- The object type registry
- The proposal/apply workflow
- The export/import behavior

Packs can add validation warnings and errors, but they cannot change core concepts or introduce required fields that break generic models.
