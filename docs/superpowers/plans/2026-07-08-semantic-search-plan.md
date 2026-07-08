# Semantic Object Search Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local-first, stdlib-only semantic ranking layer to the existing object search, exposed through a `--semantic` CLI flag and built automatically during `build-index`.

**Architecture:** A new `src/modelops_core/index/semantic_search.py` module computes TF-IDF vectors from the SQLite `objects` table at index-build time and stores them in a `semantic_index` table plus a `semantic_vocabulary` table. At search time it reranks the existing keyword search candidates by cosine similarity, with optional one-hop relationship-graph query expansion.

**Tech Stack:** Python 3.11 stdlib (`sqlite3`, `json`, `re`, `math`, `dataclasses`, `collections`). Optional `numpy` is allowed for acceleration later, but all tests must pass without it.

## Global Constraints

- Python >=3.11, Pydantic >=2.6, Typer >=0.12, Rich >=13.0, pytest >=8.0.
- No new required runtime dependencies in `modelops_core`; optional extras only.
- No real AI provider calls in tests; mock HTTP / stub adapters only.
- No API keys, secrets, or raw dataset samples in canonical files, prompts, tests, or generated artifacts.
- AI-generated changes must flow through `PatchProposal → validation → human approval → ChangeRequest → apply → audit`.
- All CLI commands must emit stable JSON when passed `--json`.
- Generated artifacts are disposable; canonical files in `model/` are source of truth.

---

## Task 1: Semantic vector module + tests

**Files:**
- Create: `src/modelops_core/index/semantic_search.py`
- Test: `tests/test_semantic_search.py`

**Interfaces:**
- Produces:
  - `_tokenize(text: str) -> list[str]`
  - `_compute_idf(doc_count: int, df: int) -> float`
  - `_magnitude(vector: dict[str, float]) -> float`
  - `_cosine_similarity(a: dict[str, float], b: dict[str, float]) -> float`
  - `SemanticIndexEntry(object_id: str, term_vector: dict[str, float], magnitude: float, term_count: int)`
  - `SemanticSearchResult(object_id: str, object_type: str, semantic_score: float, matched_terms: list[str])`
  - `SemanticIndexBuilder.build(conn: sqlite3.Connection) -> None`
  - `SemanticSearcher.search(...)` (interface finalised in Task 2)

### Step 1: Write the failing tokenizer test

```python
def test_tokenize_lowercase_and_splits():
    from modelops_core.index.semantic_search import _tokenize
    assert _tokenize("Customer Group, KNVV-KDGRP!") == [
        "customer", "group", "knvv", "kdgrp"
    ]
```

Run:

```bash
/Users/dzmitryikharlanau/Developments/martenweave/.venv/bin/python -m pytest tests/test_semantic_search.py::test_tokenize_lowercase_and_splits -v
```

Expected: `ImportError` or `ModuleNotFoundError`.

### Step 2: Create `src/modelops_core/index/semantic_search.py` with tokenizer and math helpers

```python
"""Local-first semantic search using TF-IDF and cosine similarity."""

from __future__ import annotations

import json
import math
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from modelops_core.schemas.registry import get_search_fields

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    """Lowercase and split text into alphanumeric tokens."""
    return _TOKEN_RE.findall(text.lower())


def _term_frequencies(tokens: list[str]) -> dict[str, int]:
    """Return raw term frequency counts."""
    counts: dict[str, int] = {}
    for token in tokens:
        counts[token] = counts.get(token, 0) + 1
    return counts


def _compute_idf(doc_count: int, df: int) -> float:
    """Compute inverse document frequency with smoothing."""
    if doc_count == 0 or df == 0:
        return 0.0
    return math.log(doc_count / df)


def _magnitude(vector: dict[str, float]) -> float:
    """L2 norm of a sparse vector."""
    return math.sqrt(sum(value * value for value in vector.values()))


def _normalize_vector(vector: dict[str, float]) -> dict[str, float]:
    """Return L2-normalized vector (zero vector if magnitude is 0)."""
    mag = _magnitude(vector)
    if mag == 0:
        return {}
    return {term: value / mag for term, value in vector.items()}


def _cosine_similarity(a: dict[str, float], b: dict[str, float]) -> float:
    """Cosine similarity between two sparse vectors."""
    if not a or not b:
        return 0.0
    common_terms = set(a) & set(b)
    if not common_terms:
        return 0.0
    dot = sum(a[term] * b[term] for term in common_terms)
    mag_a = _magnitude(a)
    mag_b = _magnitude(b)
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)
```

Run the tokenizer test again. Expected: PASS.

### Step 3: Write math helper tests

```python
def test_term_frequencies_counts():
    from modelops_core.index.semantic_search import _term_frequencies
    assert _term_frequencies(["a", "b", "a"]) == {"a": 2, "b": 1}


def test_compute_idf_basic():
    from modelops_core.index.semantic_search import _compute_idf
    assert _compute_idf(10, 1) > _compute_idf(10, 5)
    assert _compute_idf(0, 1) == 0.0
    assert _compute_idf(10, 0) == 0.0


def test_cosine_similarity_orthogonal():
    from modelops_core.index.semantic_search import _cosine_similarity
    assert _cosine_similarity({"a": 1.0}, {"b": 1.0}) == 0.0


def test_cosine_similarity_identical():
    from modelops_core.index.semantic_search import _cosine_similarity
    assert _cosine_similarity({"a": 1.0, "b": 1.0}, {"a": 1.0, "b": 1.0}) == 1.0
```

Run:

```bash
/Users/dzmitryikharlanau/Developments/martenweave/.venv/bin/python -m pytest tests/test_semantic_search.py -v
```

Expected: all PASS.

### Step 4: Add the dataclasses and `SemanticIndexBuilder`

Append to `src/modelops_core/index/semantic_search.py`:

```python
@dataclass(frozen=True)
class SemanticIndexEntry:
    """A single object's TF-IDF vector and metadata."""

    object_id: str
    term_vector: dict[str, float]
    magnitude: float
    term_count: int


@dataclass(frozen=True)
class SemanticSearchResult:
    """One semantic search result."""

    object_id: str
    object_type: str
    semantic_score: float
    matched_terms: list[str]


class SemanticIndexBuilder:
    """Builds a TF-IDF semantic index from the SQLite objects table."""

    _DROP_SQL = """
    DROP TABLE IF EXISTS semantic_index;
    DROP TABLE IF EXISTS semantic_vocabulary;
    """

    _CREATE_SQL = """
    CREATE TABLE semantic_vocabulary (
        term TEXT PRIMARY KEY,
        df INTEGER NOT NULL,
        idf REAL NOT NULL
    );
    CREATE TABLE semantic_index (
        object_id TEXT PRIMARY KEY,
        term_vector_json TEXT NOT NULL,
        magnitude REAL NOT NULL,
        term_count INTEGER NOT NULL
    );
    """

    def build(self, conn: sqlite3.Connection) -> None:
        """Rebuild the semantic index from all rows in ``objects``."""
        conn.executescript(self._DROP_SQL)
        conn.executescript(self._CREATE_SQL)

        rows = conn.execute(
            "SELECT id, type, name, title, description, body, frontmatter_json FROM objects"
        ).fetchall()

        doc_count = len(rows)
        term_dfs: dict[str, int] = {}
        entries: list[SemanticIndexEntry] = []

        for row in rows:
            object_id, obj_type, name, title, description, body, frontmatter_json = row
            text = self._extract_text(
                name, title, description, body, frontmatter_json
            )
            tokens = _tokenize(text)
            tf = _term_frequencies(tokens)
            for term in tf:
                term_dfs[term] = term_dfs.get(term, 0) + 1
            entries.append(
                SemanticIndexEntry(
                    object_id=object_id,
                    term_vector={},  # filled after idf computation
                    magnitude=0.0,
                    term_count=len(tokens),
                )
            )

        idf = {
            term: _compute_idf(doc_count, df) for term, df in term_dfs.items()
        }

        # Store vocabulary
        for term, df in term_dfs.items():
            conn.execute(
                "INSERT INTO semantic_vocabulary (term, df, idf) VALUES (?, ?, ?)",
                (term, df, idf[term]),
            )

        # Build weighted vectors
        final_entries: list[tuple[str, str, str, float, int]] = []
        for entry in entries:
            # Re-tokenize to rebuild tf; small repos only, so this is fine.
            row = next(
                r
                for r in rows
                if r[0] == entry.object_id
            )
            text = self._extract_text(
                row[2], row[3], row[4], row[5], row[6]
            )
            tf = _term_frequencies(_tokenize(text))
            vector = {
                term: (1 + math.log(tf_val)) * idf.get(term, 0.0)
                for term, tf_val in tf.items()
            }
            vector = _normalize_vector(vector)
            final_entries.append(
                (
                    entry.object_id,
                    json.dumps(vector, sort_keys=True),
                    _magnitude(vector),
                    entry.term_count,
                )
            )

        for object_id, vector_json, magnitude, term_count in final_entries:
            conn.execute(
                "INSERT INTO semantic_index (object_id, term_vector_json, magnitude, term_count) "
                "VALUES (?, ?, ?, ?)",
                (object_id, vector_json, magnitude, term_count),
            )

    def _extract_text(
        self,
        name: str | None,
        title: str | None,
        description: str | None,
        body: str | None,
        frontmatter_json: str | None,
    ) -> str:
        """Concatenate all searchable text for an object."""
        parts: list[str] = []
        for value in (name, title, description, body):
            if value:
                parts.append(value)

        if frontmatter_json:
            try:
                frontmatter: dict[str, Any] = json.loads(frontmatter_json)
            except json.JSONDecodeError:
                frontmatter = {}
            for field in get_search_fields():
                value = frontmatter.get(field)
                if isinstance(value, str) and value:
                    parts.append(value)

        return " ".join(parts)
```

### Step 5: Write the builder test

```python
def _build_objects_table(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE objects (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            name TEXT,
            title TEXT,
            description TEXT,
            body TEXT,
            source_file TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            frontmatter_json TEXT NOT NULL,
            created_at TEXT,
            updated_at TEXT
        );
        """
    )
    conn.execute(
        "INSERT INTO objects (id, type, name, title, description, body, source_file, content_hash, frontmatter_json) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "ATTR-001",
            "Attribute",
            "Customer Group",
            "Customer Group",
            "Sales-area-dependent customer grouping",
            "# Customer Group",
            "model/ATTR-001.md",
            "hash",
            '{"id": "ATTR-001", "type": "Attribute"}',
        ),
    )
    conn.execute(
        "INSERT INTO objects (id, type, name, title, description, body, source_file, content_hash, frontmatter_json) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "FEP-001",
            "FieldEndpoint",
            "KNVV KDGRP",
            None,
            "SAP field for customer group",
            "# KNVV KDGRP",
            "model/FEP-001.md",
            "hash",
            '{"id": "FEP-001", "type": "FieldEndpoint", "technical_name": "KDGRP"}',
        ),
    )


def test_builder_creates_tables_and_vectors(tmp_path: Path) -> None:
    import sqlite3
    from modelops_core.index.semantic_search import SemanticIndexBuilder

    db = tmp_path / "modelops.db"
    conn = sqlite3.connect(str(db))
    _build_objects_table(conn)
    builder = SemanticIndexBuilder()
    builder.build(conn)

    vocab = conn.execute("SELECT term FROM semantic_vocabulary").fetchall()
    assert ("customer",) in vocab
    index = conn.execute("SELECT object_id, magnitude FROM semantic_index").fetchall()
    assert any(row[0] == "ATTR-001" for row in index)
    conn.close()
```

Run:

```bash
/Users/dzmitryikharlanau/Developments/martenweave/.venv/bin/python -m pytest tests/test_semantic_search.py -v
```

Expected: all PASS.

### Step 6: Commit

```bash
git add src/modelops_core/index/semantic_search.py tests/test_semantic_search.py
git commit -m "feat(index): local TF-IDF semantic index builder"
```

---

## Task 2: Semantic searcher + query expansion

**Files:**
- Modify: `src/modelops_core/index/semantic_search.py`
- Test: `tests/test_semantic_search.py`

**Interfaces:**
- Consumes: `SemanticIndexEntry`, `_cosine_similarity`, `_tokenize`, `_compute_idf`, `_normalize_vector`, `_magnitude`.
- Produces:
  - `SemanticSearcher.search(db_path, query, candidate_ids=None, expand=False, limit=50, min_score=0.0) -> list[SemanticSearchResult]`

### Step 1: Write the failing search test

```python
def test_semantic_search_ranks_related_terms(tmp_path: Path) -> None:
    import sqlite3
    from modelops_core.index.semantic_search import (
        SemanticIndexBuilder,
        SemanticSearcher,
    )

    db = tmp_path / "modelops.db"
    conn = sqlite3.connect(str(db))
    _build_objects_table(conn)
    SemanticIndexBuilder().build(conn)
    conn.close()

    searcher = SemanticSearcher()
    results = searcher.search(db, "customer grouping")
    ids = [r.object_id for r in results]
    assert "ATTR-001" in ids
    assert "FEP-001" in ids
    assert results[0].semantic_score >= results[1].semantic_score
```

Run:

```bash
/Users/dzmitryikharlanau/Developments/martenweave/.venv/bin/python -m pytest tests/test_semantic_search.py::test_semantic_search_ranks_related_terms -v
```

Expected: `AttributeError` — `SemanticSearcher` not defined.

### Step 2: Add `SemanticSearcher` to `semantic_search.py`

Append:

```python
class SemanticSearcher:
    """Search the semantic index using TF-IDF cosine similarity."""

    def search(
        self,
        db_path: Path,
        query: str,
        candidate_ids: set[str] | None = None,
        expand: bool = False,
        limit: int = 50,
        min_score: float = 0.0,
    ) -> list[SemanticSearchResult]:
        """Return objects ranked by semantic similarity to ``query``."""
        query = query.strip()
        if not query or not Path(db_path).exists():
            return []

        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        try:
            if not self._has_index(conn):
                return []

            vocabulary = self._load_vocabulary(conn)
            if not vocabulary:
                return []

            query_vector = self._build_query_vector(query, vocabulary)
            if not query_vector:
                return []

            if expand and candidate_ids:
                query_vector = self._expand_query_vector(
                    conn, query_vector, candidate_ids, vocabulary
                )

            candidates = self._load_candidates(conn, candidate_ids)
            results: list[SemanticSearchResult] = []
            query_terms = set(_tokenize(query))
            for object_id, obj_type, vector in candidates:
                score = _cosine_similarity(query_vector, vector)
                if score < min_score:
                    continue
                matched_terms = [t for t in query_terms if t in vector]
                results.append(
                    SemanticSearchResult(
                        object_id=object_id,
                        object_type=obj_type,
                        semantic_score=round(score, 6),
                        matched_terms=matched_terms,
                    )
                )

            results.sort(key=lambda r: r.semantic_score, reverse=True)
            return results[:limit]
        finally:
            conn.close()

    def _has_index(self, conn: sqlite3.Connection) -> bool:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='semantic_index'"
        ).fetchone()
        return row is not None

    def _load_vocabulary(self, conn: sqlite3.Connection) -> dict[str, float]:
        rows = conn.execute("SELECT term, idf FROM semantic_vocabulary").fetchall()
        return {row["term"]: row["idf"] for row in rows}

    def _build_query_vector(
        self, query: str, vocabulary: dict[str, float]
    ) -> dict[str, float]:
        tf = _term_frequencies(_tokenize(query))
        vector = {
            term: (1 + math.log(tf_val)) * vocabulary.get(term, 0.0)
            for term, tf_val in tf.items()
        }
        return _normalize_vector(vector)

    def _load_candidates(
        self,
        conn: sqlite3.Connection,
        candidate_ids: set[str] | None,
    ) -> list[tuple[str, str, dict[str, float]]]:
        if candidate_ids is not None and not candidate_ids:
            return []
        if candidate_ids:
            placeholders = ", ".join("?" for _ in candidate_ids)
            sql = (
                "SELECT si.object_id, o.type, si.term_vector_json "
                f"FROM semantic_index si JOIN objects o ON o.id = si.object_id "
                f"WHERE si.object_id IN ({placeholders})"
            )
            rows = conn.execute(sql, list(candidate_ids)).fetchall()
        else:
            rows = conn.execute(
                "SELECT si.object_id, o.type, si.term_vector_json "
                "FROM semantic_index si JOIN objects o ON o.id = si.object_id"
            ).fetchall()
        return [
            (row["object_id"], row["type"], json.loads(row["term_vector_json"]))
            for row in rows
        ]

    def _expand_query_vector(
        self,
        conn: sqlite3.Connection,
        query_vector: dict[str, float],
        candidate_ids: set[str],
        vocabulary: dict[str, float],
        expansion_weight: float = 0.3,
        max_relationships: int = 20,
    ) -> dict[str, float]:
        """Blend in one-hop related object vectors."""
        placeholders = ", ".join("?" for _ in candidate_ids)
        rel_rows = conn.execute(
            f"""
            SELECT DISTINCT to_object_id
            FROM object_relationships
            WHERE from_object_id IN ({placeholders})
            LIMIT ?
            """,
            list(candidate_ids) + [max_relationships],
        ).fetchall()
        if not rel_rows:
            return query_vector

        related_ids = {row["to_object_id"] for row in rel_rows}
        related = self._load_candidates(conn, related_ids)
        if not related:
            return query_vector

        expanded = dict(query_vector)
        for _object_id, _obj_type, vector in related:
            for term, value in vector.items():
                expanded[term] = expanded.get(term, 0.0) + value * expansion_weight
        return _normalize_vector(expanded)
```

Run the failing test. Expected: PASS.

### Step 3: Add edge-case tests

```python
def test_semantic_search_empty_query(tmp_path: Path) -> None:
    import sqlite3
    from modelops_core.index.semantic_search import (
        SemanticIndexBuilder,
        SemanticSearcher,
    )

    db = tmp_path / "modelops.db"
    conn = sqlite3.connect(str(db))
    _build_objects_table(conn)
    SemanticIndexBuilder().build(conn)
    conn.close()

    assert SemanticSearcher().search(db, "   ") == []


def test_semantic_search_missing_index(tmp_path: Path) -> None:
    from modelops_core.index.semantic_search import SemanticSearcher

    db = tmp_path / "empty.db"
    conn = __import__("sqlite3").connect(str(db))
    conn.executescript("CREATE TABLE objects (id TEXT PRIMARY KEY);")
    conn.close()
    assert SemanticSearcher().search(db, "customer") == []
```

Run full semantic search test file. Expected: all PASS.

### Step 4: Commit

```bash
git add src/modelops_core/index/semantic_search.py tests/test_semantic_search.py
git commit -m "feat(index): semantic searcher with relationship expansion"
```

---

## Task 3: Integrate semantic index into build-index

**Files:**
- Modify: `src/modelops_core/index/sqlite_builder.py` (after `_insert_objects` and `_insert_relationships`)
- Modify: `src/modelops_core/index/query_service.py` (new wrapper)
- Test: `tests/test_index_builder.py` (or add to `tests/test_semantic_search.py`)

### Step 1: Import and call `SemanticIndexBuilder` in `sqlite_builder.py`

At the top of `src/modelops_core/index/sqlite_builder.py` add:

```python
from modelops_core.index.semantic_search import SemanticIndexBuilder
```

In the build function, after `_insert_objects` and `_insert_relationships` and before the manifest, add:

```python
SemanticIndexBuilder().build(conn)
```

### Step 2: Add convenience wrapper in `query_service.py`

At the top of `src/modelops_core/index/query_service.py` add:

```python
from modelops_core.index.semantic_search import SemanticSearcher
```

Append the function:

```python
def semantic_search_objects(
    db_path: Path,
    query: str,
    candidate_ids: set[str] | None = None,
    expand: bool = False,
    limit: int = 50,
    min_score: float = 0.0,
) -> list[Any]:
    """Semantic reranking over a candidate set.

    If ``candidate_ids`` is ``None`` all indexed objects are scored.
    """
    return SemanticSearcher().search(
        db_path=db_path,
        query=query,
        candidate_ids=candidate_ids,
        expand=expand,
        limit=limit,
        min_score=min_score,
    )
```

### Step 3: Add integration test

```python
def test_build_index_creates_semantic_index(tmp_path: Path) -> None:
    import sqlite3
    from modelops_core.index.sqlite_builder import build_index

    model_dir = tmp_path / "model"
    model_dir.mkdir()
    generated = tmp_path / "generated"
    generated.mkdir()
    (model_dir / "DOMAIN-EXAMPLE.md").write_text(
        "---\nid: DOMAIN-EXAMPLE\ntype: MasterDataDomain\nstatus: active\nname: Example Domain\n---\n\n# Example\n"
    )

    build_index(repo_root=tmp_path)

    db = generated / "modelops.db"
    conn = sqlite3.connect(str(db))
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='semantic_index'"
    ).fetchone()
    assert row is not None
    conn.close()
```

Run:

```bash
/Users/dzmitryikharlanau/Developments/martenweave/.venv/bin/python -m pytest tests/test_semantic_search.py tests/test_index_builder.py -v
```

Expected: all PASS.

### Step 4: Commit

```bash
git add src/modelops_core/index/sqlite_builder.py src/modelops_core/index/query_service.py tests/test_semantic_search.py
git commit -m "feat(index): build semantic index during build-index"
```

---

## Task 4: Add `--semantic` flag to CLI search

**Files:**
- Modify: `src/modelops_core/cli.py` (`search` command around line 5573)
- Test: `tests/test_query_service.py` or new `tests/test_semantic_cli.py`

### Step 1: Add parameters to the `search` command

Change the signature of `search(...)` in `src/modelops_core/cli.py` to include:

```python
semantic: bool = typer.Option(False, "--semantic", help="Rerank keyword results by local semantic similarity."),
semantic_expand: bool = typer.Option(False, "--semantic-expand", help="Expand query with one-hop related object terms."),
```

### Step 2: Import `semantic_search_objects`

At the top of `src/modelops_core/cli.py` (where `query_service` imports live), import:

```python
from modelops_core.index.query_service import (
    ...,
    semantic_search_objects,
)
```

### Step 3: Implement semantic branch

Inside the `search` command, after keyword results are obtained and before the table/JSON output, add:

```python
if semantic:
    candidate_ids = {r.object_id for r in results}
    semantic_results = semantic_search_objects(
        db_path=db_path,
        query=query,
        candidate_ids=candidate_ids,
        expand=semantic_expand,
        limit=limit,
    )
    semantic_by_id = {r.object_id: r for r in semantic_results}
    # Preserve keyword filters but attach semantic scores where available.
    for r in results:
        sr = semantic_by_id.get(r.object_id)
        if sr:
            r.score = sr.semantic_score
            r.matched_fields = r.matched_fields + ["semantic:" + t for t in sr.matched_terms]
    results.sort(key=lambda r: r.score, reverse=True)
```

In the JSON output, conditionally add semantic fields:

```python
result_obj = {
    "object_id": r.object_id,
    "object_type": r.object_type,
    "status": r.status,
    "name": r.name,
    "title": r.title,
    "domain": r.domain,
    "source_file": r.source_file,
    "score": r.score,
    "matched_fields": r.matched_fields,
}
if semantic:
    result_obj["semantic_score"] = r.score
    result_obj["semantic_matched_terms"] = [
        f.removeprefix("semantic:") for f in r.matched_fields if f.startswith("semantic:")
    ]
```

### Step 4: Write CLI test

```python
def test_cli_search_semantic_json(tmp_path: Path) -> None:
    from typer.testing import CliRunner
    from modelops_core.cli import app

    repo = tmp_path / "repo"
    model_dir = repo / "model"
    model_dir.mkdir(parents=True)
    generated = repo / "generated"
    generated.mkdir()

    db = generated / "modelops.db"
    conn = __import__("sqlite3").connect(str(db))
    conn.executescript(
        """
        CREATE TABLE objects (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            name TEXT,
            title TEXT,
            description TEXT,
            body TEXT,
            source_file TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            frontmatter_json TEXT NOT NULL,
            created_at TEXT,
            updated_at TEXT
        );
        """
    )
    conn.execute(
        "INSERT INTO objects VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "ATTR-001", "Attribute", "Customer Group", "Customer Group",
            "Sales-area-dependent customer grouping", "# Customer Group",
            "model/ATTR-001.md", "hash", '{"id": "ATTR-001", "type": "Attribute"}',
            None, None,
        ),
    )
    conn.execute(
        "INSERT INTO objects VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "FEP-001", "FieldEndpoint", "KNVV KDGRP", None,
            "SAP field for customer group", "# KNVV KDGRP",
            "model/FEP-001.md", "hash", '{"id": "FEP-001", "type": "FieldEndpoint", "technical_name": "KDGRP"}',
            None, None,
        ),
    )
    from modelops_core.index.semantic_search import SemanticIndexBuilder
    SemanticIndexBuilder().build(conn)
    conn.close()

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["search", "customer grouping", "--repo", str(repo), "--semantic", "--json"],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "results" in data
    assert data["total_count"] == 2
    assert all("semantic_score" in r for r in data["results"])
    assert data["results"][0]["semantic_score"] >= data["results"][1]["semantic_score"]
```

Run:

```bash
/Users/dzmitryikharlanau/Developments/martenweave/.venv/bin/python -m pytest tests/test_semantic_search.py tests/test_query_service.py -v
```

Expected: all PASS.

### Step 5: Commit

```bash
git add src/modelops_core/cli.py tests/test_semantic_search.py
git commit -m "feat(cli): --semantic flag for semantic object search"
```

---

## Task 5: Verification and example repo validation

**Files:** none (verification only)

### Step 1: Run focused tests

```bash
/Users/dzmitryikharlanau/Developments/martenweave/.venv/bin/python -m pytest tests/test_semantic_search.py tests/test_query_service.py tests/test_index_builder.py -v
```

Expected: all PASS.

### Step 2: Run full validation ladder

```bash
/Users/dzmitryikharlanau/Developments/martenweave/.venv/bin/python -m pytest -q && \
/Users/dzmitryikharlanau/Developments/martenweave/.venv/bin/python -m ruff check .
```

Expected: pytest passes, ruff clean.

### Step 3: Example repo smoke test

```bash
PYTHON=/Users/dzmitryikharlanau/Developments/martenweave/.venv/bin/python
$PYTHON -m modelops_core.cli build-index --repo examples/customer_bp_model --jsonl
$PYTHON -m modelops_core.cli search "customer grouping" --repo examples/customer_bp_model --semantic --json
```

Expected: JSON output with `ATTR-CUST-SALES-CUSTOMER-GROUP` and `FEP-S4-KNVV-KDGRP` near the top.

### Step 4: Commit any fixes and write report

Write a short report to `.superpowers/sdd/task-3-2-report.md` summarising commits, test results, and any deviations.

---

## Spec coverage check

| Spec section | Task |
|---|---|
| Local TF-IDF semantic index (3.1) | Task 1 |
| Search-time reranking (3.2) | Task 2 |
| Model-aware query expansion (3.3) | Task 2 (`semantic_expand`) |
| Optional numpy acceleration (3.4) | Not implemented (stdlib-only; numpy optional can be added later without breaking tests) |
| New module interfaces (4.1) | Tasks 1–2 |
| CLI `--semantic` (4.2) | Task 4 |
| Build-index integration (4.3) | Task 3 |
| Error handling and limits (5) | Tasks 2 and 4 |
| Testing strategy (6) | All tasks |
| No new required deps (7) | Tasks 1–4 |
| Success criteria (8) | Task 5 |

**Gap:** numpy acceleration is explicitly deferred; it is not required to meet success criteria and keeping it out preserves the no-required-deps constraint.
