"""Deterministic synthetic data generator for the Northstar Mobility pilot example.

Produces all sample datasets under ``data/samples/`` using a fixed random seed and
no timestamps, so two consecutive runs always produce byte-identical files.

Everything generated here is fictional: Northstar Mobility Group, all companies,
systems, and identifiers are invented for a synthetic SAP S/4HANA migration pilot.

Usage:
    python data/generate_synthetic_data.py

Requires only the standard library plus openpyxl.
"""

from __future__ import annotations

import csv
import io
import random
import re
import zipfile
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook

SEED = 20260112
SAMPLES_DIR = Path(__file__).resolve().parent / "samples"

# Fixed document metadata so the XLSX output is byte-identical across runs.
FIXED_DOC_DATE = datetime(2026, 1, 1, 0, 0, 0)

CUSTOMER_PREFIXES = [
    "Aldervale",
    "Brightpine",
    "Cedarfield",
    "Dunmore",
    "Elmridge",
    "Foxglove",
    "Gulliver",
    "Halloway",
    "Ironcrest",
    "Juniper",
    "Kestrel",
    "Larkspur",
    "Mistral",
    "Norberry",
    "Oakhurst",
    "Pinemart",
    "Quillan",
    "Ridgeline",
    "Stonebrook",
    "Tidewater",
    "Umberland",
    "Valecrest",
]
CUSTOMER_SUFFIXES = [
    "Construction",
    "Retail Group",
    "Foods",
    "Logistics",
    "Pharma",
    "Events",
    "Travel",
    "Grocery",
    "Manufacturing",
    "Horticulture",
    "Media",
    "Energy",
    "Telecom",
    "Furniture",
    "Stores",
    "Publishing",
    "Sports",
    "Hotels",
    "Marine",
    "Textiles",
]
VENDOR_PREFIXES = [
    "Axlebrook",
    "Brakesworth",
    "Chargefield",
    "Drivewell",
    "Equiparts",
    "Fleetwise",
    "Gearshift",
    "Hubcap",
    "Ignition",
    "Junction",
    "Kickdown",
    "Lugnut",
    "Milemarker",
    "Navpoint",
    "Overdrive",
]
VENDOR_SUFFIXES = [
    "Supply",
    "Components",
    "Leasing Services",
    "Fleet Care",
    "Parts Co",
    "Mobility Parts",
    "Auto Traders",
    "Service Works",
    "Fleet Systems",
    "Trading",
]
LEGACY_PAYMENT_TERMS = ["P15", "P30", "P45", "P60"]
LEGACY_CUSTOMER_GROUPS = ["GOLD", "SILVER", "STANDARD", "FLEET"]
LEGACY_MATERIAL_TYPES = ["VH", "SV", "PT", "PK"]
S4_MATERIAL_TYPE_MAP = {"VH": "VEH", "SV": "SERV", "PT": "PART", "PK": "PKG"}
CREDIT_BANDS = [10000, 25000, 50000, 75000, 100000, 150000]

# Rows (0-based) in the materials file whose pre-converted S/4 code is invalid.
INVALID_S4_TYPE_ROWS = {5: "FQ", 17: "ZZ", 29: "QQ"}
# Customer business keys that appear twice in the CRM extract (duplicate key defect).
# Row 9 repeats the key of row 6 (C-10007), row 24 repeats row 14 (C-10015).
DUPLICATE_CUSTOMER_ROWS = {9: 6, 24: 14}


def _unique_names(
    rng: random.Random, count: int, prefixes: list[str], suffixes: list[str]
) -> list[str]:
    """Build a deterministic list of unique fictional company names."""
    names: list[str] = []
    seen: set[str] = set()
    while len(names) < count:
        name = f"{rng.choice(prefixes)} {rng.choice(suffixes)}"
        if name in seen:
            continue
        seen.add(name)
        names.append(name)
    return names


def _write_csv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def _write_xlsx_deterministic(
    path: Path, sheet_title: str, header: list[str], rows: list[list[str]]
) -> None:
    """Write an XLSX with fixed document metadata and fixed zip entry timestamps."""
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = sheet_title
    sheet.append(header)
    for row in rows:
        sheet.append(row)
    props = workbook.properties
    props.creator = "Northstar Synthetic Generator"
    props.title = sheet_title
    props.created = FIXED_DOC_DATE
    props.modified = FIXED_DOC_DATE

    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)

    with zipfile.ZipFile(buffer, "r") as source, path.open("wb") as raw:
        with zipfile.ZipFile(raw, "w", zipfile.ZIP_DEFLATED) as target:
            for info in source.infolist():
                fixed = zipfile.ZipInfo(info.filename, date_time=(2026, 1, 1, 0, 0, 0))
                fixed.compress_type = zipfile.ZIP_DEFLATED
                fixed.external_attr = info.external_attr
                payload = source.read(info.filename)
                if info.filename == "docProps/core.xml":
                    # openpyxl overwrites dcterms:modified with the wall clock at
                    # save time; pin both timestamps to keep the file deterministic.
                    text = payload.decode("utf-8")
                    pattern = (
                        r"(<dcterms:(?:created|modified)[^>]*>)"
                        r"[^<]*"
                        r"(</dcterms:(?:created|modified)>)"
                    )
                    text = re.sub(pattern, r"\g<1>2026-01-01T00:00:00Z\g<2>", text)
                    payload = text.encode("utf-8")
                target.writestr(fixed, payload)


def build_customers(rng: random.Random) -> tuple[list[str], list[list[str]]]:
    """CRM customer extract; contains duplicated business keys on purpose."""
    header = ["customer_id", "customer_name", "customer_group", "credit_limit"]
    names = _unique_names(rng, 44, CUSTOMER_PREFIXES, CUSTOMER_SUFFIXES)
    rows: list[list[str]] = []
    for idx in range(44):
        source_idx = DUPLICATE_CUSTOMER_ROWS.get(idx, idx)
        customer_id = f"C-{10001 + source_idx}"
        name = names[source_idx]
        if idx in DUPLICATE_CUSTOMER_ROWS:
            name = name.upper()  # same key, different spelling -> duplicate defect
        rows.append(
            [
                customer_id,
                name,
                rng.choice(LEGACY_CUSTOMER_GROUPS),
                str(rng.choice(CREDIT_BANDS)),
            ]
        )
    return header, rows


def build_vendors(rng: random.Random) -> tuple[list[str], list[list[str]]]:
    header = ["vendor_id", "vendor_name", "payment_terms"]
    names = _unique_names(rng, 30, VENDOR_PREFIXES, VENDOR_SUFFIXES)
    rows = [[f"V-{2001 + idx}", names[idx], rng.choice(LEGACY_PAYMENT_TERMS)] for idx in range(30)]
    return header, rows


def build_materials(rng: random.Random) -> tuple[list[str], list[list[str]]]:
    """Material extract; the unmodeled s4_material_type column has invalid codes."""
    header = ["material_number", "material_type", "s4_material_type"]
    rows: list[list[str]] = []
    for idx in range(40):
        legacy_type = rng.choice(LEGACY_MATERIAL_TYPES)
        s4_type = INVALID_S4_TYPE_ROWS.get(idx, S4_MATERIAL_TYPE_MAP[legacy_type])
        rows.append([f"M-{300001 + idx}", legacy_type, s4_type])
    return header, rows


def build_purchase_orders(rng: random.Random) -> tuple[list[str], list[list[str]]]:
    header = ["po_id", "vendor_id", "po_payment_terms"]
    rows = [
        [str(4500001001 + idx), f"V-{2001 + idx % 30}", rng.choice(LEGACY_PAYMENT_TERMS)]
        for idx in range(36)
    ]
    return header, rows


def build_sales_orders(rng: random.Random) -> tuple[list[str], list[list[str]]]:
    """Sales order extract; ships order_total instead of the mapped net_value column."""
    header = ["order_id", "customer_id", "order_total"]
    rows = [
        [f"SO-{700001 + idx}", f"C-{10001 + idx % 44}", f"{rng.uniform(900, 42000):.2f}"]
        for idx in range(50)
    ]
    return header, rows


def build_deliveries(rng: random.Random) -> tuple[list[str], list[list[str]]]:
    header = ["delivery_id", "ship_qty"]
    rows = [[f"D-{800001 + idx}", str(rng.randint(1, 40))] for idx in range(30)]
    return header, rows


def build_open_items(rng: random.Random) -> tuple[list[str], list[list[str]]]:
    header = ["doc_id", "amount", "inv_payment_terms"]
    rows = [
        [str(1900000001 + idx), f"{rng.uniform(250, 18000):.2f}", rng.choice(LEGACY_PAYMENT_TERMS)]
        for idx in range(25)
    ]
    return header, rows


def main() -> None:
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)

    datasets = [
        ("northstar_crm_customers.csv", build_customers),
        ("voyager_vendors.csv", build_vendors),
        ("voyager_materials.csv", build_materials),
        ("voyager_purchase_orders.csv", build_purchase_orders),
        ("northstar_crm_sales_orders.csv", build_sales_orders),
        ("freightlink_deliveries.csv", build_deliveries),
    ]
    for filename, builder in datasets:
        header, rows = builder(rng)
        _write_csv(SAMPLES_DIR / filename, header, rows)
        print(f"wrote {filename}: {len(rows)} rows")

    header, rows = build_open_items(rng)
    _write_xlsx_deterministic(SAMPLES_DIR / "ledgerpro_open_items.xlsx", "open_items", header, rows)
    print(f"wrote ledgerpro_open_items.xlsx: {len(rows)} rows")


if __name__ == "__main__":
    main()
