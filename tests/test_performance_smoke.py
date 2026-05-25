"""Performance smoke tests for moderately large generated fixtures (#45)."""

from __future__ import annotations

from pathlib import Path

from modelops_core.fixtures.fixture_generator import generate_fixture_repo
from modelops_core.index.sqlite_builder import build_index
from modelops_core.repository import parse_file, scan_repository
from modelops_core.validation.pipeline import validate_objects


class TestLargeFixtureSmoke:
    def test_large_fixture_validates_without_crash(self, tmp_path: Path) -> None:
        generate_fixture_repo(tmp_path, profile="large")
        files = scan_repository(tmp_path)
        objects = [parse_file(f) for f in files]
        summary = validate_objects(objects)
        # Smoke test: verify validation completes without crashing on ~150 objects
        assert summary is not None
        assert len(objects) > 50

    def test_large_fixture_builds_index_without_crash(self, tmp_path: Path) -> None:
        generate_fixture_repo(tmp_path, profile="large")
        summary = build_index(tmp_path, max_objects=10_000, allow_invalid=True)
        # Smoke test: verify index build completes without crashing
        assert summary is not None
        db_path = tmp_path / "generated" / "modelops.db"
        assert db_path.exists()

    def test_medium_fixture_validates_without_crash(self, tmp_path: Path) -> None:
        generate_fixture_repo(tmp_path, profile="medium")
        files = scan_repository(tmp_path)
        objects = [parse_file(f) for f in files]
        summary = validate_objects(objects)
        # Smoke test: verify validation completes without crashing
        assert summary is not None
