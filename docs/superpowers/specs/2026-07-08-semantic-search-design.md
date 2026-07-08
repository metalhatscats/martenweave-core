# Semantic Object Search — Design Spec

**Date:** 2026-07-08  
**Status:** Draft (pending implementation plan)  
**Scope:** Task 3.2 of the AI-readiness roadmap for Martenweave Core.

## 1. Goal

Add a local-first, deterministic **semantic ranking** layer to the existing object search so that AI agents and human users can discover canonical objects even when their query words do not exactly match indexed text. The feature must work offline, add no required runtime dependencies, and remain transparent to the existing keyword search and query pipelines.

## 2. Non-goals

- No external vector database or embedding service as a hard dependency.
- No cloud API calls for embeddings or reranking.
- No changes to canonical file formats or the validation pipeline.
- No required heavy ML libraries (numpy, sentence-transformers, etc.).

## 3. Proposed approach

### 3.1 Local TF-IDF semantic index

At `build-index` time we compute a lightweight TF-IDF vector for every indexed object from its searchable text:

- `name`, `title`, `description`, `body`
- All registry `search_fields` extracted from `frontmatter_json`

Tokenization is simple and dependency-free: lowercase, split on non-alphanumeric characters, drop empty tokens. We do **not** ship a stop-word list; instead we rely on IDF to de-emphasise corpus-common terms.

For each object we persist:

- `object_id`
- `term_vector_json` — a JSON map of `term -> weighted tf-idf score`
- `magnitude` — precomputed L2 norm for fast cosine similarity
- `term_count` — raw token count (for diagnostics)

Storage is a new SQLite table `semantic_index` in the existing `modelops.db`. Generated artifacts remain disposable and rebuildable.

### 3.2 Search-time reranking

A new `SemanticSearcher.search(...)` method:

1. Builds a TF-IDF vector for the query using the same vocabulary and IDF weights stored in the index.
2. Loads candidate object vectors. The default candidate set is the result of the existing keyword `search_objects` (this keeps the working set small and respects existing filters). If the keyword search returns no candidates, semantic search returns an empty result.
3. Computes cosine similarity between the query vector and each candidate vector.
4. Returns results sorted by `semantic_score`, annotated with the score and the terms that contributed.

A `--semantic` flag is added to the existing CLI `search` command. When present the CLI returns results reranked by semantic score while preserving the stable `--json` contract.

### 3.3 Model-aware query expansion (unique value)

To make the search model-aware without external data, we optionally expand the query vector with terms from objects that are **graph-adjacent** to keyword-matched objects:

- For each keyword-matched object, walk one hop of `object_relationships`.
- Add the `name`/`title` tokens of related objects to the query vector with a lower weight.
- This lets a query like *"customer group"* also surface the linked `FEP-S4-KNVV-KDGRP` field endpoint even if the user did not mention `KNVV` or `KDGRP`.

Expansion is controlled by an optional `expand: bool` parameter and is capped by `resource_limits.max_context_relationships` to avoid runaway computation.

### 3.4 Optional numpy acceleration

The implementation uses only the Python standard library (`math`, `collections`, `json`, `re`, `sqlite3`). If `numpy` is installed, an internal helper may use it for dot-product and norm calculations, but all behaviour and test assertions must pass without it.

## 4. Interfaces

### 4.1 New module

`src/modelops_core/index/semantic_search.py`

```python
@dataclass
class SemanticSearchResult:
    object_id: str
    object_type: str
    semantic_score: float
    matched_terms: list[str]

class SemanticIndexBuilder:
    def build(self, conn: sqlite3.Connection) -> None: ...

class SemanticSearcher:
    def search(
        self,
        db_path: Path,
        query: str,
        candidate_ids: set[str] | None = None,
        expand: bool = False,
        limit: int = 50,
        min_score: float = 0.0,
    ) -> list[SemanticSearchResult]: ...
```

### 4.2 CLI change

```bash
modelops search "customer group" --semantic --repo ./my-model --json
```

JSON output reuses the existing search result schema and adds `semantic_score` and `semantic_matched_terms` when `--semantic` is used.

### 4.3 Build-index change

`src/modelops_core/index/sqlite_builder.py` calls `SemanticIndexBuilder().build(conn)` after object/relationship insertion.

## 5. Error handling and limits

- If `semantic_index` is missing, `semantic_search_objects` returns an empty list and the CLI prints a graceful warning.
- If `query` is empty or whitespace, return empty results.
- Respect `RepoConfig.resource_limits.max_export_objects` when loading candidate vectors.
- Unknown exceptions during semantic scoring are caught and logged; the CLI falls back to keyword results so search never hard-fails.

## 6. Testing strategy

- Unit tests for tokenizer, TF-IDF weights, cosine similarity, and magnitude caching.
- Unit tests for `SemanticIndexBuilder` against an in-memory SQLite schema.
- Unit tests for `SemanticSearcher` with a hand-built small corpus.
- CLI tests verifying `--semantic` JSON contract and graceful fallback when index table is missing.
- No real network calls or API keys.

## 7. Dependencies

- **Required:** none (stdlib only).
- **Optional:** `numpy` may be used for faster vector math if present, but all tests must pass without it.

## 8. Success criteria

- `modelops search "customer grouping" --semantic --json` returns `FEP-S4-KNVV-KDGRP` and `ATTR-CUST-SALES-CUSTOMER-GROUP` near the top in the customer example repo.
- Existing `modelops search` behaviour is unchanged when `--semantic` is not supplied.
- Full test suite remains green; ruff clean.
