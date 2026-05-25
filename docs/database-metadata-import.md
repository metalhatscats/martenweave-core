# Database Metadata Import Design

## Goal
Design how Martenweave can import database metadata (schemas, tables, columns, constraints, indexes, comments, relationships) from relational and analytical databases without bypassing the PatchProposal workflow.

## Scope

This document covers:

- Mapping from database concepts to Martenweave canonical objects
- Safe import flow from metadata inspection to PatchProposal
- Connector targets and roadmap
- Credential handling
- Out-of-scope boundaries

## Database → Martenweave Concept Map

| Database Concept | Martenweave Object | Notes |
|---|---|---|
| Database / Catalog | `System` | The database instance as a system in the landscape |
| Schema | `MasterDataDomain` | A namespace that groups related tables |
| Table | `BusinessEntity` or `Dataset` | Tables with clear business meaning → Entity; raw/storage tables → Dataset |
| Column | `Attribute` + `FieldEndpoint` | Column metadata → Attribute; physical column → FieldEndpoint |
| Primary Key | `ValidationRule` | Constraint expressed as a validation rule |
| Foreign Key | `Mapping` | Relationship between tables expressed as a mapping |
| Unique Constraint | `ValidationRule` | Uniqueness check |
| Check Constraint | `ValidationRule` | Domain constraint |
| Index | Evidence or metadata | Indexes are implementation details; can be stored as Evidence or omitted |
| Column Comment | `Attribute.description` | Database comments map to Attribute descriptions |
| Table Comment | `BusinessEntity.description` or `Dataset.description` | Table comments map to entity/dataset descriptions |
| Data Type | `FieldEndpoint` metadata | Physical data type stored on FieldEndpoint |
| Nullable | `ValidationRule` | `NOT NULL` → required field validation |
| Default Value | `Attribute` metadata | Default value stored as Attribute metadata |

## Safe Import Flow

Database metadata must never mutate canonical files directly. The import flow is:

```
1. Inspect metadata
   └─ Connect to database via optional connector
   └─ Read catalog, schemas, tables, columns, constraints, relationships
   └─ Do not read row data

2. Create SourceEntry
   └─ Register the database as a source in SourceRegistryService
   └─ Store connection reference (not credentials) in metadata

3. Generate candidates
   └─ Map database objects to Martenweave object candidates
   └─ Build candidate tree: System → Domain → Entity/Dataset → Attribute → FieldEndpoint
   └─ Include confidence scores (explicit for columns, inferred for business meaning)

4. Build PatchProposal
   └─ Package candidates as a PatchProposal
   └─ Proposal ID: PP-IMPORT-DB:<connection_hash>
   └─ Include metadata: source database, schema filter, import timestamp

5. Validate
   └─ Run the proposal through validate_repository
   └─ Check for ID collisions, broken references, type mismatches

6. Human review
   └─ Present proposal in CLI or future UI
   └─ Allow editing of generated names, descriptions, and mappings

7. Approve → ChangeRequest → Apply
   └─ Standard Martenweave approval workflow
```

## Connector Targets

### Tier 1 — Built-in support (v0.2+)

| Database | Driver | Metadata Access |
|---|---|---|
| SQLite | `sqlite3` (stdlib) | `sqlite_master`, `PRAGMA table_info`, `PRAGMA foreign_key_list` |
| PostgreSQL | `psycopg2` or `psycopg` | `information_schema.columns`, `information_schema.table_constraints`, `pg_catalog` |

### Tier 2 — Community / optional adapters (future)

| Database | Driver | Notes |
|---|---|---|
| SQL Server | `pyodbc` or `pymssql` | `INFORMATION_SCHEMA` views; Windows auth complexity |
| MySQL / MariaDB | `mysql-connector-python` or `pymysql` | `information_schema` views |
| Snowflake | `snowflake-connector-python` | Account/warehouse parameters; role-based access |
| BigQuery | `google-cloud-bigquery` | Project/dataset scope; IAM auth |
| Databricks | `databricks-sql-connector` | Cluster/warehouse connection; OAuth |
| Oracle | `oracledb` or `cx_Oracle` | `ALL_TAB_COLUMNS`, `ALL_CONSTRAINTS`; thick client complexity |

## Connector Design

A database connector implements the existing `ConnectorAdapter` protocol:

```python
class DatabaseConnector:
    @property
    def connector_type(self) -> str:
        return "database"

    def list_sources(self, prefix: str = "") -> list[ConnectorSourceInfo]:
        """List schemas or tables matching prefix."""
        ...

    def fetch_metadata(self, source_id: str) -> ConnectorSourceInfo:
        """Fetch table/column metadata for source_id (format: schema.table)."""
        ...

    def fetch_content(self, source_id: str) -> bytes:
        """Not used for metadata import. Raises ConnectorError."""
        ...
```

Connection parameters (host, port, database, schema) are passed at initialization. Credentials are read from environment variables or a secrets manager, never from canonical files.

## Credential Handling

- **Never store passwords in canonical files.**
- **Use environment variables:** `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`.
- **Or use connection strings from env:** `DATABASE_URL`.
- **SourceEntry metadata** stores the connection reference (e.g., `postgresql://host/db`) with password redacted.
- **Audit events** log import actions without logging credentials.

## Example: Importing a PostgreSQL Schema

```bash
# Set credentials via environment
export DB_HOST=localhost
export DB_NAME=mydb
export DB_SCHEMA=public
export DB_USER=modelops
export DB_PASSWORD=***

# Import metadata as a proposal
modelops import-db --repo ./my-model \
  --type postgresql \
  --schema public \
  --system-id SYSTEM-POSTGRES-PROD \
  --domain-id DOMAIN-PRODUCT

# Output: creates PatchProposal in generated/proposals/
# Review and apply through standard workflow
```

Generated candidate objects for a `products` table:

```yaml
# System
id: SYSTEM-POSTGRES-PROD
type: System
status: active
name: Production PostgreSQL

# Domain
id: DOMAIN-PRODUCT
type: MasterDataDomain
status: active
name: Product Domain

# Entity
id: ENTITY-PRODUCT
type: BusinessEntity
status: draft
name: Product
system: SYSTEM-POSTGRES-PROD
domain: DOMAIN-PRODUCT

# Attribute + FieldEndpoint for each column
id: ATTR-PRODUCT-NAME
type: Attribute
status: draft
name: Product Name
domain: DOMAIN-PRODUCT
entity: ENTITY-PRODUCT

id: FEP-POSTGRES-PRODUCTS-NAME
type: FieldEndpoint
status: draft
name: products.name
system: SYSTEM-POSTGRES-PROD
attribute: ATTR-PRODUCT-NAME
entity_context: ENTITY-PRODUCT
endpoint_type: postgresql_column
technical_name: name
```

## Out of Scope

- **Live data extraction** — reading table rows, sampling, or profiling is not part of metadata import. Use the existing dataset profiling pipeline for that.
- **Schema evolution tracking** — detecting changes over time and generating delta proposals is a future enhancement.
- **Stored procedures / functions** — not mapped to Martenweave objects in this design.
- **Database-specific advanced features** — triggers, partitions, materialized views are not covered.
- **Write-back to database** — Martenweave does not generate DDL or alter database schemas.

## Safety Notes

- The connector only reads metadata from system catalogs. No `SELECT *` queries are executed.
- Connection timeouts and read-only transaction modes prevent accidental mutations.
- Large schemas (>1,000 tables) should be filtered by schema or table pattern to avoid overwhelming the proposal builder.

## Future CLI Command

```bash
# Import metadata from a database
modelops import-db --repo ./my-model --type postgresql --schema public

# Import with table filter
modelops import-db --repo ./my-model --type postgresql --schema public --tables "product*,customer*"

# Import and skip proposal creation (dry-run preview)
modelops import-db --repo ./my-model --type postgresql --schema public --dry-run
```
