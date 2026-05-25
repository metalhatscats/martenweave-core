"""Tests for connector adapter interface and local file connector."""

from __future__ import annotations

from pathlib import Path

import pytest

from modelops_core.connectors import (
    ConnectorAdapter,
    ConnectorError,
    ConnectorSourceInfo,
    LocalFileConnector,
)
from modelops_core.schemas.source_registry import SourceEntry

# ---------------------------------------------------------------------------
# LocalFileConnector tests
# ---------------------------------------------------------------------------


def test_local_file_connector_type() -> None:
    conn = LocalFileConnector()
    assert conn.connector_type == "local_file"


def test_local_file_fetch_metadata(tmp_path: Path) -> None:
    test_file = tmp_path / "data.csv"
    test_file.write_text("a,b,c\n1,2,3\n")

    conn = LocalFileConnector(base_path=tmp_path)
    meta = conn.fetch_metadata("data.csv")

    assert meta.source_id == "data.csv"
    assert meta.source_type == "local_file"
    assert meta.display_name == "data.csv"
    assert meta.size_bytes == test_file.stat().st_size
    assert meta.checksum is not None
    assert len(meta.checksum) == 16


def test_local_file_fetch_metadata_missing() -> None:
    conn = LocalFileConnector()
    with pytest.raises(ConnectorError) as exc_info:
        conn.fetch_metadata("/does/not/exist.txt")
    assert exc_info.value.connector_type == "local_file"
    assert exc_info.value.action == "fetch_metadata"


def test_local_file_fetch_content(tmp_path: Path) -> None:
    test_file = tmp_path / "data.csv"
    test_file.write_text("hello,world\n")

    conn = LocalFileConnector(base_path=tmp_path)
    content = conn.fetch_content("data.csv")
    assert content == b"hello,world\n"


def test_local_file_fetch_content_missing() -> None:
    conn = LocalFileConnector()
    with pytest.raises(ConnectorError) as exc_info:
        conn.fetch_content("/does/not/exist.txt")
    assert exc_info.value.action == "fetch_content"


def test_local_file_write_content(tmp_path: Path) -> None:
    conn = LocalFileConnector(base_path=tmp_path)
    ok = conn.write_content("out/report.csv", b"a,b\n1,2\n")
    assert ok is True
    assert (tmp_path / "out" / "report.csv").read_bytes() == b"a,b\n1,2\n"


def test_local_file_list_sources(tmp_path: Path) -> None:
    (tmp_path / "a.csv").write_text("1\n")
    (tmp_path / "b.csv").write_text("2\n")

    conn = LocalFileConnector(base_path=tmp_path)
    sources = conn.list_sources()
    ids = {s.source_id for s in sources}
    assert "a.csv" in ids
    assert "b.csv" in ids


def test_local_file_to_source_entry(tmp_path: Path) -> None:
    test_file = tmp_path / "data.csv"
    test_file.write_text("x\n")

    conn = LocalFileConnector(base_path=tmp_path)
    entry = conn.to_source_entry("data.csv")

    assert isinstance(entry, SourceEntry)
    assert entry.source_id == "data.csv"
    assert entry.source_type == "local_file"
    assert entry.file_hash is not None
    assert entry.file_path is not None


# ---------------------------------------------------------------------------
# Protocol conformance
# ---------------------------------------------------------------------------


def test_local_file_implements_protocol() -> None:
    """Static typing check: LocalFileConnector satisfies ConnectorAdapter."""
    conn: ConnectorAdapter = LocalFileConnector()
    assert conn.connector_type == "local_file"


# ---------------------------------------------------------------------------
# Mocked cloud connector test (demonstrates future extensibility)
# ---------------------------------------------------------------------------


class MockCloudConnector:
    """A mock cloud connector for testing the protocol boundary."""

    def __init__(self, fixtures: dict[str, bytes] | None = None) -> None:
        self._fixtures = fixtures or {}

    @property
    def connector_type(self) -> str:
        return "mock_cloud"

    def list_sources(self, prefix: str = "") -> list[ConnectorSourceInfo]:
        return [
            ConnectorSourceInfo(
                source_id=k,
                source_type="mock_cloud",
                display_name=k,
            )
            for k in self._fixtures
            if not prefix or k.startswith(prefix)
        ]

    def fetch_metadata(self, source_id: str) -> ConnectorSourceInfo:
        if source_id not in self._fixtures:
            raise ConnectorError(
                "Not found",
                connector_type=self.connector_type,
                action="fetch_metadata",
            )
        return ConnectorSourceInfo(
            source_id=source_id,
            source_type="mock_cloud",
            display_name=source_id,
            size_bytes=len(self._fixtures[source_id]),
        )

    def fetch_content(self, source_id: str) -> bytes:
        if source_id not in self._fixtures:
            raise ConnectorError(
                "Not found",
                connector_type=self.connector_type,
                action="fetch_content",
            )
        return self._fixtures[source_id]

    def write_content(self, source_id: str, content: bytes) -> bool:
        self._fixtures[source_id] = content
        return True

    def to_source_entry(self, source_id: str) -> SourceEntry:
        meta = self.fetch_metadata(source_id)
        return SourceEntry(
            source_id=source_id,
            source_type=self.connector_type,
            display_name=meta.display_name,
        )


def test_mock_cloud_connector_implements_protocol() -> None:
    conn: ConnectorAdapter = MockCloudConnector(
        fixtures={"doc1.csv": b"a,b\n1,2\n"}
    )
    assert conn.connector_type == "mock_cloud"
    sources = conn.list_sources()
    assert len(sources) == 1
    assert sources[0].source_id == "doc1.csv"
    assert conn.fetch_content("doc1.csv") == b"a,b\n1,2\n"


def test_mock_cloud_connector_error_normalization() -> None:
    conn: ConnectorAdapter = MockCloudConnector()
    with pytest.raises(ConnectorError) as exc_info:
        conn.fetch_content("missing")
    assert exc_info.value.connector_type == "mock_cloud"
    assert exc_info.value.action == "fetch_content"
