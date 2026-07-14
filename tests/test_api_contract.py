"""Contract tests for the versioned v1 API surface."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from modelops_core.api.app import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Capabilities
# ---------------------------------------------------------------------------


def test_api_v1_capabilities_shape(sample_repo: Path) -> None:
    response = client.get("/api/v1/capabilities", params={"repo": str(sample_repo)})
    assert response.status_code == 200
    data = response.json()

    assert data["api_version"] == "v1"
    assert data["version"]  # package version is present
    assert data["repository"] == str(sample_repo)
    assert isinstance(data["indexed"], bool)
    assert isinstance(data["canonical_files"], int)
    assert data["canonical_files"] > 0
    assert data["read_only"] is False

    read_names = {c["name"] for c in data["read"]}
    assert "capabilities" in read_names
    assert "search" in read_names
    assert "object_detail" in read_names

    mutation_names = {c["name"] for c in data["mutations"]}
    assert "apply_proposal" in mutation_names
    assert "export" in mutation_names
    assert "dataset_readiness" in mutation_names

    # Every capability entry exposes the fields the frontend consumes.
    for entry in data["read"] + data["mutations"]:
        assert "name" in entry
        assert "method" in entry
        assert "href" in entry
        assert "description" in entry


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


def test_api_v1_search_paginated_shape(sample_repo: Path) -> None:
    response = client.get(
        "/api/v1/search", params={"repo": str(sample_repo), "q": "customer group"}
    )
    assert response.status_code == 200
    data = response.json()

    assert "total_count" in data
    assert "results" in data
    assert isinstance(data["results"], list)
    assert len(data["results"]) > 0

    first = data["results"][0]
    assert "object_id" in first
    assert "object_type" in first
    assert "status" in first
    assert "name" in first
    assert "source_file" in first
    assert "score" in first
    assert "matched_fields" in first


def test_api_v1_search_filters_by_type(sample_repo: Path) -> None:
    response = client.get(
        "/api/v1/search",
        params={"repo": str(sample_repo), "q": "customer", "type": "Attribute"},
    )
    assert response.status_code == 200
    data = response.json()

    assert all(r["object_type"] == "Attribute" for r in data["results"])


def test_api_v1_search_missing_query(sample_repo: Path) -> None:
    response = client.get("/api/v1/search", params={"repo": str(sample_repo)})
    assert response.status_code == 422


def test_api_v1_search_missing_index(temp_model_dir: Path) -> None:
    repo = str(temp_model_dir.parent)
    response = client.get("/api/v1/search", params={"repo": repo, "q": "test"})
    assert response.status_code == 400
    assert "Index not found" in response.json()["detail"]


# ---------------------------------------------------------------------------
# Object detail
# ---------------------------------------------------------------------------


def test_api_v1_object_detail_shape(sample_repo: Path) -> None:
    response = client.get(
        "/api/v1/objects/DOMAIN-CUSTOMER-BP", params={"repo": str(sample_repo)}
    )
    assert response.status_code == 200
    data = response.json()

    assert "object" in data
    assert data["object"]["id"] == "DOMAIN-CUSTOMER-BP"
    assert data["object"]["type"] == "MasterDataDomain"
    assert "relationships" in data
    assert isinstance(data["relationships"], list)


def test_api_v1_object_detail_not_found(sample_repo: Path) -> None:
    response = client.get(
        "/api/v1/objects/DOES-NOT-EXIST", params={"repo": str(sample_repo)}
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_api_v1_object_detail_missing_index(temp_model_dir: Path) -> None:
    repo = str(temp_model_dir.parent)
    response = client.get("/api/v1/objects/DOMAIN-TEST", params={"repo": repo})
    assert response.status_code == 400
    assert "Index not found" in response.json()["detail"]


# ---------------------------------------------------------------------------
# Contract stability: existing endpoints remain reachable
# ---------------------------------------------------------------------------


def test_api_v1_does_not_break_existing_endpoints(sample_repo: Path) -> None:
    # The v1 router is additive; legacy endpoints must still work.
    response = client.get("/health", params={"repo": str(sample_repo)})
    assert response.status_code == 200

    response = client.get("/objects/DOMAIN-CUSTOMER-BP", params={"repo": str(sample_repo)})
    assert response.status_code == 200
