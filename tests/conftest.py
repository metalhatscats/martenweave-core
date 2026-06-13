"""Shared test fixtures."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from modelops_core.index.sqlite_builder import build_index


@pytest.fixture
def sample_repo(tmp_path: Path) -> Path:
    """Copy the example customer-bp model into a temporary directory."""
    src = Path(__file__).resolve().parent.parent / "examples" / "customer_bp_model"
    dst = tmp_path / "customer_bp_model"
    shutil.copytree(src, dst)
    # Build the SQLite index so tests that require it don't fail in CI.
    build_index(dst, allow_invalid=True)
    return dst


@pytest.fixture
def supplier_repo(tmp_path: Path) -> Path:
    """Copy the example supplier-vendor model into a temporary directory."""
    src = Path(__file__).resolve().parent.parent / "examples" / "supplier_vendor_model"
    dst = tmp_path / "supplier_vendor_model"
    shutil.copytree(src, dst)
    build_index(dst, allow_invalid=True)
    return dst


@pytest.fixture
def temp_model_dir(tmp_path: Path) -> Path:
    """Create a temporary model directory with a few canonical objects."""
    model_dir = tmp_path / "model"
    model_dir.mkdir()

    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\nname: Test Domain\n---\n",
        encoding="utf-8",
    )

    (model_dir / "ATTR-TEST.md").write_text(
        "---\n"
        "id: ATTR-TEST\n"
        "type: Attribute\n"
        "status: draft\n"
        "name: Test Attribute\n"
        "domain: DOMAIN-TEST\n"
        "---\n",
        encoding="utf-8",
    )

    return model_dir


# ---------------------------------------------------------------------------
# Canonical object factories
# ---------------------------------------------------------------------------


@pytest.fixture
def domain_factory():
    """Return a factory that produces MasterDataDomain frontmatter dicts."""

    def _factory(**overrides):
        return {
            "id": "DOMAIN-FACTORY",
            "type": "MasterDataDomain",
            "status": "draft",
            "name": "Factory Domain",
            "created_at": "2024-01-01T00:00:00+00:00",
            **overrides,
        }

    return _factory


@pytest.fixture
def attribute_factory():
    """Return a factory that produces Attribute frontmatter dicts."""

    def _factory(**overrides):
        return {
            "id": "ATTR-FACTORY",
            "type": "Attribute",
            "status": "draft",
            "name": "Factory Attribute",
            "domain": "DOMAIN-FACTORY",
            "created_at": "2024-01-01T00:00:00+00:00",
            **overrides,
        }

    return _factory


@pytest.fixture
def entity_context_factory():
    """Return a factory that produces EntityContext frontmatter dicts."""

    def _factory(**overrides):
        return {
            "id": "ENTITY-CONTEXT-FACTORY",
            "type": "EntityContext",
            "status": "draft",
            "name": "Factory Entity Context",
            "domain": "DOMAIN-FACTORY",
            "context_category": "customer_sales_area",
            "created_at": "2024-01-01T00:00:00+00:00",
            **overrides,
        }

    return _factory


@pytest.fixture
def field_endpoint_factory():
    """Return a factory that produces FieldEndpoint frontmatter dicts."""

    def _factory(**overrides):
        return {
            "id": "FEP-FACTORY",
            "type": "FieldEndpoint",
            "status": "draft",
            "name": "Factory Field Endpoint",
            "domain": "DOMAIN-FACTORY",
            "attribute": "ATTR-FACTORY",
            "created_at": "2024-01-01T00:00:00+00:00",
            **overrides,
        }

    return _factory


@pytest.fixture
def mapping_factory():
    """Return a factory that produces Mapping frontmatter dicts."""

    def _factory(**overrides):
        return {
            "id": "MAP-FACTORY",
            "type": "Mapping",
            "status": "draft",
            "name": "Factory Mapping",
            "domain": "DOMAIN-FACTORY",
            "source_endpoint": "FEP-SOURCE-FACTORY",
            "target_endpoint": "FEP-TARGET-FACTORY",
            "created_at": "2024-01-01T00:00:00+00:00",
            **overrides,
        }

    return _factory


@pytest.fixture
def patch_proposal_factory():
    """Return a factory that produces PatchProposal frontmatter dicts."""

    def _factory(**overrides):
        return {
            "id": "PP-FACTORY",
            "type": "PatchProposal",
            "status": "pending_review",
            "name": "Factory Patch Proposal",
            "affected_objects": [],
            "created_at": "2024-01-01T00:00:00+00:00",
            "operations": [
                {
                    "op": "update_object",
                    "object_id": "ATTR-FACTORY",
                    "target_path": "name",
                    "after": "Updated Name",
                }
            ],
            **overrides,
        }

    return _factory
