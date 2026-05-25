# JSON Schema and OpenAPI Import Design

## Goal
Allow Martenweave to model API contracts and JSON payload structures as first-class data model sources.

## Scope

This document covers:

- Mapping from JSON Schema constructs to Martenweave objects
- Mapping from OpenAPI request/response schemas to Martenweave objects
- Safe import flow through PatchProposal
- Future CLI command design

## JSON Schema → Martenweave Concept Map

| JSON Schema Construct | Martenweave Object | Notes |
|---|---|---|
| Schema `title` | `BusinessEntity.name` or `Dataset.name` | Top-level title maps to entity/dataset name |
| Schema `description` | `BusinessEntity.description` or `Dataset.description` | Description carried forward |
| `properties` key | `Attribute.name` | Property name becomes attribute name |
| Property `description` | `Attribute.description` | Property description carried forward |
| Property `type` | `FieldEndpoint` metadata | JSON type stored on FieldEndpoint |
| `enum` | `ValueList` | Enum values become a ValueList with entries |
| `format` | `ValidationRule` or metadata | `format: email` → email validation rule; `format: date` → date type metadata |
| `required` array | `ValidationRule` | Required fields become `not_null` validation rules |
| `minimum` / `maximum` | `ValidationRule` | Range constraints become validation rules |
| `minLength` / `maxLength` | `ValidationRule` | Length constraints become validation rules |
| `pattern` | `ValidationRule` | Regex pattern becomes pattern validation rule |
| `$ref` | `Mapping` or `related_to` | References to other schemas become mappings or relationships |
| `allOf` / `anyOf` / `oneOf` | `BusinessEntity` with `related_to` | Composition patterns map to entity relationships |
| Nested object property | `BusinessEntity` + `Attribute` | Nested objects become child entities with attributes |
| Array `items` | `Attribute` with `usage_type: list` | Array items map to list-type attributes |

## OpenAPI → Martenweave Concept Map

| OpenAPI Construct | Martenweave Object | Notes |
|---|---|---|
| Path + operation (`GET /products`) | `Interface` or `InterfaceEndpoint` | API endpoint as interface |
| `requestBody` schema | `Dataset` | Request payload as input dataset |
| `responses` schema | `Dataset` | Response payload as output dataset |
| `components.schemas` | `BusinessEntity` | Reusable schemas become entities |
| `parameters` | `FieldEndpoint` | Query/path parameters as field endpoints |
| `tags` | `MasterDataDomain` | Tags group operations into domains |
| `securitySchemes` | Evidence or metadata | Auth methods documented as metadata, not canonical objects |

## Import Flow

```
1. Parse schema file
   └─ Read JSON Schema (.json) or OpenAPI spec (.yaml, .json)
   └─ Resolve $ref references inline or build reference map
   └─ Do not execute API calls

2. Create SourceEntry
   └─ Register the schema file as a source
   └─ Store file path and checksum in SourceRegistryService

3. Generate candidates
   └─ Map schemas to Entity/Dataset candidates
   └─ Map properties to Attribute + FieldEndpoint candidates
   └─ Map enums to ValueList candidates
   └─ Map constraints to ValidationRule candidates
   └─ Map references to Mapping candidates

4. Build PatchProposal
   └─ Package candidates as PatchProposal
   └─ Proposal ID: PP-IMPORT-SCHEMA:<file_hash>
   └─ Include metadata: source file, schema version, import timestamp

5. Validate and review
   └─ Run through standard validation pipeline
   └─ Human reviews and edits generated objects
   └─ Approve → ChangeRequest → Apply
```

## Example: Importing a Product Schema

Input JSON Schema:

```json
{
  "title": "Product",
  "type": "object",
  "required": ["id", "name", "price"],
  "properties": {
    "id": {
      "type": "string",
      "description": "Unique product identifier"
    },
    "name": {
      "type": "string",
      "description": "Product display name",
      "maxLength": 255
    },
    "price": {
      "type": "number",
      "description": "Product price",
      "minimum": 0
    },
    "status": {
      "type": "string",
      "enum": ["active", "discontinued", "draft"]
    },
    "category": {
      "$ref": "#/components/schemas/Category"
    }
  }
}
```

Generated Martenweave candidates:

```yaml
# Entity
id: ENTITY-PRODUCT
type: BusinessEntity
status: draft
name: Product

# Attributes and FieldEndpoints
id: ATTR-PRODUCT-ID
type: Attribute
status: draft
name: id
entity: ENTITY-PRODUCT

id: FEP-SCHEMA-PRODUCT-ID
type: FieldEndpoint
status: draft
name: Product.id
attribute: ATTR-PRODUCT-ID
endpoint_type: json_schema_property
technical_name: id

id: ATTR-PRODUCT-NAME
type: Attribute
status: draft
name: name
entity: ENTITY-PRODUCT

id: FEP-SCHEMA-PRODUCT-NAME
type: FieldEndpoint
status: draft
name: Product.name
attribute: ATTR-PRODUCT-NAME
endpoint_type: json_schema_property
technical_name: name

# ValidationRule for maxLength
id: VRULE-PRODUCT-NAME-LENGTH
type: ValidationRule
status: draft
name: Product name max length
attribute: ATTR-PRODUCT-NAME
rule_type: max_length

# ValueList for enum
id: VLIST-PRODUCT-STATUS
type: ValueList
status: draft
name: Product status values

# Mapping for $ref
id: MAP-PRODUCT-CATEGORY
type: Mapping
status: draft
name: Product category reference
source_endpoint: FEP-SCHEMA-PRODUCT-CATEGORY
target_endpoint: FEP-SCHEMA-CATEGORY-ID
```

## Future CLI Command

```bash
# Import from a JSON Schema file
modelops import-schema --repo ./my-model --from ./product.schema.json

# Import from an OpenAPI spec
modelops import-schema --repo ./my-model --from ./api.openapi.yaml

# Import with domain assignment
modelops import-schema --repo ./my-model --from ./api.openapi.yaml --domain DOMAIN-PRODUCT

# Dry-run preview
modelops import-schema --repo ./my-model --from ./product.schema.json --dry-run
```

## Connector Design

A schema connector implements `ConnectorAdapter`:

```python
class JsonSchemaConnector:
    @property
    def connector_type(self) -> str:
        return "json_schema"

    def list_sources(self, prefix: str = "") -> list[ConnectorSourceInfo]:
        """List schema files matching prefix."""
        ...

    def fetch_metadata(self, source_id: str) -> ConnectorSourceInfo:
        """Fetch schema metadata (title, version, property count)."""
        ...

    def fetch_content(self, source_id: str) -> bytes:
        """Return raw schema file content."""
        ...
```

The connector reads local files. No network calls are required for JSON Schema import. For OpenAPI specs hosted at URLs, a URL fetch mode can be added later.

## Handling References

- **Internal `$ref`** (`#/components/schemas/Foo`) — resolved during parsing to inline the referenced schema or create a Mapping.
- **External `$ref`** (`./other.schema.json#/Bar`) — resolved if the file exists in the same directory; otherwise logged as a warning.
- **Remote `$ref`** (`https://example.com/schema.json`) — not supported in v0.1. Logged as a warning.

## Out of Scope

- **Schema evolution / diff** — comparing two versions of a schema and generating a delta proposal is a future enhancement.
- **Code generation** — Martenweave does not generate JSON Schema or OpenAPI specs from canonical objects in this design.
- **AsyncAPI / GraphQL schemas** — not covered. The same pattern could be extended later.
- **Runtime API discovery** — fetching OpenAPI specs from a running service's `/openapi.json` endpoint is not covered.

## Safety Notes

- Schema import only reads files. No API calls are made.
- Remote `$ref` URLs are not fetched to prevent SSRF risks.
- Large schemas (>1,000 properties) should be filtered or chunked to avoid overwhelming the proposal builder.
