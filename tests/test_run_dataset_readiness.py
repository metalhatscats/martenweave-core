"""Tests for the dataset-readiness workflow command."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from modelops_core.cli import app
from modelops_core.run import generate_dataset_readiness_report, write_readiness_report

runner = CliRunner()


def _write_csv(path: Path, columns: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [",".join(columns)]
    for row in rows:
        lines.append(",".join(row))
    path.write_text("\n".join(lines), encoding="utf-8")


def test_cli_dataset_readiness_happy_path(tmp_path: Path) -> None:
    """A dataset that matches a FieldEndpoint produces a non-blocked verdict."""
    repo = tmp_path / "repo"
    model_dir = repo / "model"
    model_dir.mkdir(parents=True)

    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\nname: Test Domain\n---\n",
        encoding="utf-8",
    )
    (model_dir / "ATTR-TEST.md").write_text(
        "---\n"
        "id: ATTR-TEST\n"
        "type: Attribute\n"
        "status: draft\n"
        "name: Test Attribute\n"
        "domain: DOMAIN-TEST\n"
        "---\n",
        encoding="utf-8",
    )
    (model_dir / "FEP-TEST.md").write_text(
        "---\n"
        "id: FEP-TEST\n"
        "type: FieldEndpoint\n"
        "status: draft\n"
        "name: Test Field\n"
        "domain: DOMAIN-TEST\n"
        "attribute: ATTR-TEST\n"
        "column_name: customer_id\n"
        "---\n",
        encoding="utf-8",
    )

    dataset = tmp_path / "customers.csv"
    _write_csv(dataset, ["customer_id", "extra"], [["1", "x"], ["2", "y"]])

    out_dir = tmp_path / "out"
    result = runner.invoke(
        app,
        [
            "run",
            "dataset-readiness",
            str(dataset),
            "--repo",
            str(repo),
            "--out",
            str(out_dir),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Dataset Readiness" in result.output
    assert out_dir.exists()
    assert (out_dir / "readiness.json").exists()
    assert (out_dir / "readiness.md").exists()

    data = json.loads((out_dir / "readiness.json").read_text(encoding="utf-8"))
    assert data["verdict"] in {"ready", "ready_with_warnings"}
    assert data["validation"]["error_count"] == 0
    assert data["coverage"]["matched_columns"] == 1


def _write_minimal_repo(repo: Path, *, with_endpoint: bool = True) -> None:
    model_dir = repo / "model"
    model_dir.mkdir(parents=True)
    (model_dir / "PERSON-GOV.md").write_text(
        "---\nid: PERSON-GOV\ntype: Person\nstatus: active\nname: Data Governance\n---\n",
        encoding="utf-8",
    )
    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\n"
        "id: DOMAIN-TEST\n"
        "type: MasterDataDomain\n"
        "status: draft\n"
        "name: Test Domain\n"
        "business_owner: PERSON-GOV\n"
        "---\n",
        encoding="utf-8",
    )
    (model_dir / "ATTR-TEST.md").write_text(
        "---\n"
        "id: ATTR-TEST\n"
        "type: Attribute\n"
        "status: draft\n"
        "name: Test Attribute\n"
        "domain: DOMAIN-TEST\n"
        "business_owner: PERSON-GOV\n"
        "---\n",
        encoding="utf-8",
    )
    if with_endpoint:
        (model_dir / "FEP-TEST.md").write_text(
            "---\n"
            "id: FEP-TEST\n"
            "type: FieldEndpoint\n"
            "status: draft\n"
            "name: Test Field\n"
            "domain: DOMAIN-TEST\n"
            "attribute: ATTR-TEST\n"
            "column_name: customer_id\n"
            "business_owner: PERSON-GOV\n"
            "---\n",
            encoding="utf-8",
        )


def _run_readiness(tmp_path: Path, repo: Path, dataset: Path) -> tuple[dict, str]:
    out_dir = tmp_path / "out"
    result = runner.invoke(
        app,
        ["run", "dataset-readiness", str(dataset), "--repo", str(repo), "--out", str(out_dir)],
    )
    assert result.exit_code == 0, result.output
    data = json.loads((out_dir / "readiness.json").read_text(encoding="utf-8"))
    markdown = (out_dir / "readiness.md").read_text(encoding="utf-8")
    return data, markdown


def test_readiness_report_healthy_state_explains_zero_findings(tmp_path: Path) -> None:
    """A healthy report shows an explicit, consistent zero state and explains why."""
    repo = tmp_path / "repo"
    _write_minimal_repo(repo)
    dataset = tmp_path / "customers.csv"
    _write_csv(dataset, ["customer_id"], [["1"], ["2"]])

    data, markdown = _run_readiness(tmp_path, repo, dataset)

    assert data["verdict"] == "ready", data["validation"]
    assert data["dataset_gaps"] == []
    assert data["model_gaps"] == []
    assert data["gap_summary"]["total_gap_count"] == 0
    assert "- Total gap count: 0" in markdown
    assert "No gaps detected." in markdown
    assert "all 1 dataset column(s) matched" in markdown


def test_readiness_report_ready_with_warnings_state_counts_match(tmp_path: Path) -> None:
    """A warnings-state report keeps summary count parity with the persisted findings."""
    repo = tmp_path / "repo"
    _write_minimal_repo(repo)
    dataset = tmp_path / "customers.csv"
    _write_csv(dataset, ["customer_id", "legacy_code"], [["1", "A"], ["2", "B"]])

    data, markdown = _run_readiness(tmp_path, repo, dataset)

    assert data["verdict"] == "ready_with_warnings", data["validation"]
    total = len(data["dataset_gaps"]) + len(data["model_gaps"])
    assert total == 1
    assert data["gap_summary"]["total_gap_count"] == total
    assert data["gap_summary"]["dataset_gap_count"] == len(data["dataset_gaps"])
    assert f"- Total gap count: {total}" in markdown
    assert "**Recommended next action:**" in markdown
    for gap in data["dataset_gaps"]:
        assert gap["finding"]["id"] in markdown


def test_readiness_report_blocked_state_names_concrete_next_action(tmp_path: Path) -> None:
    """A blocked report names a concrete, safe review action tied to a finding ID."""
    repo = tmp_path / "repo"
    _write_minimal_repo(repo)
    dataset = tmp_path / "unrelated.csv"
    _write_csv(dataset, ["totally_unrelated"], [["a"]])

    data, markdown = _run_readiness(tmp_path, repo, dataset)

    assert data["verdict"] == "blocked"
    total = len(data["dataset_gaps"]) + len(data["model_gaps"])
    assert data["gap_summary"]["total_gap_count"] == total
    assert f"- Total gap count: {total}" in markdown
    action_line = next(
        line for line in markdown.splitlines() if line.startswith("**Recommended next action:**")
    )
    assert data["dataset_gaps"][0]["finding"]["id"] in action_line


def test_readiness_report_redacts_high_risk_samples(tmp_path: Path) -> None:
    """High-risk column values never reach the JSON or Markdown report."""
    repo = tmp_path / "repo"
    _write_minimal_repo(repo)
    dataset = tmp_path / "contacts.csv"
    _write_csv(
        dataset,
        ["customer_id", "customer_email"],
        [["1", "ada.lovelace@example.com"]],
    )

    data, markdown = _run_readiness(tmp_path, repo, dataset)
    raw = json.dumps(data) + markdown

    assert "ada.lovelace@example.com" not in raw
    assert "customer_email" in data["dataset_profile"]["privacy_warnings"]


def test_cli_dataset_readiness_accepts_named_dataset_option(tmp_path: Path) -> None:
    """The documented --dataset form is equivalent to the positional argument."""
    repo = tmp_path / "repo"
    model_dir = repo / "model"
    model_dir.mkdir(parents=True)
    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\nname: Test Domain\n---\n",
        encoding="utf-8",
    )
    dataset = tmp_path / "customers.csv"
    _write_csv(dataset, ["customer_id"], [["1"]])

    result = runner.invoke(
        app,
        [
            "run",
            "dataset-readiness",
            "--dataset",
            str(dataset),
            "--repo",
            str(repo),
            "--out",
            str(tmp_path / "out"),
        ],
    )

    assert result.exit_code == 0, result.output


def test_cli_dataset_readiness_blocked_when_no_matches(tmp_path: Path) -> None:
    """A dataset with no matching columns is blocked."""
    repo = tmp_path / "repo"
    model_dir = repo / "model"
    model_dir.mkdir(parents=True)

    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\nname: Test Domain\n---\n",
        encoding="utf-8",
    )
    (model_dir / "FEP-TEST.md").write_text(
        "---\n"
        "id: FEP-TEST\n"
        "type: FieldEndpoint\n"
        "status: draft\n"
        "name: Test Field\n"
        "domain: DOMAIN-TEST\n"
        "column_name: customer_id\n"
        "---\n",
        encoding="utf-8",
    )

    dataset = tmp_path / "unrelated.csv"
    _write_csv(dataset, ["totally_unrelated"], [["a"]])

    out_dir = tmp_path / "out"
    result = runner.invoke(
        app,
        [
            "run",
            "dataset-readiness",
            str(dataset),
            "--repo",
            str(repo),
            "--out",
            str(out_dir),
        ],
    )

    assert result.exit_code == 0, result.output
    data = json.loads((out_dir / "readiness.json").read_text(encoding="utf-8"))
    assert data["verdict"] == "blocked"
    assert data["coverage"]["match_rate"] == 0.0


def test_cli_dataset_readiness_json_output(tmp_path: Path) -> None:
    """The --json flag prints the full report to stdout."""
    repo = tmp_path / "repo"
    model_dir = repo / "model"
    model_dir.mkdir(parents=True)

    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\nname: Test Domain\n---\n",
        encoding="utf-8",
    )

    dataset = tmp_path / "empty.csv"
    _write_csv(dataset, ["col"], [["val"]])

    out_dir = tmp_path / "out"
    result = runner.invoke(
        app,
        [
            "run",
            "dataset-readiness",
            str(dataset),
            "--repo",
            str(repo),
            "--out",
            str(out_dir),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert "verdict" in data
    assert "validation" in data


def test_cli_dataset_readiness_dry_run_does_not_write(tmp_path: Path) -> None:
    """Dry-run must not create report files."""
    repo = tmp_path / "repo"
    model_dir = repo / "model"
    model_dir.mkdir(parents=True)

    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\nname: Test Domain\n---\n",
        encoding="utf-8",
    )

    dataset = tmp_path / "data.csv"
    _write_csv(dataset, ["col"], [["val"]])

    out_dir = tmp_path / "out"
    result = runner.invoke(
        app,
        [
            "run",
            "dataset-readiness",
            str(dataset),
            "--repo",
            str(repo),
            "--out",
            str(out_dir),
            "--dry-run",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Dry-run" in result.output
    assert not out_dir.exists() or not any(out_dir.iterdir())


def test_cli_dataset_readiness_missing_dataset(tmp_path: Path) -> None:
    """A missing dataset file produces a clean error and exit code 1."""
    repo = tmp_path / "repo"
    model_dir = repo / "model"
    model_dir.mkdir(parents=True)

    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\nname: Test Domain\n---\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "run",
            "dataset-readiness",
            str(tmp_path / "missing.csv"),
            "--repo",
            str(repo),
            "--out",
            str(tmp_path / "out"),
        ],
    )

    assert result.exit_code == 1
    assert "Dataset not found" in result.output


def test_cli_dataset_readiness_missing_model(tmp_path: Path) -> None:
    """A missing model directory produces a clean error and exit code 1."""
    dataset = tmp_path / "data.csv"
    _write_csv(dataset, ["col"], [["val"]])

    result = runner.invoke(
        app,
        [
            "run",
            "dataset-readiness",
            str(dataset),
            "--repo",
            str(tmp_path / "no_model"),
            "--out",
            str(tmp_path / "out"),
        ],
    )

    assert result.exit_code == 1
    assert "Model path does not exist" in result.output


def test_service_generate_report_with_check_model(tmp_path: Path) -> None:
    """The service function supports the check_model flag."""
    repo = tmp_path / "repo"
    model_dir = repo / "model"
    model_dir.mkdir(parents=True)

    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\nname: Test Domain\n---\n",
        encoding="utf-8",
    )
    (model_dir / "ATTR-TEST.md").write_text(
        "---\n"
        "id: ATTR-TEST\n"
        "type: Attribute\n"
        "status: draft\n"
        "name: Test Attribute\n"
        "domain: DOMAIN-TEST\n"
        "---\n",
        encoding="utf-8",
    )

    dataset = tmp_path / "data.csv"
    _write_csv(dataset, ["customer_id"], [["1"]])

    report = generate_dataset_readiness_report(
        repo_root=repo,
        dataset_path=dataset,
        check_model=True,
    )

    assert report.verdict in {"ready", "ready_with_warnings", "blocked"}
    assert isinstance(report.model_gaps, list)


def test_write_readiness_report_creates_json_and_md(tmp_path: Path) -> None:
    """write_readiness_report emits both JSON and Markdown files."""
    repo = tmp_path / "repo"
    model_dir = repo / "model"
    model_dir.mkdir(parents=True)
    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\nname: Test Domain\n---\n",
        encoding="utf-8",
    )

    dataset = tmp_path / "data.csv"
    _write_csv(dataset, ["col"], [["val"]])

    report = generate_dataset_readiness_report(repo_root=repo, dataset_path=dataset)
    out_dir = tmp_path / "out"
    json_path, md_path = write_readiness_report(report, out_dir)

    assert json_path.exists()
    assert md_path.exists()
    assert json_path.name == "readiness.json"
    assert md_path.name == "readiness.md"

    loaded = json.loads(json_path.read_text(encoding="utf-8"))
    assert loaded["verdict"] == report.verdict


def test_cli_dataset_readiness_with_sample_repo(sample_repo: Path, tmp_path: Path) -> None:
    """The command runs successfully against the bundled customer example."""
    dataset = sample_repo / "data" / "samples" / "customer_sales_area_sample.csv"
    out_dir = tmp_path / "out"

    result = runner.invoke(
        app,
        [
            "run",
            "dataset-readiness",
            str(dataset),
            "--repo",
            str(sample_repo),
            "--out",
            str(out_dir),
            "--check-model",
        ],
    )

    assert result.exit_code == 0, result.output
    data = json.loads((out_dir / "readiness.json").read_text(encoding="utf-8"))
    assert data["verdict"] in {"ready", "ready_with_warnings", "blocked"}
    assert data["dataset_profile"]["row_count"] > 0


def test_cli_promote_to_proposal_creates_patch_proposal(tmp_path: Path) -> None:
    """--promote-to-proposal writes a draft PatchProposal for dataset gaps."""
    repo = tmp_path / "repo"
    model_dir = repo / "model"
    model_dir.mkdir(parents=True)

    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\nname: Test Domain\n---\n",
        encoding="utf-8",
    )
    (model_dir / "ATTR-TEST.md").write_text(
        "---\n"
        "id: ATTR-TEST\n"
        "type: Attribute\n"
        "status: draft\n"
        "name: Test Attribute\n"
        "domain: DOMAIN-TEST\n"
        "---\n",
        encoding="utf-8",
    )
    (model_dir / "FEP-TEST.md").write_text(
        "---\n"
        "id: FEP-TEST\n"
        "type: FieldEndpoint\n"
        "status: draft\n"
        "name: Test Field\n"
        "domain: DOMAIN-TEST\n"
        "attribute: ATTR-TEST\n"
        "column_name: customer_id\n"
        "---\n",
        encoding="utf-8",
    )

    dataset = tmp_path / "customers.csv"
    _write_csv(dataset, ["customer_id", "legacy_code"], [["1", "A"], ["2", "B"]])

    out_dir = tmp_path / "out"
    result = runner.invoke(
        app,
        [
            "run",
            "dataset-readiness",
            str(dataset),
            "--repo",
            str(repo),
            "--out",
            str(out_dir),
            "--promote-to-proposal",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Promoted to proposal" in result.output

    data = json.loads((out_dir / "readiness.json").read_text(encoding="utf-8"))
    assert data["promoted_proposal_path"] is not None
    assert Path(data["promoted_proposal_path"]).exists()
    assert "PP-GAP-" in data["promoted_proposal_path"]


def test_cli_promote_to_proposal_respects_dry_run(tmp_path: Path) -> None:
    """--promote-to-proposal must not write a proposal when --dry-run is set."""
    repo = tmp_path / "repo"
    model_dir = repo / "model"
    model_dir.mkdir(parents=True)

    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\nname: Test Domain\n---\n",
        encoding="utf-8",
    )

    dataset = tmp_path / "customers.csv"
    _write_csv(dataset, ["legacy_code"], [["A"]])

    out_dir = tmp_path / "out"
    result = runner.invoke(
        app,
        [
            "run",
            "dataset-readiness",
            str(dataset),
            "--repo",
            str(repo),
            "--out",
            str(out_dir),
            "--promote-to-proposal",
            "--dry-run",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["promoted_proposal_path"] is None
    assert not (repo / "model" / "patch-proposals").exists()


def test_service_promote_to_proposal_returns_path(tmp_path: Path) -> None:
    """The service function returns the promoted proposal path when requested."""
    repo = tmp_path / "repo"
    model_dir = repo / "model"
    model_dir.mkdir(parents=True)

    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\nname: Test Domain\n---\n",
        encoding="utf-8",
    )

    dataset = tmp_path / "customers.csv"
    _write_csv(dataset, ["legacy_code"], [["A"]])

    report = generate_dataset_readiness_report(
        repo_root=repo,
        dataset_path=dataset,
        promote_to_proposal=True,
    )

    assert report.promoted_proposal_path is not None
    assert Path(report.promoted_proposal_path).exists()


def test_cli_issue_draft_creates_draft(tmp_path: Path) -> None:
    """--issue-draft writes a GitHub-ready issue draft from the readiness report."""
    repo = tmp_path / "repo"
    model_dir = repo / "model"
    model_dir.mkdir(parents=True)

    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\nname: Test Domain\n---\n",
        encoding="utf-8",
    )

    dataset = tmp_path / "customers.csv"
    _write_csv(dataset, ["legacy_code"], [["A"]])

    out_dir = tmp_path / "out"
    result = runner.invoke(
        app,
        [
            "run",
            "dataset-readiness",
            str(dataset),
            "--repo",
            str(repo),
            "--out",
            str(out_dir),
            "--issue-draft",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Issue draft" in result.output

    data = json.loads((out_dir / "readiness.json").read_text(encoding="utf-8"))
    assert data["issue_draft_path"] is not None
    draft_path = Path(data["issue_draft_path"])
    assert draft_path.exists()
    assert "[Readiness]" in draft_path.read_text(encoding="utf-8")


def test_cli_issue_draft_respects_dry_run(tmp_path: Path) -> None:
    """--issue-draft must not write a draft when --dry-run is set."""
    repo = tmp_path / "repo"
    model_dir = repo / "model"
    model_dir.mkdir(parents=True)

    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\nname: Test Domain\n---\n",
        encoding="utf-8",
    )

    dataset = tmp_path / "customers.csv"
    _write_csv(dataset, ["legacy_code"], [["A"]])

    out_dir = tmp_path / "out"
    result = runner.invoke(
        app,
        [
            "run",
            "dataset-readiness",
            str(dataset),
            "--repo",
            str(repo),
            "--out",
            str(out_dir),
            "--issue-draft",
            "--dry-run",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["issue_draft_path"] is None
    assert not (repo / "generated" / "issues").exists()


def test_service_issue_draft_returns_path(tmp_path: Path) -> None:
    """The service function returns the issue draft path when requested."""
    repo = tmp_path / "repo"
    model_dir = repo / "model"
    model_dir.mkdir(parents=True)

    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\nname: Test Domain\n---\n",
        encoding="utf-8",
    )

    dataset = tmp_path / "customers.csv"
    _write_csv(dataset, ["legacy_code"], [["A"]])

    report = generate_dataset_readiness_report(
        repo_root=repo,
        dataset_path=dataset,
        issue_draft=True,
    )

    assert report.issue_draft_path is not None
    assert Path(report.issue_draft_path).exists()
