"""Assertion helper for the installed-wheel first-value smoke (issue #625).

The shell wrapper ``release_smoke_wheel_first_value.sh`` builds the wheel,
installs it into an isolated virtualenv, and drives this helper with that
environment's Python so every check exercises the installed distribution —
never the source tree.  The helper itself is stdlib-only: it must run inside
the freshly created smoke virtualenv before anything beyond the wheel and its
runtime dependencies is installed.

Every failure line names the user-visible contract that broke, so release
evidence points at the broken promise instead of a stack trace.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, NoReturn


def ok(contract: str, detail: str) -> None:
    print(f"OK   [{contract}] {detail}")


def fail(contract: str, detail: str) -> NoReturn:
    print(f"FAIL [{contract}] {detail}")
    raise SystemExit(1)


def _load_json(path: Path, contract: str) -> Any:
    if not path.is_file():
        fail(contract, f"missing artifact: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(contract, f"unreadable JSON artifact {path}: {exc}")


def _load_manifest(workspace: Path) -> dict[str, Any]:
    return _load_json(workspace / "generated" / "start_manifest.json", "workspace manifest")


def check_start(args: argparse.Namespace) -> None:
    """Verify the persisted result surfaces of one ``martenweave start`` run."""
    workspace: Path = args.workspace
    manifest = _load_manifest(workspace)
    ok("workspace manifest", "generated/start_manifest.json exists and parses")

    stdout_manifest = _load_json(args.stdout_json, "start command output")
    if stdout_manifest != manifest:
        fail(
            "start command output",
            "--json stdout does not match the persisted generated/start_manifest.json",
        )
    ok("start command output", "--json stdout matches the persisted manifest exactly")

    readiness = manifest.get("readiness") or {}
    verdict = readiness.get("verdict")
    total = readiness.get("total_findings")
    dataset_gaps = readiness.get("dataset_gaps")
    model_gaps = readiness.get("model_gaps")
    if not isinstance(verdict, str) or not verdict:
        fail("manifest readiness summary", f"verdict is missing or empty: {verdict!r}")
    if total != dataset_gaps + model_gaps:
        fail(
            "manifest readiness summary",
            f"total_findings={total} != dataset_gaps={dataset_gaps} + model_gaps={model_gaps}",
        )
    if not isinstance(total, int) or total < 1:
        fail(
            "manifest readiness summary",
            f"the synthetic CSV must produce findings for a meaningful smoke, got {total}",
        )
    ok("manifest readiness summary", f"verdict={verdict}, total_findings={total}")

    outputs = manifest.get("generated_outputs") or {}
    profile_path = workspace / (outputs.get("profile") or "")
    profile = _load_json(profile_path, "dataset profile")
    column_names = {column.get("name") for column in profile.get("columns") or []}
    if not {"customer_id", "customer_group", "sales_org"} <= column_names:
        fail(
            "dataset profile",
            f"profile columns {sorted(column_names)} do not cover the synthetic CSV header",
        )
    ok("dataset profile", f"profile persisted at {outputs['profile']} with all CSV columns")

    report_json_path = workspace / (outputs.get("readiness_json") or "")
    report = _load_json(report_json_path, "readiness report")
    report_total = len(report.get("dataset_gaps") or []) + len(report.get("model_gaps") or [])
    summary_total = (report.get("gap_summary") or {}).get("total_gap_count")
    if report_total != total or summary_total != total:
        fail(
            "readiness report matches manifest",
            f"readiness.json findings={report_total}, gap_summary={summary_total}, "
            f"manifest total_findings={total}",
        )

    markdown_path = workspace / (outputs.get("readiness_markdown") or "")
    if not markdown_path.is_file():
        fail("readiness report matches manifest", f"missing artifact: {markdown_path}")
    markdown = markdown_path.read_text(encoding="utf-8")
    if f"## Verdict: {verdict}" not in markdown:
        fail(
            "readiness report matches manifest",
            f"readiness.md verdict line does not match manifest verdict {verdict!r}",
        )
    if f"- Total gap count: {total}" not in markdown:
        fail(
            "readiness report matches manifest",
            f"readiness.md Gap Summary count does not match manifest total_findings={total}",
        )
    ok(
        "readiness report matches manifest",
        "readiness.json and readiness.md Gap Summary share the manifest verdict and count",
    )

    proposal_ref = outputs.get("draft_proposal")
    if not proposal_ref:
        fail("unapplied draft proposal", "manifest generated_outputs.draft_proposal is null")
    proposal_path = workspace / proposal_ref
    if not proposal_path.is_file():
        fail("unapplied draft proposal", f"missing artifact: {proposal_path}")
    proposal_text = proposal_path.read_text(encoding="utf-8")
    if not re.search(r"^status:\s*pending_review\s*$", proposal_text, re.MULTILINE):
        fail(
            "unapplied draft proposal",
            f"{proposal_ref} is not a pending_review PatchProposal",
        )
    model_dir = workspace / "model"
    applied = [
        path.name
        for pattern in ("ATTR-*.md", "FEP-*.md", "MAP-*.md")
        for path in model_dir.glob(pattern)
    ]
    if applied:
        fail(
            "unapplied draft proposal",
            f"inferred objects were applied without review: {applied}",
        )
    ok("unapplied draft proposal", f"{proposal_ref} is pending review; nothing was applied")

    if not (model_dir / "DOMAIN-EXAMPLE.md").is_file():
        fail(
            "workspace scaffold",
            "start did not scaffold the seeded workspace model (model/DOMAIN-EXAMPLE.md)",
        )
    ok("workspace scaffold", "start scaffolded the seeded workspace model")


def check_template(args: argparse.Namespace) -> None:
    """Verify that a wheel-scaffolded model-spine template validates clean."""
    workspace: Path = args.workspace
    if not (workspace / "modelops.config.yaml").is_file():
        fail("template discovery/validation", f"missing modelops.config.yaml in {workspace}")
    seeded = sorted(path.name for path in (workspace / "model").glob("*.md"))
    if not seeded:
        fail(
            "template discovery/validation",
            "init --template did not copy packaged model-spine objects into model/",
        )
    validation = _load_json(args.validate_json, "template discovery/validation")
    if validation.get("is_valid") is not True:
        fail(
            "template discovery/validation",
            f"martenweave validate reports the template-scaffolded workspace invalid: "
            f"{validation.get('summary_by_code')}",
        )
    ok(
        "template discovery/validation",
        f"wheel-packaged model spine scaffolded {len(seeded)} objects and validates clean",
    )


def check_loader(args: argparse.Namespace) -> None:
    """Verify template discovery and the persisted-result loader from the wheel."""
    import modelops_core

    package_file = Path(modelops_core.__file__).resolve()
    if not str(package_file).startswith(sys.prefix):
        fail(
            "install isolation",
            f"modelops_core resolved from {package_file}, outside the smoke venv {sys.prefix}",
        )
    ok("install isolation", f"modelops_core loaded from the installed wheel: {package_file}")

    from modelops_core.repository.scaffold import available_templates

    templates = available_templates()
    if "sap_bp_customer_migration" not in templates:
        fail(
            "template discovery",
            f"wheel-packaged model spines not discovered, available: {templates}",
        )
    ok("template discovery", f"packaged model spines discovered: {templates}")

    import importlib.resources

    static_index = importlib.resources.files("modelops_core") / "workbench_static" / "index.html"
    if not static_index.is_file():
        fail("packaged workbench assets", "workbench_static/index.html missing from the wheel")
    ok("packaged workbench assets", "workbench UI assets shipped inside the installed wheel")

    from modelops_core.run.start_result import load_start_result

    manifest = _load_manifest(args.workspace)
    result = load_start_result(args.workspace)
    if result is None:
        fail("core start-result loader", "load_start_result returned None for a start workspace")
    readiness = manifest["readiness"]
    if result["verdict"] != readiness["verdict"]:
        fail(
            "core start-result loader",
            f"loader verdict {result['verdict']!r} != manifest {readiness['verdict']!r}",
        )
    if result["total_findings"] != readiness["total_findings"]:
        fail(
            "core start-result loader",
            f"loader total_findings {result['total_findings']} "
            f"!= manifest {readiness['total_findings']}",
        )
    if (result["evidence"] or {}).get("readiness_markdown") != "readiness/readiness.md":
        fail(
            "core start-result loader",
            f"loader evidence does not name the persisted report: {result['evidence']}",
        )
    if (result["provenance"] or {}).get("input_name") != args.input_name:
        fail(
            "core start-result loader",
            f"loader provenance does not name the input file {args.input_name!r}",
        )
    ok("core start-result loader", "load_start_result replays the persisted manifest result")


def _get(url: str, contract: str) -> bytes:
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            if response.status != 200:
                fail(contract, f"GET {url} returned HTTP {response.status}")
            return response.read()
    except (urllib.error.URLError, OSError) as exc:
        fail(contract, f"GET {url} failed: {exc}")


def check_api(args: argparse.Namespace) -> None:
    """Verify the local API/Workbench contract for the start-created workspace."""
    base = args.base_url.rstrip("/")
    repo_query = urllib.parse.quote(str(args.workspace), safe="")
    capabilities_url = f"{base}/api/v1/capabilities?repo={repo_query}"

    deadline = time.monotonic() + args.wait_seconds
    while True:
        try:
            with urllib.request.urlopen(capabilities_url, timeout=2):
                break
        except (urllib.error.URLError, OSError):
            if time.monotonic() >= deadline:
                fail(
                    "workbench server startup",
                    f"workbench did not answer at {base} within {args.wait_seconds}s",
                )
            time.sleep(0.5)
    ok("workbench server startup", f"martenweave workbench serving at {base}")

    html = _get(f"{base}/", "packaged workbench ui")
    if b"<html" not in html.lower():
        fail("packaged workbench ui", "GET / did not return the packaged Workbench HTML")
    ok("packaged workbench ui", "GET / serves the wheel-packaged Workbench")

    capabilities = json.loads(_get(capabilities_url, "capabilities start_result entry"))
    read_names = {entry.get("name") for entry in capabilities.get("read") or []}
    if "start_result" not in read_names:
        fail(
            "capabilities start_result entry",
            f"/api/v1/capabilities read list lacks start_result: {sorted(read_names)}",
        )
    ok("capabilities start_result entry", "capabilities advertises the start_result read")

    result_url = f"{base}/api/v1/start-result?repo={repo_query}"
    result = json.loads(_get(result_url, "start-result api matches manifest"))
    manifest = _load_manifest(args.workspace)
    readiness = manifest["readiness"]
    if result.get("available") is not True:
        fail("start-result api matches manifest", f"available is not true: {result}")
    if result.get("verdict") != readiness["verdict"]:
        fail(
            "start-result api matches manifest",
            f"API verdict {result.get('verdict')!r} != manifest {readiness['verdict']!r}",
        )
    if result.get("total_findings") != readiness["total_findings"]:
        fail(
            "start-result api matches manifest",
            f"API total_findings {result.get('total_findings')} "
            f"!= manifest {readiness['total_findings']}",
        )
    if len(result.get("findings") or []) != readiness["total_findings"]:
        fail(
            "start-result api matches manifest",
            "API findings list length does not equal manifest total_findings",
        )
    if (result.get("evidence") or {}).get("readiness_markdown") != "readiness/readiness.md":
        fail(
            "start-result api matches manifest",
            f"API evidence does not name the persisted report: {result.get('evidence')}",
        )
    if (result.get("provenance") or {}).get("input_name") != args.input_name:
        fail(
            "start-result api matches manifest",
            f"API provenance does not name the input file {args.input_name!r}",
        )
    ok(
        "start-result api matches manifest",
        f"/api/v1/start-result replays verdict={readiness['verdict']}, "
        f"total_findings={readiness['total_findings']}",
    )

    report_body = _get(
        f"{base}/api/v1/reports/readiness/readiness.md?repo={repo_query}",
        "evidence artifact download",
    )
    if b"Gap Summary" not in report_body:
        fail(
            "evidence artifact download",
            "downloaded readiness.md lacks the Gap Summary section",
        )
    ok("evidence artifact download", "evidence artifact IDs resolve through the reports API")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    start_cmd = commands.add_parser("check-start", help="Verify persisted start-run surfaces.")
    start_cmd.add_argument("--workspace", type=Path, required=True)
    start_cmd.add_argument("--stdout-json", type=Path, required=True)
    start_cmd.set_defaults(handler=check_start)

    template_cmd = commands.add_parser(
        "check-template", help="Verify template scaffolding and validation."
    )
    template_cmd.add_argument("--workspace", type=Path, required=True)
    template_cmd.add_argument("--validate-json", type=Path, required=True)
    template_cmd.set_defaults(handler=check_template)

    loader_cmd = commands.add_parser("check-loader", help="Verify wheel loader and templates.")
    loader_cmd.add_argument("--workspace", type=Path, required=True)
    loader_cmd.add_argument("--input-name", required=True)
    loader_cmd.set_defaults(handler=check_loader)

    api_cmd = commands.add_parser("check-api", help="Verify the API/Workbench contract.")
    api_cmd.add_argument("--workspace", type=Path, required=True)
    api_cmd.add_argument("--base-url", required=True)
    api_cmd.add_argument("--input-name", required=True)
    api_cmd.add_argument("--wait-seconds", type=float, default=30.0)
    api_cmd.set_defaults(handler=check_api)

    args = parser.parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
