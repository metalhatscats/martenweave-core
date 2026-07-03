"""Generate static Markdown documentation and a local read-only HTML viewer."""

from __future__ import annotations

import hashlib
import html
import json
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from modelops_core.__version__ import __version__
from modelops_core.reports.decisions_report import generate_decisions_report
from modelops_core.reports.gap_summary import generate_gap_summary_report
from modelops_core.reports.index_freshness import check_index_freshness
from modelops_core.reports.ownership_report import generate_ownership_report

_ANCHOR_CHARS = set("abcdefghijklmnopqrstuvwxyz0123456789_-")
_OWNER_FIELDS = (
    "business_owner",
    "technical_owner",
    "data_steward",
    "accountable_team",
    "approver",
)
_FACT_FIELDS = (
    "semantic_category",
    "data_classification",
    "endpoint_type",
    "system_type",
    "sap_table",
    "sap_field",
    "technical_name",
    "source_system",
    "source_table",
    "source_field",
    "target_system",
    "target_table",
    "target_field",
    "source_endpoint",
    "target_endpoint",
    "business_attribute",
    "entity_context",
    "usage_type",
    "scope",
    "decision_category",
    "category",
    "severity",
    "risk_level",
)

_VIEWER_FAVICON = (
    """<link rel="icon" href="data:image/svg+xml,"""
    """%3Csvg%20xmlns%3D%27http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%27%20"""
    """viewBox%3D%270%200%20100%20100%27%3E%3Ctext%20y%3D%27.9em%27%20"""
    """font-size%3D%2790%27%3E%F0%9F%A7%B6%3C%2Ftext%3E%3C%2Fsvg%3E">"""
)

_VIEWER_CSS = """
:root {
  color-scheme: light;
  --bg: #f7f8fb;
  --panel: #ffffff;
  --panel-soft: #f0f4f8;
  --text: #1f2937;
  --muted: #64748b;
  --border: #d8e0ea;
  --accent: #175cd3;
  --accent-soft: #e8f0ff;
  --warning: #a15c00;
  --warning-bg: #fff7e6;
  --danger: #b42318;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font: 15px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
.shell { max-width: 1180px; margin: 0 auto; padding: 24px; }
.topbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 22px;
}
.brand h1 { margin: 0 0 4px; font-size: 30px; letter-spacing: -0.03em; }
.brand p { margin: 0; color: var(--muted); }
.nav { display: flex; flex-wrap: wrap; gap: 8px; justify-content: flex-end; }
.nav a, .pill {
  display: inline-flex;
  align-items: center;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--panel);
  color: var(--text);
  padding: 6px 11px;
  font-size: 13px;
}
.nav a[aria-current="page"] { background: var(--accent-soft); border-color: #b7cdfb; }
.notice {
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 12px 14px;
  background: var(--panel);
  margin: 0 0 16px;
}
.notice.warning { background: var(--warning-bg); border-color: #f3ca7a; color: var(--warning); }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 14px; }
.card {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 16px;
  min-width: 0;
}
.card h2, .card h3 { margin: 0 0 10px; letter-spacing: -0.02em; }
.metric { font-size: 28px; font-weight: 700; letter-spacing: -0.03em; }
.muted { color: var(--muted); }
.section { margin-top: 18px; }
.searchbox {
  width: 100%;
  max-width: 680px;
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 11px 13px;
  font: inherit;
  background: var(--panel);
}
.filters { display: flex; flex-wrap: wrap; gap: 8px; margin: 12px 0; }
table {
  width: 100%;
  border-collapse: collapse;
  background: var(--panel);
  border-radius: 14px;
  overflow: hidden;
}
th, td {
  text-align: left;
  padding: 10px 12px;
  border-bottom: 1px solid var(--border);
  vertical-align: top;
}
th {
  font-size: 12px;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: .04em;
  background: var(--panel-soft);
}
tr:last-child td { border-bottom: 0; }
.badge {
  display: inline-block;
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 2px 8px;
  margin: 2px 4px 2px 0;
  font-size: 12px;
  background: var(--panel-soft);
}
.empty {
  color: var(--muted);
  background: var(--panel-soft);
  border: 1px dashed var(--border);
  border-radius: 12px;
  padding: 12px;
}
.object-title { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }
.body-text {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  background: #0f172a;
  color: #e2e8f0;
  border-radius: 12px;
  padding: 14px;
}
.two-col { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 14px; }
code { background: var(--panel-soft); border-radius: 5px; padding: 1px 5px; }
footer { margin-top: 28px; color: var(--muted); font-size: 13px; }
@media (max-width: 760px) {
  .topbar, .two-col { display: block; }
  .nav { justify-content: flex-start; margin-top: 14px; }
  .shell { padding: 16px; }
  table { display: block; overflow-x: auto; }
}
""".strip()

_VIEWER_JS = """
(function () {
  function normalise(value) {
    return (value || "").toString().toLowerCase();
  }

  function setupSearch() {
    var input = document.querySelector("[data-viewer-search]");
    var rows = Array.prototype.slice.call(document.querySelectorAll("[data-search-row]"));
    var count = document.querySelector("[data-result-count]");
    if (!input || rows.length === 0) {
      return;
    }

    function applyFilter() {
      var query = normalise(input.value).trim();
      var visible = 0;
      rows.forEach(function (row) {
        var text = normalise(row.getAttribute("data-search"));
        var keep = query === "" || text.indexOf(query) !== -1;
        row.hidden = !keep;
        if (keep) {
          visible += 1;
        }
      });
      if (count) {
        count.textContent = visible + " object" + (visible === 1 ? "" : "s");
      }
    }

    input.addEventListener("input", applyFilter);
    applyFilter();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setupSearch);
  } else {
    setupSearch();
  }
})();
""".strip()


def _anchor(text: str) -> str:
    """Convert a string to a Markdown anchor."""
    lowered = text.lower().replace(" ", "-").replace("_", "-")
    return "".join(c for c in lowered if c in _ANCHOR_CHARS)


def _fm_field(frontmatter: dict[str, Any], key: str) -> str | None:
    val = frontmatter.get(key)
    if val is None or val == "":
        return None
    if isinstance(val, list):
        return ", ".join(str(item) for item in val if item)
    if isinstance(val, dict):
        return json.dumps(val, sort_keys=True)
    return str(val)


def generate_static_docs(
    repo_root: Path,
    output_dir: Path,
    db_path: Path | None = None,
) -> Path:
    """Generate static Markdown docs and a local HTML viewer from the SQLite index.

    Args:
        repo_root: Path to the model repository root.
        output_dir: Directory where docs and viewer files will be written.
        db_path: Optional path to the SQLite database. Defaults to
            ``<repo_root>/generated/modelops.db``.

    Returns:
        Path to the generated output directory.
    """
    if db_path is None:
        db_path = repo_root / "generated" / "modelops.db"

    if not db_path.exists():
        raise FileNotFoundError(
            f"No index found at {db_path}. Run `martenweave build-index` first."
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    try:
        all_objects = _load_objects(conn)
        objects_by_type: dict[str, list[dict[str, Any]]] = {}
        for obj in all_objects:
            objects_by_type.setdefault(obj["type"], []).append(obj)

        relationships = _load_relationships(conn)
        validation_results = _load_validation_results(conn)
        index_manifest = _load_index_manifest(conn)
        tags = _load_tags(conn)
    finally:
        conn.close()

    file_map = _build_object_file_map(all_objects)
    freshness = check_index_freshness(repo_root, generated_path=db_path.parent)
    ownership = generate_ownership_report(db_path, repo_root)
    decisions = generate_decisions_report(db_path, repo_root)
    gaps = generate_gap_summary_report(db_path, repo_root)

    # Generate Markdown first to preserve existing docs-build behaviour.
    _write_index_md(output_dir, all_objects, objects_by_type)
    _write_objects_md(output_dir, all_objects)
    for obj_type, objs in objects_by_type.items():
        _write_type_md(output_dir, obj_type, objs)

    viewer_context = {
        "repo_root": repo_root,
        "output_dir": output_dir,
        "db_path": db_path,
        "objects": all_objects,
        "objects_by_type": objects_by_type,
        "relationships": relationships,
        "validation_results": validation_results,
        "index_manifest": index_manifest,
        "tags": tags,
        "file_map": file_map,
        "freshness": freshness,
        "ownership": ownership,
        "decisions": decisions,
        "gaps": gaps,
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "repo_meta": _load_repo_metadata(repo_root),
    }
    _write_viewer(viewer_context)

    return output_dir


def _load_objects(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, type, status, name, title, domain, description, "
        "frontmatter_json, body FROM objects ORDER BY type, id"
    )
    rows = cursor.fetchall()
    objects: list[dict[str, Any]] = []
    for row in rows:
        frontmatter = json.loads(row[7] or "{}")
        obj = {
            "id": row[0],
            "type": row[1],
            "status": row[2],
            "name": row[3],
            "title": row[4],
            "domain": row[5],
            "description": row[6],
            "frontmatter": frontmatter,
            "body": row[8] or "",
        }
        obj["label"] = obj["name"] or obj["title"] or obj["id"]
        objects.append(obj)
    return objects


def _load_relationships(conn: sqlite3.Connection) -> list[dict[str, str]]:
    rows = conn.execute(
        "SELECT from_object_id, relationship_type, relationship_class, to_object_id, confidence "
        "FROM object_relationships ORDER BY from_object_id, relationship_type, to_object_id"
    ).fetchall()
    return [
        {
            "from": row[0],
            "type": row[1],
            "class": row[2],
            "to": row[3],
            "confidence": row[4],
        }
        for row in rows
    ]


def _load_validation_results(conn: sqlite3.Connection) -> list[dict[str, str]]:
    rows = conn.execute(
        "SELECT severity, code, message, object_id, object_type, field_path "
        "FROM validation_results ORDER BY severity, code, object_id"
    ).fetchall()
    return [
        {
            "severity": row[0],
            "code": row[1],
            "message": row[2],
            "object_id": row[3] or "",
            "object_type": row[4] or "",
            "field_path": row[5] or "",
        }
        for row in rows
    ]


def _load_index_manifest(conn: sqlite3.Connection) -> dict[str, str]:
    rows = conn.execute("SELECT key, value FROM index_manifest ORDER BY key").fetchall()
    return {str(key): str(value) for key, value in rows}


def _load_tags(conn: sqlite3.Connection) -> dict[str, list[str]]:
    rows = conn.execute("SELECT object_id, tag FROM tags ORDER BY object_id, tag").fetchall()
    tags: dict[str, list[str]] = defaultdict(list)
    for object_id, tag in rows:
        tags[str(object_id)].append(str(tag))
    return dict(tags)


def _load_repo_metadata(repo_root: Path) -> dict[str, str]:
    config_path = repo_root / "modelops.config.yaml"
    if not config_path.exists():
        config_path = repo_root / "modelops.config.yml"
    data: dict[str, Any] = {}
    if config_path.exists():
        try:
            loaded = yaml.safe_load(config_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                data = loaded
        except Exception:
            data = {}
    name = data.get("name") or data.get("workspace_name") or repo_root.name
    if str(name).strip() == "Untitled Repository":
        name = repo_root.name
    return {
        "name": str(name),
        "version": str(data.get("version") or "unknown"),
        "schema_version": str(data.get("schema_version") or "unknown"),
    }


def _build_object_file_map(objects: list[dict[str, Any]]) -> dict[str, str]:
    bases: dict[str, list[str]] = defaultdict(list)
    for obj in objects:
        base = _safe_filename_base(obj["id"])
        bases[base].append(obj["id"])

    file_map: dict[str, str] = {}
    for obj in objects:
        obj_id = obj["id"]
        base = _safe_filename_base(obj_id)
        if len(bases[base]) > 1:
            digest = hashlib.sha256(obj_id.encode("utf-8")).hexdigest()[:8]
            base = f"{base}-{digest}"
        file_map[obj_id] = f"objects/{base}.html"
    return file_map


def _safe_filename_base(obj_id: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", obj_id.lower()).strip("-")
    if not base:
        base = hashlib.sha256(obj_id.encode("utf-8")).hexdigest()[:12]
    return base


def _write_index_md(
    output_dir: Path,
    all_objects: list[dict[str, Any]],
    objects_by_type: dict[str, list[dict[str, Any]]],
) -> None:
    lines: list[str] = [
        "# Model Documentation",
        "",
        "> **Generated view** — This documentation is a generated view over the "
        "canonical model files. The canonical Markdown + YAML frontmatter objects "
        "in `model/` are the source of truth. This site can be rebuilt at any time "
        "with `martenweave build-index` and `martenweave docs-build`.",
        "",
        "## Local static viewer",
        "",
        "Open [index.html](index.html) for the generated local, static, read-only viewer. "
        "It is disposable output from `modelops.db`; it is not a hosted UI, editor, "
        "login surface, SAP write-back path, or AI mutation workflow.",
        "",
        "## Overview",
        "",
        f"- **Total objects**: {len(all_objects)}",
        "- **Object types**:",
    ]

    for obj_type in sorted(objects_by_type.keys()):
        count = len(objects_by_type[obj_type])
        anchor = _anchor(obj_type)
        lines.append(f"  - [{obj_type}]({anchor}.md): {count}")

    lines.extend(
        [
            "",
            "## Browse",
            "",
            "- [All objects](objects.md)",
        ]
    )

    for obj_type in sorted(objects_by_type.keys()):
        anchor = _anchor(obj_type)
        lines.append(f"- [{obj_type}]({anchor}.md)")

    lines.append("")

    (output_dir / "index.md").write_text("\n".join(lines), encoding="utf-8")


def _write_objects_md(output_dir: Path, all_objects: list[dict[str, Any]]) -> None:
    lines: list[str] = [
        "# All Objects",
        "",
        "> **Generated view** — See [index.md](index.md) for overview.",
        "",
    ]

    for obj in all_objects:
        obj_id = obj["id"]
        obj_type = obj["type"]
        name = obj["name"] or obj["title"] or obj_id
        status = obj["status"]
        anchor = _anchor(obj_id)
        lines.append(f"### {name} (`{obj_id}`) {{#{anchor}}}")
        lines.append(f"- **Type**: {obj_type}")
        lines.append(f"- **Status**: {status}")
        if obj["domain"]:
            lines.append(f"- **Domain**: {obj['domain']}")
        if obj["description"]:
            lines.append(f"- **Description**: {obj['description']}")
        lines.append("")

    (output_dir / "objects.md").write_text("\n".join(lines), encoding="utf-8")


def _write_type_md(
    output_dir: Path,
    obj_type: str,
    objs: list[dict[str, Any]],
) -> None:
    filename = f"{_anchor(obj_type)}.md"
    lines: list[str] = [
        f"# {obj_type}",
        "",
        f"> **Generated view** — [{len(objs)} object(s)](objects.md)",
        "",
    ]

    for obj in objs:
        obj_id = obj["id"]
        name = obj["name"] or obj["title"] or obj_id
        status = obj["status"]
        anchor = _anchor(obj_id)
        lines.append(f"## {name} (`{obj_id}`) {{#{anchor}}}")
        lines.append(f"- **Status**: {status}")
        if obj["domain"]:
            lines.append(f"- **Domain**: {obj['domain']}")

        fm = obj["frontmatter"]
        for key in _FACT_FIELDS + _OWNER_FIELDS:
            val = _fm_field(fm, key)
            if val:
                lines.append(f"- **{key.replace('_', ' ').title()}**: {val}")

        if obj["description"]:
            lines.append(f"- **Description**: {obj['description']}")

        lines.append("")

    (output_dir / filename).write_text("\n".join(lines), encoding="utf-8")


def _write_viewer(context: dict[str, Any]) -> None:
    output_dir: Path = context["output_dir"]
    (output_dir / "assets").mkdir(parents=True, exist_ok=True)
    (output_dir / "objects").mkdir(parents=True, exist_ok=True)

    (output_dir / "assets" / "viewer.css").write_text(_VIEWER_CSS + "\n", encoding="utf-8")
    (output_dir / "assets" / "viewer.js").write_text(_VIEWER_JS + "\n", encoding="utf-8")

    _write_search_index(context)
    _write_manifest(context)
    _write_dashboard(context)
    _write_objects_html(context)
    _write_gaps_html(context)
    _write_decisions_html(context)
    _write_owners_html(context)
    for obj in context["objects"]:
        _write_object_detail(context, obj)


def _write_search_index(context: dict[str, Any]) -> None:
    output_dir: Path = context["output_dir"]
    file_map: dict[str, str] = context["file_map"]
    items = []
    for obj in context["objects"]:
        items.append(
            {
                "id": obj["id"],
                "type": obj["type"],
                "label": obj["label"],
                "status": obj["status"],
                "href": file_map[obj["id"]],
                "terms": _object_search_terms(context, obj),
            }
        )
    (output_dir / "search-index.json").write_text(
        json.dumps(items, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_manifest(context: dict[str, Any]) -> None:
    output_dir: Path = context["output_dir"]
    freshness = context["freshness"]
    validation_counts = _validation_counts(context["validation_results"])
    manifest = {
        "viewer_schema_version": "1.0",
        "generator": "martenweave docs-build",
        "package_version": __version__,
        "generated_at_utc": context["generated_at"],
        "repository": context["repo_meta"],
        "object_count": len(context["objects"]),
        "type_counts": dict(sorted(Counter(obj["type"] for obj in context["objects"]).items())),
        "validation_counts": validation_counts,
        "index": {
            "fresh": freshness.fresh,
            "reason": freshness.reason,
            "db_mtime_utc": _iso_or_none(freshness.db_mtime),
            "newest_source_mtime_utc": _iso_or_none(freshness.newest_source_mtime),
            "source_content_hash": context["index_manifest"].get("source_content_hash"),
            "built_at_utc": context["index_manifest"].get("build_timestamp")
            or context["index_manifest"].get("built_at"),
        },
        "outputs": {
            "dashboard": "index.html",
            "objects": "objects.html",
            "gaps": "gaps.html",
            "decisions": "decisions.html",
            "owners": "owners.html",
            "search_index": "search-index.json",
        },
        "product_boundary": {
            "local_static_read_only": True,
            "hosted_user_interface": False,
            "editing": False,
            "authentication": False,
            "sap_write_back": False,
            "ai_auto_mutation": False,
        },
    }
    (output_dir / "viewer-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_dashboard(context: dict[str, Any]) -> None:
    repo = context["repo_meta"]
    objects = context["objects"]
    type_counts = Counter(obj["type"] for obj in objects)
    validation_counts = _validation_counts(context["validation_results"])
    freshness = context["freshness"]
    body = [
        _notice_blocks(freshness),
        _read_only_notice(),
        '<div class="grid">',
        _metric_card("Objects", str(len(objects)), "Indexed canonical objects"),
        _metric_card("Object types", str(len(type_counts)), "Types represented in the index"),
        _metric_card(
            "Validation findings",
            str(sum(validation_counts.values())),
            ", ".join(f"{k}: {v}" for k, v in sorted(validation_counts.items())) or "None",
        ),
        _metric_card(
            "Index freshness",
            "Fresh" if freshness.fresh else "Stale",
            freshness.reason or "Hash matches canonical source",
        ),
        "</div>",
        '<div class="section card">',
        "<h2>Repository</h2>",
        "<table><tbody>",
        _fact_row("Repository", repo["name"]),
        _fact_row("Repository version", repo["version"]),
        _fact_row("Schema version", repo["schema_version"]),
        _fact_row("Martenweave package", __version__),
        _fact_row("Index built", context["index_manifest"].get("built_at", "unknown")),
        _fact_row("Viewer generated", context["generated_at"]),
        "</tbody></table>",
        "</div>",
        '<div class="section card">',
        "<h2>Type counts</h2>",
        "<table><thead><tr><th>Type</th><th>Count</th></tr></thead><tbody>",
    ]
    for obj_type, count in sorted(type_counts.items()):
        body.append(f"<tr><td>{_e(obj_type)}</td><td>{count}</td></tr>")
    body.extend(
        [
            "</tbody></table>",
            "</div>",
            '<div class="section card">',
            "<h2>Quick search</h2>",
            '<input class="searchbox" data-viewer-search id="viewer-search" '
            'aria-label="Filter objects" '
            'placeholder="Filter objects by Customer Group, KNVV, KDGRP, owner, type...">',
            '<p class="muted"><span data-result-count></span> shown. '
            "Search runs locally from embedded rows and does not require network access.</p>",
            _objects_table(context, max_rows=12),
            '<p><a href="objects.html">Open full searchable object list</a></p>',
            "</div>",
        ]
    )
    _write_page(context, "index.html", "Local Static Viewer", body, current="index")


def _write_objects_html(context: dict[str, Any]) -> None:
    body = [
        _notice_blocks(context["freshness"]),
        _read_only_notice(),
        '<div class="card">',
        "<h2>Searchable objects</h2>",
        '<input class="searchbox" data-viewer-search id="viewer-search" '
        'aria-label="Search objects" '
        'placeholder="Search IDs, labels, Customer Group, KNVV, KDGRP, owners, related terms...">',
        '<p class="muted"><span data-result-count></span> shown. Search is local and works from '
        "file:// because the rows contain their own search terms.</p>",
        '<div class="filters">',
    ]
    for obj_type in sorted(context["objects_by_type"]):
        body.append(f'<span class="pill">{_e(obj_type)}</span>')
    body.extend(["</div>", _objects_table(context), "</div>"])
    _write_page(context, "objects.html", "Objects", body, current="objects")


def _write_gaps_html(context: dict[str, Any]) -> None:
    gaps = context["gaps"]
    validation_results = context["validation_results"]
    issue_objects = [obj for obj in context["objects"] if obj["type"] == "Issue"]
    body = [
        _notice_blocks(context["freshness"]),
        '<div class="grid">',
        _metric_card("Total gap count", str(gaps.total_gap_count), "Deterministic gap sources"),
        _metric_card("Gap score", str(gaps.gap_score), "Capped ratio of gaps to objects"),
        _metric_card(
            "Sources checked",
            str(len(gaps.sources_checked)),
            ", ".join(gaps.sources_checked),
        ),
        "</div>",
        '<div class="section card">',
        "<h2>Gap types</h2>",
    ]
    if gaps.gaps_by_type:
        body.append(
            "<table><thead><tr><th>Gap type</th><th>Count</th><th>Samples</th></tr></thead><tbody>"
        )
        for gap_type, summary in gaps.gaps_by_type.items():
            links = ", ".join(_object_link(context, obj_id) for obj_id in summary.sample_object_ids)
            body.append(f"<tr><td>{_e(gap_type)}</td><td>{summary.count}</td><td>{links}</td></tr>")
        body.append("</tbody></table>")
    else:
        body.append(_empty("No deterministic model gaps were found in the current index."))
    body.extend(
        [
            "</div>",
            '<div class="section card">',
            "<h2>Validation findings</h2>",
        ]
    )
    if validation_results:
        body.append(
            "<table><thead><tr><th>Severity</th><th>Code</th><th>Object</th><th>Message</th></tr></thead><tbody>"
        )
        for row in validation_results:
            body.append(
                "<tr>"
                f"<td>{_e(row['severity'])}</td>"
                f"<td>{_e(row['code'])}</td>"
                f"<td>{_object_link(context, row['object_id']) if row['object_id'] else ''}</td>"
                f"<td>{_e(row['message'])}</td>"
                "</tr>"
            )
        body.append("</tbody></table>")
    else:
        body.append(_empty("No validation findings are present in the SQLite index."))
    body.extend(
        [
            "</div>",
            '<div class="section card">',
            "<h2>Canonical issues</h2>",
        ]
    )
    if issue_objects:
        body.append(_objects_table(context, rows=issue_objects))
    else:
        body.append(_empty("No canonical Issue objects are present in this model."))
    body.extend(
        [
            "</div>",
            '<div class="section card">',
            "<h2>Dataset gap metrics</h2>",
            _empty(
                "Dataset-specific metrics are not included unless deterministic dataset gap "
                "artifacts have been produced. Run "
                "<code>martenweave gaps --repo examples/customer_bp_model</code> for a local "
                "dataset-oriented gap pass, then rebuild generated artifacts as needed."
            ),
            "</div>",
        ]
    )
    _write_page(context, "gaps.html", "Gaps", body, current="gaps")


def _write_decisions_html(context: dict[str, Any]) -> None:
    decisions_report = context["decisions"]
    decision_objects = [obj for obj in context["objects"] if obj["type"] == "Decision"]
    body = [
        _notice_blocks(context["freshness"]),
        '<div class="grid">',
        _metric_card(
            "Decisions",
            str(decisions_report.total_decisions),
            "Canonical Decision objects",
        ),
        _metric_card(
            "With evidence",
            str(decisions_report.total_with_evidence),
            f"{decisions_report.overall_coverage_percent}% evidence coverage",
        ),
        "</div>",
        '<div class="section card">',
        "<h2>Canonical decisions</h2>",
    ]
    if decision_objects:
        body.append(
            "<table><thead><tr><th>Decision</th><th>Status</th><th>Domain</th>"
            "<th>Evidence</th><th>Related objects</th></tr></thead><tbody>"
        )
        for obj in decision_objects:
            fm = obj["frontmatter"]
            evidence = _refs_from_value(fm.get("evidence"))
            related = _related_for_object(context, obj["id"])
            body.append(
                "<tr>"
                f"<td>{_object_link(context, obj['id'])}</td>"
                f"<td>{_e(obj['status'])}</td>"
                f"<td>{_e(obj.get('domain') or '')}</td>"
                f"<td>{_link_refs(context, evidence)}</td>"
                f"<td>{_link_refs(context, related[:8])}</td>"
                "</tr>"
            )
        body.append("</tbody></table>")
    else:
        body.append(_empty("No canonical Decision objects are present in this model."))
    body.extend(
        [
            "</div>",
            '<div class="section card">',
            "<h2>Evidence coverage by domain</h2>",
        ]
    )
    if decisions_report.evidence_coverage:
        body.append(
            "<table><thead><tr><th>Domain</th><th>Decisions</th>"
            "<th>With evidence</th><th>Coverage</th></tr></thead><tbody>"
        )
        for row in decisions_report.evidence_coverage:
            body.append(
                "<tr>"
                f"<td>{_e(row.domain or 'Unassigned')}</td>"
                f"<td>{row.total_decisions}</td>"
                f"<td>{row.decisions_with_evidence}</td>"
                f"<td>{row.coverage_percent}%</td>"
                "</tr>"
            )
        body.append("</tbody></table>")
    else:
        body.append(_empty("No decision evidence coverage rows are available."))
    body.append("</div>")
    _write_page(context, "decisions.html", "Decisions", body, current="decisions")


def _write_owners_html(context: dict[str, Any]) -> None:
    ownership = context["ownership"]
    body = [
        _notice_blocks(context["freshness"]),
        '<div class="grid">',
        _metric_card(
            "Coverage",
            f"{ownership.coverage_percent}%",
            "Ownership-eligible active objects",
        ),
        _metric_card("Eligible", str(ownership.total_eligible), "Objects in ownership scope"),
        _metric_card(
            "With owner",
            str(ownership.total_with_owner),
            "Objects with at least one owner field",
        ),
        _metric_card(
            "Missing owner",
            str(len(ownership.orphaned_objects)),
            "Objects needing stewardship",
        ),
        "</div>",
        '<div class="section card">',
        "<h2>Owner workload by role and type</h2>",
    ]
    if ownership.owners:
        body.append(
            "<table><thead><tr><th>Owner</th><th>Role</th><th>Objects</th><th>Types</th></tr></thead><tbody>"
        )
        for owner in ownership.owners:
            type_counts = ", ".join(
                f"{obj_type}: {count}" for obj_type, count in sorted(owner.object_types.items())
            )
            body.append(
                "<tr>"
                f"<td>{_e(owner.owner_id)}</td>"
                f"<td>{_e(owner.role)}</td>"
                f"<td>{owner.object_count}</td>"
                f"<td>{_e(type_counts)}</td>"
                "</tr>"
            )
        body.append("</tbody></table>")
    else:
        body.append(
            _empty("No owner assignments are present on active ownership-eligible objects.")
        )
    body.extend(["</div>", '<div class="section card">', "<h2>Missing-owner objects</h2>"])
    if ownership.orphaned_objects:
        body.append(
            "<table><thead><tr><th>Object</th><th>Type</th><th>Name</th></tr></thead><tbody>"
        )
        for obj in ownership.orphaned_objects:
            body.append(
                "<tr>"
                f"<td>{_object_link(context, obj.object_id)}</td>"
                f"<td>{_e(obj.object_type)}</td>"
                f"<td>{_e(obj.object_name or '')}</td>"
                "</tr>"
            )
        body.append("</tbody></table>")
    else:
        body.append(_empty("No missing-owner objects were found."))
    body.append("</div>")
    _write_page(context, "owners.html", "Owners", body, current="owners")


def _write_object_detail(context: dict[str, Any], obj: dict[str, Any]) -> None:
    output_dir: Path = context["output_dir"]
    file_map: dict[str, str] = context["file_map"]
    object_index = _object_index(context)
    inbound, outbound = _relationships_for(context, obj["id"])
    fm = obj["frontmatter"]
    old_depth = context.get("_current_depth")
    context["_current_depth"] = "../"
    try:
        body = [
            _notice_blocks(context["freshness"], depth="../"),
            '<div class="card">',
            '<div class="object-title">',
            f"<h2>{_e(obj['label'])}</h2>",
            f'<span class="badge">{_e(obj["id"])}</span>',
            f'<span class="badge">{_e(obj["type"])}</span>',
            f'<span class="badge">{_e(obj["status"])}</span>',
            "</div>",
            _read_only_notice(),
            "</div>",
            '<div class="two-col section">',
            '<div class="card"><h2>Facts</h2><table><tbody>',
            _fact_row("ID", obj["id"]),
            _fact_row("Type", obj["type"]),
            _fact_row("Status", obj["status"]),
            _fact_row("Domain", obj.get("domain") or ""),
        ]
        for key in _FACT_FIELDS:
            value = _fm_field(fm, key)
            if value:
                body.append(_fact_row(key.replace("_", " ").title(), value))
        body.extend(["</tbody></table></div>", '<div class="card"><h2>Owners</h2>'])
        owner_rows = []
        for key in _OWNER_FIELDS:
            value = _fm_field(fm, key)
            if value:
                owner_rows.append(_fact_row(key.replace("_", " ").title(), value))
        if owner_rows:
            body.append("<table><tbody>")
            body.extend(owner_rows)
            body.append("</tbody></table>")
        else:
            body.append(_empty("No owner fields are assigned on this object."))
        body.extend(["</div>", "</div>"])

        body.extend(['<div class="section card"><h2>Description</h2>'])
        if obj.get("description"):
            body.append(f"<p>{_e(obj['description'])}</p>")
        else:
            body.append(_empty("No description is present in the index."))
        if obj.get("body"):
            body.append("<h3>Canonical body</h3>")
            body.append(f'<div class="body-text">{_e(obj["body"])}</div>')
        else:
            body.append(_empty("No canonical body content is present."))
        body.append("</div>")

        body.extend(
            [
                '<div class="two-col section">',
                '<div class="card"><h2>Outgoing relationships</h2>',
            ]
        )
        body.append(_relationship_table(context, outbound, "to"))
        body.extend(["</div>", '<div class="card"><h2>Incoming relationships</h2>'])
        body.append(_relationship_table(context, inbound, "from"))
        body.extend(["</div>", "</div>"])

        for title, refs in (
            ("Mappings", _typed_related(context, obj["id"], {"Mapping"})),
            ("Rules", _typed_related(context, obj["id"], {"ValidationRule"})),
            ("Issues", _typed_related(context, obj["id"], {"Issue"})),
            ("Decisions", _typed_related(context, obj["id"], {"Decision"})),
            ("Evidence", _typed_related(context, obj["id"], {"Evidence"})),
        ):
            body.extend([f'<div class="section card"><h2>{title}</h2>'])
            if refs:
                body.append("<ul>")
                for ref in refs:
                    label = object_index.get(ref, {}).get("label", ref)
                    body.append(
                        f"<li>{_object_link(context, ref)} "
                        f'<span class="muted">{_e(label)}</span></li>'
                    )
                body.append("</ul>")
            else:
                body.append(
                    _empty(f"No {title.lower()} are connected by one-hop indexed relationships.")
                )
            body.append("</div>")

        target = output_dir / file_map[obj["id"]]
        _write_page(context, file_map[obj["id"]], obj["label"], body, current="", depth="../")
        assert target.exists()
    finally:
        if old_depth is None:
            context.pop("_current_depth", None)
        else:
            context["_current_depth"] = old_depth


def _write_page(
    context: dict[str, Any],
    relative_path: str,
    title: str,
    body: list[str],
    current: str,
    depth: str = "",
) -> None:
    output_dir: Path = context["output_dir"]
    nav = [
        ("index", "Dashboard", f"{depth}index.html"),
        ("objects", "Objects", f"{depth}objects.html"),
        ("gaps", "Gaps", f"{depth}gaps.html"),
        ("decisions", "Decisions", f"{depth}decisions.html"),
        ("owners", "Owners", f"{depth}owners.html"),
        ("manifest", "Manifest", f"{depth}viewer-manifest.json"),
    ]
    nav_items = []
    for key, label, href in nav:
        current_attr = ' aria-current="page"' if key == current else ""
        nav_items.append(f'<a href="{href}"{current_attr}>{label}</a>')
    nav_html = " ".join(nav_items)
    html_text = "\n".join(
        [
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            f"<title>{_e(title)} · Martenweave Viewer</title>",
            _VIEWER_FAVICON,
            f'<link rel="stylesheet" href="{depth}assets/viewer.css">',
            f'<script defer src="{depth}assets/viewer.js"></script>',
            "</head>",
            "<body>",
            '<main class="shell">',
            '<header class="topbar">',
            '<div class="brand">',
            f"<h1>{_e(title)}</h1>",
            "<p>Generated local static read-only viewer over the SQLite index.</p>",
            "</div>",
            f'<nav class="nav" aria-label="Viewer navigation">{nav_html}</nav>',
            "</header>",
            *body,
            "<footer>",
            "Generated output is disposable. Canonical Markdown + YAML files remain authoritative. "
            "No hosted UI, login, editor, SAP write-back, or AI auto-mutation is included.",
            "</footer>",
            "</main>",
            "</body>",
            "</html>",
            "",
        ]
    )
    (output_dir / relative_path).write_text(html_text, encoding="utf-8")


def _objects_table(
    context: dict[str, Any],
    rows: list[dict[str, Any]] | None = None,
    max_rows: int | None = None,
) -> str:
    objects = rows or context["objects"]
    if max_rows is not None:
        objects = objects[:max_rows]
    parts = [
        "<table>",
        "<thead><tr><th>ID</th><th>Type</th><th>Label</th><th>Status</th><th>Owners</th><th>Hints</th></tr></thead>",
        "<tbody>",
    ]
    for obj in objects:
        fm = obj["frontmatter"]
        owners = _owners_text(fm)
        hints = _hints_text(fm)
        search_terms = _object_search_terms(context, obj)
        parts.append(
            f'<tr data-search-row data-search="{_attr(search_terms)}">'
            f"<td>{_object_link(context, obj['id'])}</td>"
            f"<td>{_e(obj['type'])}</td>"
            f"<td>{_e(obj['label'])}</td>"
            f"<td>{_e(obj['status'])}</td>"
            f"<td>{_e(owners)}</td>"
            f"<td>{_e(hints)}</td>"
            "</tr>"
        )
    parts.extend(["</tbody>", "</table>"])
    return "\n".join(parts)


def _relationship_table(
    context: dict[str, Any], rows: list[dict[str, str]], target_key: str
) -> str:
    if not rows:
        return _empty("No indexed one-hop relationships in this direction.")
    parts = [
        "<table><thead><tr><th>Relationship</th><th>Object</th><th>Class</th></tr></thead><tbody>"
    ]
    for row in rows:
        parts.append(
            "<tr>"
            f"<td>{_e(row['type'])}</td>"
            f"<td>{_object_link(context, row[target_key])}</td>"
            f"<td>{_e(row['class'])}</td>"
            "</tr>"
        )
    parts.append("</tbody></table>")
    return "\n".join(parts)


def _relationships_for(
    context: dict[str, Any],
    obj_id: str,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    inbound = [rel for rel in context["relationships"] if rel["to"] == obj_id]
    outbound = [rel for rel in context["relationships"] if rel["from"] == obj_id]
    return inbound, outbound


def _related_for_object(context: dict[str, Any], obj_id: str) -> list[str]:
    refs = set()
    for rel in context["relationships"]:
        if rel["from"] == obj_id:
            refs.add(rel["to"])
        if rel["to"] == obj_id:
            refs.add(rel["from"])
    return sorted(refs)


def _typed_related(context: dict[str, Any], obj_id: str, types: set[str]) -> list[str]:
    index = _object_index(context)
    return [
        ref
        for ref in _related_for_object(context, obj_id)
        if index.get(ref, {}).get("type") in types
    ]


def _object_search_terms(context: dict[str, Any], obj: dict[str, Any]) -> str:
    terms = [
        obj["id"],
        obj["type"],
        obj["status"],
        obj["label"],
        obj.get("domain") or "",
        obj.get("description") or "",
        _owners_text(obj["frontmatter"]),
        _hints_text(obj["frontmatter"]),
        " ".join(context["tags"].get(obj["id"], [])),
    ]
    index = _object_index(context)
    for ref in _related_for_object(context, obj["id"]):
        related = index.get(ref)
        if not related:
            terms.append(ref)
            continue
        terms.extend(
            [
                related["id"],
                related["type"],
                related["label"],
                _hints_text(related["frontmatter"]),
            ]
        )
    return " ".join(str(term) for term in terms if term)


def _object_index(context: dict[str, Any]) -> dict[str, dict[str, Any]]:
    index = context.get("_object_index")
    if index is None:
        index = {obj["id"]: obj for obj in context["objects"]}
        context["_object_index"] = index
    return index


def _owners_text(fm: dict[str, Any]) -> str:
    values: list[str] = []
    for key in _OWNER_FIELDS:
        value = _fm_field(fm, key)
        if value:
            values.append(value)
    return ", ".join(values)


def _hints_text(fm: dict[str, Any]) -> str:
    values: list[str] = []
    for key in (
        "sap_table",
        "sap_field",
        "technical_name",
        "source_table",
        "source_field",
        "target_table",
        "target_field",
        "endpoint_type",
        "system_type",
    ):
        value = _fm_field(fm, key)
        if value:
            values.append(value)
    return ", ".join(values)


def _refs_from_value(value: Any) -> list[str]:
    if isinstance(value, str) and value:
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if item]
    return []


def _link_refs(context: dict[str, Any], refs: list[str]) -> str:
    if not refs:
        return _empty("None")
    return ", ".join(_object_link(context, ref) for ref in refs)


def _object_link(context: dict[str, Any], obj_id: str) -> str:
    file_map: dict[str, str] = context["file_map"]
    if obj_id in file_map:
        href = _relative_href(context, file_map[obj_id])
        return f'<a href="{href}"><code>{_e(obj_id)}</code></a>'
    return f"<code>{_e(obj_id)}</code>"


def _relative_href(context: dict[str, Any], href: str) -> str:
    # Detail pages call _object_link while writing under objects/, so adjust one level up.
    current_depth = context.get("_current_depth", "")
    if current_depth and not href.startswith("../"):
        return current_depth + href
    return href


def _validation_counts(results: list[dict[str, str]]) -> dict[str, int]:
    counts = Counter(row["severity"] for row in results)
    return dict(sorted(counts.items()))


def _notice_blocks(freshness: Any, depth: str = "") -> str:
    if freshness.fresh:
        return (
            '<div class="notice">Index freshness: <strong>fresh</strong>. '
            "Viewer content is generated from the current SQLite index.</div>"
        )
    reason = freshness.reason or "unknown"
    return (
        '<div class="notice warning">Index freshness: <strong>stale</strong>. '
        f"Reason: {_e(reason)}. Rebuild with <code>martenweave build-index</code> "
        "before treating "
        f'<a href="{depth}viewer-manifest.json">this manifest</a> as current.</div>'
    )


def _read_only_notice() -> str:
    return (
        '<div class="notice">Read-only generated artifact. Canonical files in '
        "<code>model/</code> remain the source of truth; this viewer can be deleted "
        "and rebuilt at any time.</div>"
    )


def _metric_card(title: str, value: str, subtitle: str) -> str:
    return (
        '<div class="card">'
        f"<h3>{_e(title)}</h3>"
        f'<div class="metric">{_e(value)}</div>'
        f'<div class="muted">{_e(subtitle)}</div>'
        "</div>"
    )


def _fact_row(label: str, value: str) -> str:
    rendered_value = _e(value) if value else '<span class="muted">None</span>'
    return f"<tr><th>{_e(label)}</th><td>{rendered_value}</td></tr>"


def _empty(message: str) -> str:
    return f'<div class="empty">{message}</div>'


def _iso_or_none(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _e(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _attr(value: Any) -> str:
    return html.escape(str(value), quote=True)
