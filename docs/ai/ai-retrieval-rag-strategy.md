# Retrieval and RAG Strategy

## Principle

Deterministic-first, vector-optional-later.

## Retrieval Layers

### Layer 1 — Exact ID Lookup
- Direct `objects` table query by `id`
- Fast, deterministic, always tried first

### Layer 2 — Structured Query
- SQLite queries over `objects` (type, status, domain)
- SQL: `SELECT * FROM objects WHERE type = 'Attribute' AND domain = '...'`

### Layer 3 — Relationship Expansion
- BFS over `object_relationships` from a seed object
- Controlled depth (default 2)

### Layer 4 — Keyword Search
- Full-text search over generated `search_documents.jsonl`
- Tokenized names, descriptions, IDs

### Layer 5 — Vector Retrieval (Later)
- Embeddings over search documents
- Optional vector DB or in-memory index

## When RAG Is Needed

| Scenario | Layers Used |
|---|---|
| User asks about specific object | 1 + 3 |
| User asks "what attributes relate to sales?" | 2 + 4 |
| User asks broad question about model | 2 + 3 + 4 |
| File-to-model inference | 2 + dataset profile |
| Chat-to-model (open-ended) | 2 + 3 + 4 (+ 5 later) |

## Ranking Signals

1. Object type priority: Attribute > FieldEndpoint > Mapping > ValueList
2. Relationship distance: closer = higher rank
3. Source evidence: objects with validation errors or recent changes
4. Ownership gaps: objects missing owner/steward
5. Usage context: objects in active proposals or issues
6. User target: explicit object IDs in query = highest rank

## Response Budgets

| Workflow | Max Objects | Max Relationships |
|---|---|---|
| file-to-model | 50 | 100 |
| chat-to-model | 30 | 60 |
| trace/impact | 20 | 40 |
| gap suggestion | 40 | 80 |

## Truncation Rules

1. Sort by rank signal score
2. Include top N objects within budget
3. Include relationships only for included objects
4. Add `excluded_count` to bundle metadata

## Exclusions

- Raw dataset rows are never retrieved by default
- Generated artifacts (DB, JSONL) are inputs, not outputs
- Secrets and credentials are filtered at context builder layer
