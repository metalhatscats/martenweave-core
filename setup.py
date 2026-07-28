"""Setuptools hook for synthetic CLI assets included in every wheel."""

from __future__ import annotations

import shutil
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py

# setuptools requires data-file source paths to be relative to setup.py.
ROOT = Path(".")
ASSET_ROOTS = (
    ROOT / "templates" / "model_spines",
    ROOT / "examples" / "customer_bp_model",
    ROOT / "examples" / "sap_bp_customer_vendor_reference",
    ROOT / "tests" / "fixtures" / "pilot",
)
EXCLUDED_PARTS = frozenset({"generated", "__pycache__"})


class BuildPyWithBundledAssets(build_py):
    """Copy public synthetic assets into the package before wheel assembly."""

    def run(self) -> None:
        super().run()
        destination_root = Path(self.build_lib) / "modelops_core" / "assets"
        for root in ASSET_ROOTS:
            for path in sorted(root.rglob("*")):
                if not path.is_file() or EXCLUDED_PARTS.intersection(path.parts):
                    continue
                destination = destination_root / path.relative_to(ROOT)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, destination)


setup(
    cmdclass={"build_py": BuildPyWithBundledAssets},
    package_data={"modelops_core": ["assets/**/*"]},
)
