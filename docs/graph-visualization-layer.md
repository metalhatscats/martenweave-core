<!-- modelops-freshness-ignore: all -->

# Graph Visualization Layer

## Goal
Define how the future one-screen workspace should visualize model lineage, system flows, interfaces, rules, and impact without making graph visualization part of the core truth layer.

## Principle

The core remains backend-only. Graph visualization is a frontend concern that consumes exported graph data. The backend does not know which library renders the graph.

## Recommended Library: React Flow / xyflow

**First choice for the Martenweave UI:** [React Flow](https://reactflow.dev/) (now xyflow)

Why React Flow:

- **React-native** — fits naturally into a React-based UI stack.
- **Interactive editing** — supports node selection, pan, zoom, and edge highlighting out of the box.
- **Custom nodes** — allows rich node rendering (status badges, type icons, ownership avatars).
- **Controlled state** — the UI owns node positions and selection state; the backend provides data only.
- **Mature ecosystem** — layout plugins (e.g., `react-flow-renderer` with Dagre or ELK), minimap, controls.
- **Performance** — handles medium-sized graphs (hundreds of nodes) well. For larger graphs, virtualization or level-of-detail nodes can be added.

Why not Cytoscape.js as first choice:

- Cytoscape.js is excellent for layout-heavy exploration and large graphs (1000+ nodes).
- It is less natural for interactive editing workflows where users rearrange nodes manually.
- **Recommendation:** Use Cytoscape.js as a secondary view for large lineage exploration or as an alternative layout engine if React Flow performance becomes limiting.

Why not D3:

- D3 offers maximum flexibility but requires significant custom code for interaction, layouts, and state management.
- **Recommendation:** Use D3 only for highly specialized visualizations (e.g., custom radial ownership charts) that React Flow or Cytoscape.js cannot express easily.

## Graph View Types

### 1. Object Trace Graph

**Purpose:** Show all objects reachable from a given object via lineage edges.

**Data source:** `martenweave trace <id> --json`

**Visual conventions:**
- Root object centered or highlighted.
- Upstream objects to the left, downstream to the right.
- Edge labels show relationship type on hover.
- Color by object type.

### 2. System Lineage Graph

**Purpose:** Show how data moves across systems, interfaces, and transformations.

**Data source:** `modelops graph-export --format jsonl` filtered to system-lineage node types.

**Visual conventions:**
- Systems as large rectangles.
- Interfaces and flows as connectors between systems.
- Steps inside a flow grouped or nested.
- Direction arrows on edges.

### 3. Interface Flow Graph

**Purpose:** Focus on a single integration flow and its steps.

**Data source:** Filtered trace starting from an `IntegrationFlow` object.

**Visual conventions:**
- Linear or pipeline layout (extract → transform → load).
- Transformation rules attached to steps as annotation nodes.
- Source/target endpoints shown at step boundaries.

### 4. Impact Graph

**Purpose:** Show upstream and downstream impact of changing an object.

**Data source:** `martenweave impact <id> --json`

**Visual conventions:**
- Root object in the center.
- Upstream objects to the left (sources), downstream to the right (affected).
- Depth indicated by concentric layers or distance.
- Affected objects colored by severity (if available).

### 5. Ownership / Governance Graph

**Purpose:** Show who owns, stewards, and approves what.

**Data source:** `modelops graph-export --format jsonl` filtered to governance edges.

**Visual conventions:**
- People and teams as circular nodes.
- Objects as rectangular nodes.
- Edge labels: "owns", "stewards", "approves".
- Optional: highlight objects with no owner as gaps.

### 6. Value List / Value Mapping Graph

**Purpose:** Show value list hierarchies and mappings.

**Data source:** `modelops graph-export --format jsonl` filtered to `ValueList` and `ValueMapping` nodes.

**Visual conventions:**
- Tree layout for value list hierarchies.
- Side-by-side columns for source and target value lists.
- Mapping edges drawn across columns.

## Graph JSON Contract

The UI receives graph data from the backend via the graph projection export contract (issue #76). The contract is format-agnostic; the UI can consume JSONL, a JSON API response, or WebSocket messages.

### Minimal node shape

```json
{
  "node_id": "ATTR-CUST-SALES-CUSTOMER-GROUP",
  "node_type": "Attribute",
  "node_label": "Customer Group",
  "status": "draft",
  "domain": "DOMAIN-CUSTOMER-BP"
}
```

### Minimal edge shape

```json
{
  "from_node_id": "ATTR-CUST-SALES-CUSTOMER-GROUP",
  "to_node_id": "FEP-S4-KNVV-KDGRP",
  "edge_type": "implemented_by_field",
  "edge_class": "core_dependency"
}
```

### UI-specific enrichments (computed on the frontend)

The UI may add computed fields without mutating the backend contract:

- `x`, `y` — node positions (user-arranged or auto-layout)
- `selected` — boolean selection state
- `expanded` — whether a collapsed group is open
- `highlighted` — whether the node matches a search query

## Layout Strategies

| View Type | Recommended Layout | Library Support |
|---|---|---|
| Object trace | Hierarchical (left-to-right) | Dagre + React Flow |
| System lineage | Hierarchical or force-directed | Dagre / ELK + React Flow |
| Interface flow | Linear pipeline | Custom + React Flow |
| Impact | Concentric or hierarchical | Dagre + React Flow |
| Ownership | Force-directed or radial | Cytoscape.js or D3 |
| Value mapping | Bipartite or tree | Dagre + React Flow |

## Performance Guidelines

- **< 200 nodes:** Render all nodes. Use React Flow with Dagre layout.
- **200–1,000 nodes:** Use level-of-detail nodes (collapse domains, show counts). Lazy-load edge labels.
- **> 1,000 nodes:** Switch to Cytoscape.js or add aggressive filtering (depth limit, type filter). Consider server-side path pre-computation.

## Out of Scope

- **Live graph editing** — moving nodes in the UI does not write back to canonical files. Position data is UI-local or stored in UI preferences.
- **Graph mutations from UI** — creating or deleting objects in the graph view is not supported in v0.1. Users create PatchProposals through forms or notes.
- **3D visualization** — not evaluated. 2D is sufficient for data model lineage.
- **Real-time updates** — the UI refreshes graph data on explicit reload or periodic polling.

## Safety Notes

- The backend never executes frontend-supplied graph queries. All queries are generated from validated CLI/API commands.
- No secrets are included in graph exports consumed by the UI.
- The UI is a read-only consumer of graph data. Write operations go through the existing PatchProposal workflow.

## Future Work

- Add a `martenweave serve` command that exposes a read-only HTTP API for graph data, enabling the UI to fetch nodes and edges on demand.
- Add filtering parameters to graph export (e.g., `--depth 3`, `--types Attribute,FieldEndpoint`).
- Evaluate WebSocket push for incremental graph updates when canonical files change.
