"""Workbook-first, proposal-only bootstrap for new pilot repositories."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

from modelops_core.config import RepoConfig
from modelops_core.imports.dataset_profiler import profile_csv, profile_xlsx
from modelops_core.imports.model_inference_service import infer_model_from_profile
from modelops_core.patching.patch_proposal_service import write_patch_proposal


class BootstrapAssessmentError(ValueError):
    """Raised for actionable, safe bootstrap failures."""


@dataclass(frozen=True)
class BootstrapAssessmentResult:
    repo_root: Path
    proposal_path: Path
    report_json_path: Path
    report_markdown_path: Path
    proposal_id: str


def _profile_to_dict(profile: Any) -> dict[str, Any]:
    """Serialize profiler dataclasses without retaining raw workbook values beyond samples."""
    return asdict(profile)


def _bootstrap_id(mapping: Path) -> str:
    digest = hashlib.sha256(mapping.read_bytes()).hexdigest()[:16].upper()
    return f"PP-BOOTSTRAP-{digest}"


def _initialize_repo(repo_root: Path, name: str) -> None:
    repo_root.mkdir(parents=True, exist_ok=True)
    if any(repo_root.iterdir()):
        raise BootstrapAssessmentError(
            f"Output repository must be empty to avoid overwriting existing work: {repo_root}"
        )
    (repo_root / "model" / "patch-proposals").mkdir(parents=True)
    (repo_root / "generated").mkdir()
    (repo_root / "data" / "samples").mkdir(parents=True)
    config = RepoConfig(name=name)
    (repo_root / "modelops.config.yaml").write_text(
        yaml.safe_dump(config.model_dump(), default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )


def bootstrap_assessment(
    mapping_path: Path,
    repo_name: str,
    out_repo: Path,
    dataset_path: Path | None = None,
) -> BootstrapAssessmentResult:
    """Initialize a pilot repository and create only a draft proposal from workbook evidence."""
    mapping_path = mapping_path.resolve()
    out_repo = out_repo.resolve()
    if not mapping_path.is_file() or mapping_path.suffix.lower() != ".xlsx":
        raise BootstrapAssessmentError("Mapping workbook must be an existing .xlsx file.")
    if dataset_path is not None:
        if not dataset_path.is_file():
            raise BootstrapAssessmentError(f"Dataset not found: {dataset_path}")
        if dataset_path.suffix.lower() not in {".csv", ".xlsx"}:
            raise BootstrapAssessmentError("Dataset must be an existing CSV or XLSX file.")

    _initialize_repo(out_repo, repo_name)
    report_dir = out_repo / "generated" / "bootstrap-assessment"
    report_dir.mkdir()
    try:
        dataset_id = mapping_path.stem
        mapping_profile = profile_xlsx(mapping_path, dataset_id=dataset_id)
        if not mapping_profile.status.success or not mapping_profile.sheets:
            reason = mapping_profile.status.reason or "no readable sheets"
            raise BootstrapAssessmentError(f"Unsupported workbook layout: {reason}")
        proposal = infer_model_from_profile(
            _profile_to_dict(mapping_profile), dataset_id=dataset_id
        )
        if not proposal["operations"]:
            raise BootstrapAssessmentError(
                "Workbook has no inferable columns; no proposal was created."
            )
        inferred_object_ids = list(proposal["affected_objects"])
        proposal["id"] = _bootstrap_id(mapping_path)
        proposal["name"] = proposal["id"]
        proposal["title"] = f"Bootstrap proposal from {mapping_path.name}"
        proposal["schema_version"] = "1.0"
        proposal.pop("created_at", None)
        # A fresh repository has no canonical objects yet.  Keeping inferred IDs in
        # affected_objects would turn this proposal-only bootstrap into a set of
        # broken canonical references.  The operations remain the authoritative
        # proposed changes and the report retains the inferred IDs for review.
        proposal.pop("affected_objects", None)
        proposal["human_checks"] = sorted(proposal["human_checks"])
        proposal["source_evidence"] = (
            f"Workbook bootstrap: {mapping_path.name}; SHA-256 {mapping_profile.file_hash}"
        )
        proposal_path = write_patch_proposal(proposal, out_repo / "model")

        dataset_profile: dict[str, Any] | None = None
        if dataset_path is not None:
            profiler = profile_xlsx if dataset_path.suffix.lower() == ".xlsx" else profile_csv
            dataset_profile = _profile_to_dict(profiler(dataset_path, dataset_path.stem))
        report = {
            "repository": str(out_repo),
            "mapping_workbook": mapping_path.name,
            "mapping_sha256": mapping_profile.file_hash,
            "proposal_id": proposal["id"],
            "proposal_path": str(proposal_path),
            "inferred_object_ids": inferred_object_ids,
            "unresolved_columns": [
                sheet["sheet_name"]
                for sheet in _profile_to_dict(mapping_profile)["sheets"]
                if not sheet["status"]["success"]
            ],
            "assumptions": proposal["assumptions"],
            "warnings": [
                sheet["status"]["reason"]
                for sheet in _profile_to_dict(mapping_profile)["sheets"]
                if sheet["status"]["reason"]
            ],
            "dataset_profile": dataset_profile,
            "next_commands": [
                f"martenweave validate --repo {out_repo}",
                f"martenweave proposal validate --repo {out_repo} {proposal['id']}",
                f"martenweave proposal review --repo {out_repo} {proposal['id']}",
            ],
        }
    except BootstrapAssessmentError as exc:
        failure = report_dir / "bootstrap-diagnostics.md"
        failure.write_text(f"# Bootstrap diagnostics\n\n{exc}\n", encoding="utf-8")
        raise
    except Exception as exc:
        failure = report_dir / "bootstrap-diagnostics.md"
        failure.write_text(f"# Bootstrap diagnostics\n\n{exc}\n", encoding="utf-8")
        raise BootstrapAssessmentError(f"Workbook bootstrap failed safely: {exc}") from exc

    json_path = report_dir / "bootstrap-report.json"
    markdown_path = report_dir / "bootstrap-report.md"
    json_path.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    markdown_path.write_text(
        "# Workbook bootstrap\n\n"
        f"Draft proposal: `{proposal['id']}`\n\n"
        "No inferred canonical object has been applied. Review the proposal before any change.\n\n"
        "## Next commands\n\n"
        + "\n".join(f"- `{command}`" for command in report["next_commands"])
        + "\n",
        encoding="utf-8",
    )
    return BootstrapAssessmentResult(
        repo_root=out_repo,
        proposal_path=proposal_path,
        report_json_path=json_path,
        report_markdown_path=markdown_path,
        proposal_id=proposal["id"],
    )
