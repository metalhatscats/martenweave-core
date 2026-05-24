"""Tests for dataset profiler."""

from __future__ import annotations

import json
from pathlib import Path

from modelops_core.imports.dataset_profiler import (
    WorkbookProfile,
    dataset_profile_to_dict,
    profile_csv,
    profile_xlsx,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestProfileCsv:
    def test_profile_csv_success(self) -> None:
        csv_path = FIXTURES_DIR / "customer_sample.csv"
        profile = profile_csv(csv_path, dataset_id="customer_sample")

        assert profile.status.success is True
        assert profile.row_count == 5
        assert profile.column_count == 3
        assert profile.dataset_id == "customer_sample"
        assert len(profile.columns) == 3

    def test_profile_csv_column_details(self) -> None:
        csv_path = FIXTURES_DIR / "customer_sample.csv"
        profile = profile_csv(csv_path, dataset_id="customer_sample")

        col_names = [c.name for c in profile.columns]
        assert col_names == ["customer_id", "customer_group", "sales_org"]

        customer_group_col = profile.columns[1]
        assert customer_group_col.blank_count == 1
        assert customer_group_col.non_blank_count == 4
        assert customer_group_col.distinct_count == 3

    def test_profile_csv_empty_file(self, tmp_path: Path) -> None:
        empty_csv = tmp_path / "empty.csv"
        empty_csv.write_text("", encoding="utf-8")
        profile = profile_csv(empty_csv, dataset_id="empty")

        assert profile.status.success is False
        assert "Empty CSV" in (profile.status.reason or "")

    def test_profile_csv_deterministic(self) -> None:
        csv_path = FIXTURES_DIR / "customer_sample.csv"
        profile1 = profile_csv(csv_path, dataset_id="customer_sample")
        profile2 = profile_csv(csv_path, dataset_id="customer_sample")

        assert dataset_profile_to_dict(profile1) == dataset_profile_to_dict(profile2)


class TestProfileXlsx:
    def test_profile_xlsx_single_sheet(self) -> None:
        xlsx_path = FIXTURES_DIR / "customer_sample.xlsx"
        profile = profile_xlsx(xlsx_path, dataset_id="customer_sample")

        assert isinstance(profile, WorkbookProfile)
        assert profile.status.success is True
        assert len(profile.sheets) == 1
        assert profile.sheet_names == ["customers"]

        sheet = profile.sheets[0]
        assert sheet.sheet_name == "customers"
        assert sheet.row_count == 5
        assert sheet.column_count == 3

    def test_profile_xlsx_multi_sheet(self) -> None:
        xlsx_path = FIXTURES_DIR / "customer_sample_multi.xlsx"
        profile = profile_xlsx(xlsx_path, dataset_id="customer_sample_multi")

        assert isinstance(profile, WorkbookProfile)
        assert profile.status.success is True
        assert len(profile.sheets) == 2
        assert profile.sheet_names == ["customers", "orders"]

        customers_sheet = profile.sheets[0]
        assert customers_sheet.row_count == 2
        assert customers_sheet.column_count == 3

        orders_sheet = profile.sheets[1]
        assert orders_sheet.row_count == 2
        assert orders_sheet.column_count == 3

    def test_profile_xlsx_column_details(self) -> None:
        xlsx_path = FIXTURES_DIR / "customer_sample.xlsx"
        profile = profile_xlsx(xlsx_path, dataset_id="customer_sample")

        sheet = profile.sheets[0]
        col_names = [c.name for c in sheet.columns]
        assert col_names == ["customer_id", "customer_group", "sales_org"]

        customer_group_col = sheet.columns[1]
        assert customer_group_col.blank_count == 1
        assert customer_group_col.non_blank_count == 4

    def test_profile_xlsx_deterministic(self) -> None:
        xlsx_path = FIXTURES_DIR / "customer_sample.xlsx"
        profile1 = profile_xlsx(xlsx_path, dataset_id="customer_sample")
        profile2 = profile_xlsx(xlsx_path, dataset_id="customer_sample")

        assert dataset_profile_to_dict(profile1) == dataset_profile_to_dict(profile2)


class TestDatasetProfileToDict:
    def test_csv_profile_round_trip(self) -> None:
        csv_path = FIXTURES_DIR / "customer_sample.csv"
        profile = profile_csv(csv_path, dataset_id="customer_sample")
        d = dataset_profile_to_dict(profile)

        assert d["dataset_id"] == "customer_sample"
        assert d["row_count"] == 5
        assert "status" in d

        # Verify JSON serializable
        json_str = json.dumps(d, indent=2, default=str, sort_keys=True)
        assert json_str

    def test_xlsx_profile_round_trip(self) -> None:
        xlsx_path = FIXTURES_DIR / "customer_sample_multi.xlsx"
        profile = profile_xlsx(xlsx_path, dataset_id="customer_sample_multi")
        d = dataset_profile_to_dict(profile)

        assert d["dataset_id"] == "customer_sample_multi"
        assert len(d["sheets"]) == 2
        assert "sheet_names" in d

        json_str = json.dumps(d, indent=2, default=str, sort_keys=True)
        assert json_str
