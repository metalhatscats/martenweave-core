"""Safe diagnostics bundle export for model repositories."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from modelops_core.config import load_repo_config, resolve_generated_path, resolve_model_path
from modelops_core.reports.health_report import generate_repository_health
from modelops_core.reports.index_freshness import check_index_freshness
from modelops_core.reports.scorecard_service import (
    _count_open_issues,
    _count_pending_changes,
    generate_scorecard,
)
from modelops_core.repository import parse_file, scan_repository
from modelops_core.validation.pipeline import validate_objects

# Files/patterns that must never be copied into a diagnostics bundle.
_SENSITIVE_PATTERNS = (".env", ".env.")


def _is_sensitive_path(path: Path) -> bool:
    name = path.name
    return any(name.startswith(p) for p in _SENSITIVE_PATTERNS)


def _to_iso(mtime: float | None) -> str | None:
    if mtime is None:
        return None
    return datetime.fromtimestamp(mtime, tz=UTC).isoformat()


@dataclass
class DiagnosticsBundle:
    """In-memory representation of a safe diagnostics bundle."""

    manifest: dict[str, Any]
    validation: dict[str, Any]
    health: dict[str, Any]
    scorecard: dict[str, Any]
    config: dict[str, Any]
    source_registry: dict[str, Any]
    generated_manifest: dict[str, Any]
    pending_changes: dict[str, Any]
    dataset_samples: dict[str, Any]
    command_outputs: dict[str, Any] = field(default_factory=dict)


def _load_validation_summary(
    model_path: Path, enabled_packs: list[str] | None
) -> dict[str, Any]:
    if not model_path.exists():
        return {"ran": False, "reason": "model path not found"}

    files = scan_repository(model_path)
    parsed = [parse_file(f) for f in files]
    summary = validate_objects(parsed, enabled_domain_packs=enabled_packs)
    return {
        "ran": True,
        "is_valid": summary.is_valid,
        "error_count": summary.error_count,
        "warning_count": summary.warning_count,
        "info_count": summary.info_count,
        "summary_by_code": summary.summary_by_code,
    }


def _load_source_registry(model_path: Path, repo_root: Path) -> dict[str, Any]:
    if not model_path.exists():
        return {"file_count": 0, "total_size_bytes": 0, "files": []}

    entries: list[dict[str, Any]] = []
    total_size = 0
    for file_path in sorted(scan_repository(model_path)):
        path_obj = Path(file_path)
        if _is_sensitive_path(path_obj):
            continue
        parsed = parse_file(file_path)
        fm = parsed.frontmatter or {}
        try:
            size = path_obj.stat().st_size
        except OSError:
            size = 0
        total_size += size
        entries.append(
            {
                "relative_path": str(path_obj.relative_to(repo_root)).replace("\\", "/"),
                "content_hash": parsed.content_hash,
                "object_id": fm.get("id"),
                "object_type": fm.get("type"),
                "status": fm.get("status"),
                "parser_error": parsed.parser_error,
                "size_bytes": size,
            }
        )

    return {
        "file_count": len(entries),
        "total_size_bytes": total_size,
        "files": entries,
    }


def _load_generated_manifest(generated_path: Path, repo_root: Path) -> dict[str, Any]:
    if not generated_path.exists():
        return {"file_count": 0, "total_size_bytes": 0, "files": []}

    entries: list[dict[str, Any]] = []
    total_size = 0
    for file_path in sorted(generated_path.rglob("*")):
        if not file_path.is_file():
            continue
        if _is_sensitive_path(file_path):
            continue
        try:
            stat = file_path.stat()
        except OSError:
            continue
        total_size += stat.st_size
        entries.append(
            {
                "relative_path": str(file_path.relative_to(repo_root)).replace("\\", "/"),
                "size_bytes": stat.st_size,
                "mtime": _to_iso(stat.st_mtime),
            }
        )

    return {
        "file_count": len(entries),
        "total_size_bytes": total_size,
        "files": entries,
    }


def _load_dataset_samples(data_path: Path, repo_root: Path) -> dict[str, Any]:
    if not data_path.exists():
        return {"file_count": 0, "total_size_bytes": 0, "files": []}

    entries: list[dict[str, Any]] = []
    total_size = 0
    for file_path in sorted(data_path.rglob("*")):
        if not file_path.is_file():
            continue
        if _is_sensitive_path(file_path):
            continue
        try:
            stat = file_path.stat()
        except OSError:
            continue
        total_size += stat.st_size
        entries.append(
            {
                "relative_path": str(file_path.relative_to(repo_root)).replace("\\", "/"),
                "size_bytes": stat.st_size,
                "mtime": _to_iso(stat.st_mtime),
            }
        )

    return {
        "file_count": len(entries),
        "total_size_bytes": total_size,
        "files": entries,
    }


def _load_pending_changes(model_path: Path) -> dict[str, Any]:
    pending_proposals, pending_crs, high_risk = (
        _count_pending_changes(model_path) if model_path.exists() else (0, 0, 0)
    )
    return {
        "open_issues": _count_open_issues(model_path) if model_path.exists() else 0,
        "pending_proposals": pending_proposals,
        "pending_change_requests": pending_crs,
        "high_risk_changes": high_risk,
    }


def _health_to_dict(report: Any) -> dict[str, Any]:
    return {
        "object_count": report.object_count,
        "index_fresh": report.index_fresh,
        "type_counts": report.type_counts,
        "coverage_gaps": (
            {
                "objects_without_name": report.coverage_gaps.objects_without_name,
                "objects_without_description": report.coverage_gaps.objects_without_description,
            }
            if report.coverage_gaps
            else {}
        ),
        "ownership_coverage": (
            report.ownership_coverage.__dict__ if report.ownership_coverage else {}
        ),
        "data_quality_coverage": (
            report.data_quality_coverage.__dict__ if report.data_quality_coverage else {}
        ),
        "coverage_gaps_list": [
            {
                "object_id": g.object_id,
                "object_type": g.object_type,
                "object_name": g.object_name,
                "gap_type": g.gap_type,
                "suggested_action": g.suggested_action,
            }
            for g in report.coverage_gaps_list
        ],
    }


def _scorecard_to_dict(report: Any) -> dict[str, Any]:
    return {
        "repo_name": report.repo_name,
        "generated_at": report.generated_at,
        "readiness_level": report.readiness_level,
        "object_count": report.object_count,
        "metrics": [m.__dict__ for m in report.metrics],
        "gaps": [g.__dict__ for g in report.gaps],
        "summary": report.summary,
    }


def _build_command_outputs(
    repo_root: Path,
    model_path: Path,
    generated_path: Path,
    db_path: Path,
    validation: dict[str, Any],
    health: dict[str, Any],
    scorecard: dict[str, Any],
) -> dict[str, Any]:
    """Return JSON-serializable snapshots of key commands."""
    freshness = check_index_freshness(repo_root, model_path, generated_path)
    return {
        "validate.json": validation,
        "health.json": health,
        "scorecard.json": scorecard,
        "index-freshness.json": {
            "fresh": freshness.fresh,
            "reason": freshness.reason,
            "db_mtime": _to_iso(freshness.db_mtime.timestamp() if freshness.db_mtime else None),
            "newest_source_mtime": _to_iso(
                freshness.newest_source_mtime.timestamp()
                if freshness.newest_source_mtime
                else None
            ),
            "stale_sources": freshness.stale_sources,
            "hash_mismatch": freshness.hash_mismatch,
        },
    }


def generate_diagnostics_bundle(
    repo_root: Path,
    out_dir: Path,
    include_command_outputs: bool = False,
) -> DiagnosticsBundle:
    """Generate a safe diagnostics bundle for a model repository.

    The bundle contains metadata, validation/health/scorecard summaries, and
    source/generated registries. It never includes secrets, raw dataset
    values, or full canonical file contents.
    """
    config = load_repo_config(repo_root)
    model_path = resolve_model_path(repo_root)
    generated_path = resolve_generated_path(repo_root)
    db_path = generated_path / "modelops.db"

    repo_name = config.name if config else "Untitled Repository"
    enabled_packs = config.enabled_domain_packs if config else None

    freshness = check_index_freshness(repo_root, model_path, generated_path)

    validation = _load_validation_summary(model_path, enabled_packs)
    source_registry = _load_source_registry(model_path, repo_root)
    generated_manifest = _load_generated_manifest(generated_path, repo_root)
    pending_changes = _load_pending_changes(model_path)
    dataset_samples = _load_dataset_samples(
        repo_root / (config.data_path if config else "data"), repo_root
    )

    health: dict[str, Any] = {}
    scorecard: dict[str, Any] = {}
    type_counts: dict[str, int] = {}
    object_count = 0
    if db_path.exists():
        from modelops_core.index.queries import get_object_counts_by_type

        type_counts = get_object_counts_by_type(db_path)
        object_count = sum(type_counts.values())
        health = _health_to_dict(generate_repository_health(db_path))
        scorecard = _scorecard_to_dict(generate_scorecard(db_path, repo_root))

    manifest = {
        "martenweave_version": __import__("modelops_core").__version__,
        "generated_at": datetime.now(UTC).isoformat(),
        "repo_root": str(repo_root),
        "repo_name": repo_name,
        "bundle_path": str(out_dir),
        "redaction_note": (
            "Raw dataset values, secrets, and full canonical contents are excluded by default."
        ),
        "index_fresh": freshness.fresh,
        "index_stale_reason": freshness.reason,
        "object_count": object_count,
        "type_counts": type_counts,
        "validation": validation,
        "pending_changes": pending_changes,
        "dataset_samples": {
            "file_count": dataset_samples["file_count"],
            "total_size_bytes": dataset_samples["total_size_bytes"],
        },
        "generated_manifest": {
            "file_count": generated_manifest["file_count"],
            "total_size_bytes": generated_manifest["total_size_bytes"],
        },
        "source_registry": {
            "file_count": source_registry["file_count"],
            "total_size_bytes": source_registry["total_size_bytes"],
        },
    }

    bundle = DiagnosticsBundle(
        manifest=manifest,
        validation=validation,
        health=health,
        scorecard=scorecard,
        config=config.model_dump(mode="json") if config else {},
        source_registry=source_registry,
        generated_manifest=generated_manifest,
        pending_changes=pending_changes,
        dataset_samples=dataset_samples,
    )

    if include_command_outputs:
        bundle.command_outputs = _build_command_outputs(
            repo_root,
            model_path,
            generated_path,
            db_path,
            validation,
            health,
            scorecard,
        )

    return bundle


def write_diagnostics_bundle(
    repo_root: Path,
    out_dir: Path,
    include_command_outputs: bool = False,
) -> DiagnosticsBundle:
    """Generate and write a diagnostics bundle to disk."""
    bundle = generate_diagnostics_bundle(
        repo_root, out_dir, include_command_outputs=include_command_outputs
    )

    out_dir.mkdir(parents=True, exist_ok=True)

    files_to_write: dict[str, Any] = {
        "manifest.json": bundle.manifest,
        "validation.json": bundle.validation,
        "health.json": bundle.health,
        "scorecard.json": bundle.scorecard,
        "config.json": bundle.config,
        "source_registry.json": bundle.source_registry,
        "generated_manifest.json": bundle.generated_manifest,
        "pending_changes.json": bundle.pending_changes,
        "dataset_samples.json": bundle.dataset_samples,
    }

    for name, data in files_to_write.items():
        (out_dir / name).write_text(
            json.dumps(data, indent=2, default=str), encoding="utf-8"
        )

    if bundle.command_outputs:
        commands_dir = out_dir / "commands"
        commands_dir.mkdir(parents=True, exist_ok=True)
        for name, data in bundle.command_outputs.items():
            (commands_dir / name).write_text(
                json.dumps(data, indent=2, default=str), encoding="utf-8"
            )

    return bundle
