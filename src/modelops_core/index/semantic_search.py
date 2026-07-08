"""Local-first semantic search using TF-IDF and cosine similarity."""

from __future__ import annotations

import json
import math
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from modelops_core.errors import ResourceLimitExceeded
from modelops_core.schemas.registry import get_search_fields

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _stem(token: str) -> str:
    """Apply conservative English stemming so variants like ``grouping`` match ``group``."""
    if len(token) > 4 and token.endswith("ing"):
        return token[:-3]
    if len(token) > 3 and token.endswith("ed"):
        return token[:-2]
    if len(token) > 3 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 3 and token.endswith("es") and not token.endswith(("ss", "us", "is")):
        return token[:-2]
    if len(token) > 3 and token.endswith("s") and not token.endswith(("ss", "us")):
        return token[:-1]
    return token


def _tokenize(text: str) -> list[str]:
    """Lowercase, split, and stem text into alphanumeric tokens."""
    return [_stem(t) for t in _TOKEN_RE.findall(text.lower())]


def _term_frequencies(tokens: list[str]) -> dict[str, int]:
    """Return raw term frequency counts."""
    counts: dict[str, int] = {}
    for token in tokens:
        counts[token] = counts.get(token, 0) + 1
    return counts


def _compute_idf(doc_count: int, df: int) -> float:
    """Compute inverse document frequency with smoothing.

    The +1 smoothing guarantees that terms appearing in every document still
    contribute a small non-zero weight, preventing empty query/document vectors
    in tiny corpora.
    """
    if doc_count == 0 or df == 0:
        return 0.0
    return math.log(doc_count / df + 1)


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
    if a == b:
        return 1.0
    common_terms = set(a) & set(b)
    if not common_terms:
        return 0.0
    dot = sum(a[term] * b[term] for term in common_terms)
    mag_a = _magnitude(a)
    mag_b = _magnitude(b)
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


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
        final_entries: list[tuple[str, str, float, int]] = []
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
        conn.commit()

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
        expand_candidate_ids: set[str] | None = None,
        max_objects: int | None = None,
    ) -> list[SemanticSearchResult]:
        """Return objects ranked by semantic similarity to ``query``.

        ``candidate_ids`` restricts which objects are scored. ``expand`` uses
        one-hop relationships from ``expand_candidate_ids`` (falling back to
        ``candidate_ids``) to broaden the query vector.

        ``max_objects`` enforces ``RepoConfig.resource_limits.max_export_objects``:
        if more candidates would be loaded than allowed, ``ResourceLimitExceeded``
        is raised so callers can fall back gracefully.
        """
        query = query.strip()
        if not query or not Path(db_path).exists():
            return []

        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        try:
            expansion_ids = (
                expand_candidate_ids
                if expand_candidate_ids is not None
                else candidate_ids
            )
            if not self._has_index(conn, expand=expand, candidate_ids=expansion_ids):
                return []

            vocabulary = self._load_vocabulary(conn)
            if not vocabulary:
                return []

            query_vector = self._build_query_vector(query, vocabulary)
            if not query_vector:
                return []

            if expand and expansion_ids:
                query_vector = self._expand_query_vector(
                    conn, query_vector, expansion_ids, vocabulary
                )

            candidates = self._load_candidates(conn, candidate_ids)
            if max_objects is not None and len(candidates) > max_objects:
                raise ResourceLimitExceeded(
                    resource="max_export_objects",
                    message=(
                        f"Semantic search candidate count ({len(candidates)}) exceeds "
                        f"the configured max_export_objects limit ({max_objects}). "
                        "Rerun with a narrower query or increase "
                        "resource_limits.max_export_objects."
                    ),
                )
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

    def _has_index(
        self,
        conn: sqlite3.Connection,
        expand: bool = False,
        candidate_ids: set[str] | None = None,
    ) -> bool:
        """Verify required semantic-search tables exist.

        Expansion requires ``object_relationships`` only when it will actually
        be invoked (``expand=True`` with non-empty ``candidate_ids``).
        """
        required = ["semantic_index", "semantic_vocabulary"]
        if expand and candidate_ids:
            required.append("object_relationships")
        for table in required:
            row = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table,),
            ).fetchone()
            if row is None:
                return False
        return True

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
