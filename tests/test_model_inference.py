"""Tests for model inference from dataset profiles."""

from __future__ import annotations

from pathlib import Path

from modelops_core.imports.dataset_profiler import profile_csv, profile_xlsx
from modelops_core.imports.model_inference_service import infer_model_from_profile
from modelops_core.patching.patch_validator import validate_patch_proposal

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestInferModelFromProfile:
    def test_infer_from_csv_profile(self) -> None:
        csv_path = FIXTURES_DIR / "customer_sample.csv"
        profile = profile_csv(csv_path, dataset_id="customer_sample")
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

        proposal = infer_model_from_profile(profile_dict, dataset_id="customer_sample")

        assert proposal["type"] == "PatchProposal"
        assert proposal["status"] == "pending_review"
        assert proposal["id"] == "PP-INFER-CUSTOMER-SAMPLE"
        assert len(proposal["operations"]) > 0
        assert proposal["assumptions"]
        assert proposal["human_checks"]

        # Validate the proposal
        results = validate_patch_proposal(proposal)
        assert not any(r.severity == "ERROR" for r in results)

    def test_infer_from_xlsx_profile(self) -> None:
        xlsx_path = FIXTURES_DIR / "customer_sample_multi.xlsx"
        profile = profile_xlsx(xlsx_path, dataset_id="customer_sample_multi")
        profile_dict = {
            "dataset_id": profile.dataset_id,
            "file_path": profile.file_path,
            "file_hash": profile.file_hash,
            "sheet_names": profile.sheet_names,
            "sheets": [
                {
                    "dataset_id": s.dataset_id,
                    "file_path": s.file_path,
                    "file_hash": s.file_hash,
                    "sheet_name": s.sheet_name,
                    "row_count": s.row_count,
                    "column_count": s.column_count,
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
                        for c in s.columns
                    ],
                    "status": {
                        "success": s.status.success,
                        "truncated": s.status.truncated,
                        "reason": s.status.reason,
                        "rows_processed": s.status.rows_processed,
                        "file_size_bytes": s.status.file_size_bytes,
                    },
                }
                for s in profile.sheets
            ],
            "status": {
                "success": profile.status.success,
                "truncated": profile.status.truncated,
                "reason": profile.status.reason,
                "rows_processed": profile.status.rows_processed,
                "file_size_bytes": profile.status.file_size_bytes,
            },
        }

        proposal = infer_model_from_profile(profile_dict, dataset_id="customer_sample_multi")

        assert proposal["type"] == "PatchProposal"
        assert len(proposal["operations"]) > 0

        # Should have entities for both sheets
        entities = [
            op for op in proposal["operations"] if op.get("object_type") == "BusinessEntity"
        ]
        assert len(entities) == 2

        # Validate
        results = validate_patch_proposal(proposal)
        assert not any(r.severity == "ERROR" for r in results)

    def test_no_canonical_mutation(self, tmp_path: Path) -> None:
        """Inference must not mutate canonical model files."""
        csv_path = FIXTURES_DIR / "customer_sample.csv"
        profile = profile_csv(csv_path, dataset_id="customer_sample")
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

        # Run inference
        proposal = infer_model_from_profile(profile_dict, dataset_id="customer_sample")

        # The proposal itself should not touch the filesystem
        assert isinstance(proposal, dict)
        assert all(
            op.get("op") in {"create_object", "add_relationship"} for op in proposal["operations"]
        )
