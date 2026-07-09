<!-- modelops-freshness-ignore: all -->

# Neo4j Graph Projection Evaluation

## Goal
Evaluate whether Neo4j should be used as an optional graph projection layer for Martenweave lineage, trace, impact analysis, and system flow exploration.

## Current State

Martenweave stores lineage edges in a local SQLite database (`generated/modelops.db`). Trace and impact analysis use in-memory BFS over these edges. The current design supports:

- Up to ~10,000 canonical objects per repository (configurable limit)
- Bidirectional BFS up to depth 5 for trace, depth 2 for impact
- All relationship types traversable without filtering
- Zero external dependencies for core operations

## What Neo4j Could Improve

### 1. Multi-hop lineage queries

SQLite BFS loads all edges into memory and walks them iteratively. For deep lineage (5+ hops) across thousands of objects, this is acceptable on modern hardware but becomes slower as the graph grows.

Neo4j's native graph storage and Cypher path queries can traverse multi-hop relationships efficiently without loading the entire graph into application memory.

**Verdict:** Modest improvement for typical repository sizes. Significant improvement only for enterprise-scale graphs (>50,000 nodes, >200,000 edges).

### 2. System-to-system flow analysis

With the new system lineage model (issue #65), flows cross systems, interfaces, endpoints, and transformations. Finding all paths between two systems is a path-finding problem.

Neo4j's `shortestPath` and `allSimplePaths` algorithms are purpose-built for this. SQLite BFS can compute the same results but requires custom application code.

**Verdict:** Useful for complex multi-hop system landscapes. Overkill for simple two-system flows.

### 3. Impact paths across interfaces and transformations

Impact analysis currently returns a flat list of affected objects. A Neo4j projection could preserve the exact path shape: which interface → which flow → which step → which transformation → which field.

**Verdict:** Nice-to-have for visualization. The same path can be reconstructed from SQLite edges with post-processing.

### 4. Ownership and governance network exploration

Graph algorithms like PageRank, betweenness centrality, and community detection can reveal which objects are most connected, which teams own critical paths, and where governance gaps exist.

**Verdict:** High value for enterprise governance dashboards. Requires the Graph Data Science (GDS) library, which adds complexity.

### 5. Graph algorithms for centrality, hotspots, communities, dependency risk

Neo4j GDS provides:
- **Degree centrality** — find most referenced attributes/fields
- **Betweenness centrality** — find bottleneck objects
- **Community detection** — cluster related domains/entities
- **Dependency risk scoring** — identify objects with many downstream dependents

**Verdict:** High analytical value, but GDS is a separate library with its own licensing and runtime requirements.

## What Neo4j Must Not Do

| Constraint | Rationale |
|---|---|
| **Must not replace canonical files** | Markdown + YAML frontmatter remains the source of truth. Neo4j is a generated projection. |
| **Must not be required for v0.1 core** | Core must remain local-first with zero external database dependencies. |
| **Must not store secrets** | Connection strings, API keys, and credentials never enter the graph. |
| **Must not allow direct mutation** | All changes to canonical objects go through PatchProposal / ChangeRequest workflow. |
| **Must not lock in to Neo4j specifically** | The graph projection export contract (issue #76) must remain engine-agnostic. |

## Complexity and Cost Analysis

| Factor | SQLite (current) | Neo4j (optional) |
|---|---|---|
| **Install cost** | Zero (embedded) | Docker container or desktop install |
| **Runtime cost** | Zero admin | JVM process, memory tuning |
| **Developer burden** | SQL knowledge | Cypher + graph modeling + driver setup |
| **Test complexity** | In-memory SQLite | Testcontainers or mock driver |
| **Distribution** | Single binary / pip install | Requires separate Neo4j install |
| **Licensing** | Public domain | Community Edition (free), Enterprise (paid) |
| **Backup / portability** | Single `.db` file | Database dump + config |
| **Query language** | SQL | Cypher |

## Go / No-Go Criteria

### Go (introduce Neo4j as optional projection) if:

- A customer or user has >50,000 canonical objects and SQLite BFS becomes measurably slow.
- There is a concrete need for graph algorithms (centrality, community detection, dependency risk).
- A UI team wants to use Neo4j Bloom or a Cypher-based visualization layer.
- The team has operational experience running Neo4j and accepts the runtime cost.

### No-Go (stay with SQLite) if:

- Repository sizes remain under ~10,000 objects.
- Impact and trace performance is acceptable (<1s for typical queries).
- No graph algorithm requirements exist.
- The team values single-binary portability over analytical power.

## Recommendation

**No-Go for v0.1. Stay with SQLite as the sole index backend.**

Rationale:
- The current BFS implementation is fast enough for the target repository sizes.
- The graph projection export contract (issue #76) already defines how data can be exported to Neo4j when needed.
- Adding Neo4j now would introduce operational complexity before product-market fit is confirmed.
- SQLite is sufficient for CLI-driven workflows and API backends.

**Re-evaluate after:**
- A user reports SQLite performance issues with a real repository >20,000 objects.
- A concrete UI or analytics use case requires graph algorithms.
- The project has resources to maintain an optional Neo4j connector and documentation.

## Future Integration Path

If Neo4j is introduced later, the integration should follow this pattern:

1. **Export** — Use the existing `modelops graph-export --format neo4j-csv` command (issue #76).
2. **Import** — Load CSVs into Neo4j with `neo4j-admin import` or `LOAD CSV`.
3. **Optional connector** — Implement a `Neo4jConnector` class that conforms to `ConnectorAdapter` if live queries are needed.
4. **No core dependency** — Keep all Neo4j code in an optional module with lazy imports.

## Out of Scope

- **Live Neo4j sync** — Real-time synchronization from canonical files to Neo4j is not evaluated here.
- **Neo4j Aura / Cloud** — Managed Neo4j services have different cost and network considerations.
- **Alternative graph databases** — Amazon Neptune, ArangoDB, and TigerGraph are not evaluated. The export contract remains agnostic.

## Acceptance Criteria

- [x] Clear decision framework for Neo4j go/no-go.
- [x] Neo4j positioned as optional generated projection, not model truth.
- [x] Evaluation covers complexity, install/runtime cost, developer burden, and product value.
- [x] Design explains when SQLite is enough and when Neo4j becomes justified.
- [x] Future integration path documented without adding code.
