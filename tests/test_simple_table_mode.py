"""Tests for simple table modeling mode."""

from __future__ import annotations

from pathlib import Path

from modelops_core.imports.dataset_profiler import profile_csv
from modelops_core.imports.model_inference_service import infer_model_from_profile
from modelops_core.patching.patch_validator import validate_patch_proposal
from modelops_core.repository.parser import parse_file
from modelops_core.repository.scanner import scan_repository
from modelops_core.validation import validate_objects

SIMPLE_REPO = Path(__file__).parent.parent / "examples" / "simple_product_model"
FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_simple_product_model_validates() -> None:
    model_path = SIMPLE_REPO / "model"
    files = scan_repository(model_path)
    parsed = [parse_file(f) for f in files]
    summary = validate_objects(parsed)
    assert summary.is_valid, summary.results


def test_simple_product_model_has_domain_entity_attributes() -> None:
    model_path = SIMPLE_REPO / "model"
    files = scan_repository(model_path)
    parsed = [parse_file(f) for f in files]

    types = {p.frontmatter.get("type") for p in parsed}
    assert "MasterDataDomain" in types
    assert "BusinessEntity" in types
    assert "Attribute" in types
    assert "FieldEndpoint" in types
    assert "Dataset" in types
    assert "ValueList" in types

    # BusinessEntity links to Domain
    entity = next(p for p in parsed if p.frontmatter.get("id") == "ENTITY-PRODUCT")
    assert entity.frontmatter.get("domain") == "DOMAIN-PRODUCT"

    # FieldEndpoints link to Attributes and Dataset
    fep = next(p for p in parsed if p.frontmatter.get("id") == "FEP-PRODUCT-NAME")
    assert fep.frontmatter.get("attribute") == "ATTR-PRODUCT-NAME"
    assert fep.frontmatter.get("dataset") == "DS-PRODUCT-CSV"


def test_infer_model_from_csv_creates_simple_model() -> None:
    csv_path = FIXTURES_DIR / "product_sample.csv"
    profile = profile_csv(csv_path, dataset_id="product_sample")
    profile_dict = {
        "dataset_id": profile.dataset_id,
        "file_path": profile.file_path,
        "file_hash": profile.file_hash,
        "row_count": profile.row_count,
        "column_count": profile.column_count,
        "columns": [
            {
                "name": c.name,
                "position": c.position,
                "blank_count": c.blank_count,
                "non_blank_count": c.non_blank_count,
                "distinct_count": c.distinct_count,
                "sample_values": c.sample_values,
                "inferred_type": c.inferred_type,
            }
            for c in profile.columns
        ],
        "status": {
            "success": profile.status.success,
            "truncated": profile.status.truncated,
            "reason": profile.status.reason,
            "rows_processed": profile.status.rows_processed,
            "file_size_bytes": profile.status.file_size_bytes,
        },
    }

    proposal = infer_model_from_profile(profile_dict, dataset_id="product_sample")

    assert proposal["type"] == "PatchProposal"
    assert proposal["id"] == "PP-INFER-PRODUCT-SAMPLE"

    ops = proposal["operations"]
    obj_types = [op["object_type"] for op in ops]

    # Simple mode must include Domain, Dataset, BusinessEntity, Attribute, FieldEndpoint
    assert "MasterDataDomain" in obj_types
    assert "Dataset" in obj_types
    assert "BusinessEntity" in obj_types
    assert "Attribute" in obj_types
    assert "FieldEndpoint" in obj_types

    # All objects should reference the same domain
    domain_ops = [op for op in ops if op["object_type"] == "MasterDataDomain"]
    assert len(domain_ops) == 1
    domain_id = domain_ops[0]["object_id"]

    for op in ops:
        after = op.get("after", {})
        if "domain" in after:
            assert after["domain"] == domain_id

    # Validate proposal
    results = validate_patch_proposal(proposal)
    assert not any(r.severity == "ERROR" for r in results)
