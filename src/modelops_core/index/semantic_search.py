"""Local-first semantic search using TF-IDF and cosine similarity."""

from __future__ import annotations

import json
import math
import re
import sqlite3
from dataclasses import dataclass
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
