"""Tests for CLI commands."""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from modelops_core.cli import app

runner = CliRunner()

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_cli_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "martenweave-core" in result.output


def test_cli_init(tmp_path: Path) -> None:
    result = runner.invoke(app, ["init", str(tmp_path / "new-repo")])
    assert result.exit_code == 0
    assert (tmp_path / "new-repo" / "modelops.config.yaml").exists()


def test_cli_validate(sample_repo: Path) -> None:
    result = runner.invoke(app, ["validate", "--repo", str(sample_repo)])
    assert result.exit_code == 0
    assert "Validation Results" in result.output


def test_cli_validate_json_output(sample_repo: Path) -> None:
    result = runner.invoke(app, ["validate", "--repo", str(sample_repo), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "is_valid" in data
    assert "error_count" in data
    assert "warning_count" in data
    assert "info_count" in data
    assert "results" in data
    assert isinstance(data["results"], list)


def test_cli_build_index(sample_repo: Path) -> None:
    result = runner.invoke(app, ["build-index", "--repo", str(sample_repo), "--jsonl"])
    assert result.exit_code == 0
    assert "Index built" in result.output


def test_cli_health(sample_repo: Path) -> None:
    # Need index first
    runner.invoke(app, ["build-index", "--repo", str(sample_repo)])
    result = runner.invoke(app, ["health", "--repo", str(sample_repo)])
    assert result.exit_code == 0
    assert "Repository Health" in result.output


def test_cli_impact(sample_repo: Path) -> None:
    runner.invoke(app, ["build-index", "--repo", str(sample_repo)])
    result = runner.invoke(app, ["impact", "FEP-S4-KNVV-KDGRP", "--repo", str(sample_repo)])
    assert result.exit_code == 0
    assert "Impact Report" in result.output


def test_cli_impact_markdown_format(sample_repo: Path) -> None:
    runner.invoke(app, ["build-index", "--repo", str(sample_repo)])
    result = runner.invoke(
        app, ["impact", "FEP-S4-KNVV-KDGRP", "--repo", str(sample_repo), "--format", "markdown"]
    )
    assert result.exit_code == 0
    assert "# Impact Report: FEP-S4-KNVV-KDGRP" in result.output
    assert "| Object ID | Type | Name | Direction | Depth |" in result.output


def test_cli_impact_markdown_output_file(sample_repo: Path, tmp_path: Path) -> None:
    runner.invoke(app, ["build-index", "--repo", str(sample_repo)])
    output_path = tmp_path / "impact.md"
    result = runner.invoke(
        app,
        [
            "impact",
            "FEP-S4-KNVV-KDGRP",
            "--repo",
            str(sample_repo),
            "--format",
            "markdown",
            "--output",
            str(output_path),
        ],
    )
    assert result.exit_code == 0
    assert output_path.exists()
    content = output_path.read_text(encoding="utf-8")
    assert "# Impact Report: FEP-S4-KNVV-KDGRP" in content


def test_cli_impact_json_format(sample_repo: Path) -> None:
    runner.invoke(app, ["build-index", "--repo", str(sample_repo)])
    result = runner.invoke(
        app, ["impact", "FEP-S4-KNVV-KDGRP", "--repo", str(sample_repo), "--format", "json"]
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["root_object_id"] == "FEP-S4-KNVV-KDGRP"


def test_cli_impact_table_output_requires_format(sample_repo: Path, tmp_path: Path) -> None:
    runner.invoke(app, ["build-index", "--repo", str(sample_repo)])
    output_path = tmp_path / "impact.txt"
    result = runner.invoke(
        app,
        [
            "impact",
            "FEP-S4-KNVV-KDGRP",
            "--repo",
            str(sample_repo),
            "--output",
            str(output_path),
        ],
    )
    assert result.exit_code == 1
    assert "--output requires --format markdown or --format json" in result.output


def test_cli_profile_dataset_csv(sample_repo: Path) -> None:
    csv_file = FIXTURES_DIR / "customer_sample.csv"
    result = runner.invoke(app, ["profile-dataset", str(csv_file), "--repo", str(sample_repo)])
    assert result.exit_code == 0
    assert "Profile saved" in result.output
    assert "Rows: 5" in result.output
    assert "Columns: 3" in result.output

    profile_path = sample_repo / "generated" / "dataset_profiles" / "customer_sample.json"
    assert profile_path.exists()


def test_cli_profile_dataset_xlsx(sample_repo: Path) -> None:
    xlsx_file = FIXTURES_DIR / "customer_sample.xlsx"
    result = runner.invoke(app, ["profile-dataset", str(xlsx_file), "--repo", str(sample_repo)])
    assert result.exit_code == 0
    assert "Profile saved" in result.output
    assert "Sheets: 1" in result.output

    profile_path = sample_repo / "generated" / "dataset_profiles" / "customer_sample.json"
    assert profile_path.exists()


def test_cli_profile_dataset_json_output(sample_repo: Path) -> None:
    csv_file = FIXTURES_DIR / "customer_sample.csv"
    result = runner.invoke(
        app, ["profile-dataset", str(csv_file), "--repo", str(sample_repo), "--json"]
    )
    assert result.exit_code == 0
    assert '"dataset_id"' in result.output
    assert '"row_count"' in result.output


def test_cli_profile_dataset_privacy_warning(sample_repo: Path, tmp_path: Path) -> None:
    csv_file = tmp_path / "sensitive.csv"
    csv_file.write_text(
        "email,phone,customer_group\nalice@example.com,555-1234,A\n",
        encoding="utf-8",
    )
    result = runner.invoke(app, ["profile-dataset", str(csv_file), "--repo", str(sample_repo)])
    assert result.exit_code == 0
    assert "Privacy warning" in result.output
    assert "email" in result.output
    assert "phone" in result.output

    # Verify saved profile has redacted samples
    profile_path = sample_repo / "generated" / "dataset_profiles" / "sensitive.json"
    assert profile_path.exists()
    data = json.loads(profile_path.read_text(encoding="utf-8"))
    for col in data["columns"]:
        if col["name"] in ("email", "phone"):
            assert all(v == "[REDACTED]" for v in col["sample_values"])


def test_cli_profile_dataset_include_raw_samples(sample_repo: Path, tmp_path: Path) -> None:
    csv_file = tmp_path / "sensitive.csv"
    csv_file.write_text("email,customer_group\nalice@example.com,A\n", encoding="utf-8")
    result = runner.invoke(
        app,
        [
            "profile-dataset",
            str(csv_file),
            "--repo",
            str(sample_repo),
            "--include-raw-samples",
        ],
    )
    assert result.exit_code == 0
    profile_path = sample_repo / "generated" / "dataset_profiles" / "sensitive.json"
    data = json.loads(profile_path.read_text(encoding="utf-8"))
    email_col = next(c for c in data["columns"] if c["name"] == "email")
    # Even with --include-raw-samples, high-risk columns are redacted
    assert all(v == "[REDACTED]" for v in email_col["sample_values"])


def test_cli_infer_model(sample_repo: Path) -> None:
    # First profile a dataset
    csv_file = FIXTURES_DIR / "customer_sample.csv"
    runner.invoke(app, ["profile-dataset", str(csv_file), "--repo", str(sample_repo)])

    # Then infer model from the profile
    profile_path = sample_repo / "generated" / "dataset_profiles" / "customer_sample.json"
    result = runner.invoke(app, ["infer-model", str(profile_path), "--repo", str(sample_repo)])
    assert result.exit_code == 0
    assert "PatchProposal written" in result.output
    assert "PP-INFER-CUSTOMER-SAMPLE" in result.output

    proposal_path = sample_repo / "model" / "patch-proposals" / "PP-INFER-CUSTOMER-SAMPLE.md"
    assert proposal_path.exists()


def test_cli_profile_dataset_updates_index_by_name_match(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    model_dir = repo_root / "model"
    model_dir.mkdir(parents=True, exist_ok=True)
    generated_dir = repo_root / "generated"
    generated_dir.mkdir(parents=True, exist_ok=True)

    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\nname: Test\n---\n",
        encoding="utf-8",
    )
    (model_dir / "DS-TEST.md").write_text(
        "---\nid: DS-TEST\ntype: Dataset\nstatus: active\nname: customer_sample.csv\n---\n",
        encoding="utf-8",
    )

    runner.invoke(app, ["build-index", "--repo", str(repo_root)])
    csv_file = FIXTURES_DIR / "customer_sample.csv"
    result = runner.invoke(app, ["profile-dataset", str(csv_file), "--repo", str(repo_root)])
    assert result.exit_code == 0

    health_result = runner.invoke(app, ["health", "--repo", str(repo_root)])
    assert health_result.exit_code == 0
    assert "Datasets with profile:" in health_result.output
    assert "1/1" in health_result.output


def test_cli_profile_dataset_updates_index_with_explicit_id(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    model_dir = repo_root / "model"
    model_dir.mkdir(parents=True, exist_ok=True)
    generated_dir = repo_root / "generated"
    generated_dir.mkdir(parents=True, exist_ok=True)

    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\nname: Test\n---\n",
        encoding="utf-8",
    )
    (model_dir / "DS-TEST.md").write_text(
        "---\nid: DS-TEST\ntype: Dataset\nstatus: active\nname: Other Dataset\n---\n",
        encoding="utf-8",
    )

    runner.invoke(app, ["build-index", "--repo", str(repo_root)])
    csv_file = FIXTURES_DIR / "customer_sample.csv"
    result = runner.invoke(
        app,
        [
            "profile-dataset",
            str(csv_file),
            "--repo",
            str(repo_root),
            "--dataset-id",
            "DS-TEST",
        ],
    )
    assert result.exit_code == 0

    health_result = runner.invoke(app, ["health", "--repo", str(repo_root)])
    assert health_result.exit_code == 0
    assert "Datasets with profile:" in health_result.output
    assert "1/1" in health_result.output


def test_cli_profile_dataset_warns_when_no_dataset_match(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    model_dir = repo_root / "model"
    model_dir.mkdir(parents=True, exist_ok=True)
    generated_dir = repo_root / "generated"
    generated_dir.mkdir(parents=True, exist_ok=True)

    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\nname: Test\n---\n",
        encoding="utf-8",
    )

    runner.invoke(app, ["build-index", "--repo", str(repo_root)])
    csv_file = FIXTURES_DIR / "customer_sample.csv"
    result = runner.invoke(app, ["profile-dataset", str(csv_file), "--repo", str(repo_root)])
    assert result.exit_code == 0
    assert "No matching Dataset object found" in result.output


# Global option tests ---------------------------------------------------------


def test_cli_quiet_validate_no_output_on_success(sample_repo: Path) -> None:
    result = runner.invoke(app, ["--quiet", "validate", "--repo", str(sample_repo)])
    assert result.exit_code == 0
    assert result.output == ""


def test_cli_quiet_validate_shows_errors(sample_repo: Path) -> None:
    # Create an invalid object to trigger an error
    bad_file = sample_repo / "model" / "BAD-ID.md"
    bad_file.write_text(
        "---\nid: bad-id-lower\ntype: Attribute\nstatus: draft\n---\n",
        encoding="utf-8",
    )
    result = runner.invoke(app, ["--quiet", "validate", "--repo", str(sample_repo)])
    assert result.exit_code == 1
    assert "bad-id-lower" in result.output


def test_cli_no_color_health_no_ansi_codes(sample_repo: Path) -> None:
    runner.invoke(app, ["build-index", "--repo", str(sample_repo)])
    result = runner.invoke(app, ["--no-color", "health", "--repo", str(sample_repo)])
    assert result.exit_code == 0
    assert "\033[" not in result.output


def test_cli_json_output_unaffected_by_quiet(sample_repo: Path) -> None:
    result = runner.invoke(app, ["--quiet", "validate", "--repo", str(sample_repo), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["is_valid"] is True


def test_cli_quiet_and_no_color_together(sample_repo: Path) -> None:
    runner.invoke(app, ["build-index", "--repo", str(sample_repo)])
    result = runner.invoke(app, ["--quiet", "--no-color", "health", "--repo", str(sample_repo)])
    assert result.exit_code == 0
    assert result.output == ""
    assert "\033[" not in result.output


def test_cli_validate_strict_exits_2_on_warnings(sample_repo: Path) -> None:
    """--strict should exit 2 when warnings exist but no errors."""
    result = runner.invoke(app, ["validate", "--repo", str(sample_repo), "--strict"])
    assert result.exit_code == 2
    assert "Validation Results" in result.output


def test_cli_validate_strict_exits_0_on_clean(tmp_path: Path) -> None:
    """--strict should exit 0 when no warnings and no errors."""
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\n"
        "id: DOMAIN-TEST\n"
        "type: MasterDataDomain\n"
        "status: active\n"
        "name: Test Domain\n"
        'schema_version: "1.0"\n'
        "---\n",
        encoding="utf-8",
    )
    result = runner.invoke(app, ["validate", "--repo", str(tmp_path), "--strict"])
    assert result.exit_code == 0


def test_cli_validate_strict_exits_1_on_errors(sample_repo: Path) -> None:
    """--strict should exit 1 when errors exist regardless of strict mode."""
    bad_file = sample_repo / "model" / "BAD-ID.md"
    bad_file.write_text(
        "---\nid: bad-id-lower\ntype: Attribute\nstatus: draft\n---\n",
        encoding="utf-8",
    )
    result = runner.invoke(app, ["validate", "--repo", str(sample_repo), "--strict"])
    assert result.exit_code == 1
    assert "bad-id-lower" in result.output


def test_cli_validate_strict_json_output(sample_repo: Path) -> None:
    """--strict with --json should still output JSON and exit 2 on warnings."""
    result = runner.invoke(app, ["validate", "--repo", str(sample_repo), "--strict", "--json"])
    assert result.exit_code == 2
    data = json.loads(result.output)
    assert data["is_valid"] is True
    assert data["warning_count"] > 0


# ---------------------------------------------------------------------------
# doctor
# ---------------------------------------------------------------------------


def test_cli_doctor_human_output(sample_repo: Path) -> None:
    result = runner.invoke(app, ["doctor", "--repo", str(sample_repo)])
    assert result.exit_code == 0
    assert "Doctor Report" in result.output
    assert "Package version" in result.output
    assert "Config present" in result.output
    assert "Model path exists" in result.output
    assert "Index exists" in result.output


def test_cli_doctor_json_output(sample_repo: Path) -> None:
    result = runner.invoke(app, ["doctor", "--repo", str(sample_repo), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "martenweave_version" in data
    assert "repo_root" in data
    assert "config_present" in data
    assert "model_path_exists" in data
    assert "generated_path_exists" in data
    assert "index_exists" in data
    assert "index_fresh" in data
    assert "validation" in data
    assert data["validation"]["ran"] is True
    assert "is_valid" in data["validation"]
    assert "error_count" in data["validation"]
    assert "warning_count" in data["validation"]


def test_cli_doctor_missing_model_path(tmp_path: Path) -> None:
    result = runner.invoke(app, ["doctor", "--repo", str(tmp_path)])
    assert result.exit_code == 0
    assert "Model path exists:   False" in result.output
    assert "Validation skipped" in result.output


def test_cli_doctor_json_missing_model_path(tmp_path: Path) -> None:
    result = runner.invoke(app, ["doctor", "--repo", str(tmp_path), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["model_path_exists"] is False
    assert data["validation"]["ran"] is False


def test_cli_doctor_json_reports_host_tools(sample_repo: Path) -> None:
    result = runner.invoke(app, ["doctor", "--repo", str(sample_repo), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "host_tools" in data
    for tool in ("jq", "node", "npm"):
        assert tool in data["host_tools"]
        entry = data["host_tools"][tool]
        assert "available" in entry
        assert "purpose" in entry
        if entry["available"]:
            assert entry["path"]
        else:
            assert entry["path"] is None


def test_cli_doctor_human_reports_host_tools(sample_repo: Path) -> None:
    result = runner.invoke(app, ["doctor", "--repo", str(sample_repo)])
    assert result.exit_code == 0
    assert "Host tools" in result.output
    for tool in ("jq", "node", "npm"):
        assert tool in result.output


def test_host_tools_marks_missing_tools() -> None:
    from modelops_core.commands.health_reports import _host_tools

    tools = _host_tools(which=lambda name: None)
    for entry in tools.values():
        assert entry["available"] is False
        assert entry["path"] is None
        assert entry["purpose"]


# ---------------------------------------------------------------------------
# ai-provider
# ---------------------------------------------------------------------------


def test_ai_provider_list() -> None:
    result = runner.invoke(app, ["ai-provider", "list"])
    assert result.exit_code == 0
    assert "no_provider" in result.output
    assert "kimi" in result.output
    assert "openai" in result.output
    assert "ollama" in result.output


def test_ai_provider_list_json() -> None:
    result = runner.invoke(app, ["ai-provider", "list", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    providers = {row["provider"] for row in data}
    assert providers == {"no_provider", "kimi", "openai", "ollama"}

    by_provider = {row["provider"]: row for row in data}
    assert by_provider["kimi"]["required_env_vars"] == ["MOONSHOT_API_KEY"]
    assert by_provider["openai"]["required_env_vars"] == ["OPENAI_API_KEY"]
    assert by_provider["ollama"]["required_env_vars"] == []
    assert by_provider["no_provider"]["required_env_vars"] == []


def test_ai_provider_health_no_provider() -> None:
    result = runner.invoke(app, ["ai-provider", "health", "--provider", "no_provider", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["provider"] == "no_provider"
    assert data["configured"] is True
    assert data["reachable"] is True
    assert data["model"] is None
    assert data["error"] is None


def test_ai_provider_health_default_env(monkeypatch) -> None:
    monkeypatch.setenv("MARTENWEAVE_AI_PROVIDER", "no_provider")
    result = runner.invoke(app, ["ai-provider", "health", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["provider"] == "no_provider"
    assert data["configured"] is True
    assert data["reachable"] is True


def test_ai_provider_health_empty_env(monkeypatch) -> None:
    monkeypatch.setenv("MARTENWEAVE_AI_PROVIDER", "")
    result = runner.invoke(app, ["ai-provider", "health", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["provider"] == "no_provider"
    assert data["configured"] is True
    assert data["reachable"] is True


def test_ai_provider_health_missing_key(monkeypatch) -> None:
    monkeypatch.delenv("MOONSHOT_API_KEY", raising=False)
    result = runner.invoke(app, ["ai-provider", "health", "--provider", "kimi", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["provider"] == "kimi"
    assert data["configured"] is False
    assert data["reachable"] is False
    assert data["error"] == "MOONSHOT_API_KEY not set"


def test_ai_provider_health_reachable(monkeypatch) -> None:
    monkeypatch.setenv("MOONSHOT_API_KEY", "test-key")

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)

    def mock_urlopen(req, **_kwargs):
        return mock_resp

    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)

    result = runner.invoke(app, ["ai-provider", "health", "--provider", "kimi", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["provider"] == "kimi"
    assert data["configured"] is True
    assert data["reachable"] is True
    assert data["model"] == "kimi-latest"
    assert data["error"] is None


def test_ai_provider_health_unreachable(monkeypatch) -> None:
    monkeypatch.setenv("MOONSHOT_API_KEY", "test-key")

    def mock_urlopen(_req, **_kwargs):
        raise urllib.error.URLError("Connection refused")

    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)

    result = runner.invoke(app, ["ai-provider", "health", "--provider", "kimi", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["provider"] == "kimi"
    assert data["configured"] is True
    assert data["reachable"] is False
    assert "test-key" not in json.dumps(data)


def test_ai_provider_health_ollama_no_key(monkeypatch) -> None:
    monkeypatch.delenv("OLLAMA_API_KEY", raising=False)

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)

    captured_requests: list[urllib.request.Request] = []

    def mock_urlopen(req, **_kwargs):
        captured_requests.append(req)
        return mock_resp

    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)

    result = runner.invoke(app, ["ai-provider", "health", "--provider", "ollama", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["provider"] == "ollama"
    assert data["configured"] is True
    assert data["reachable"] is True
    assert captured_requests
    assert "Authorization" not in str(captured_requests[0].headers)


def test_ai_provider_list_configured_with_key_only(monkeypatch) -> None:
    monkeypatch.delenv("MOONSHOT_BASE_URL", raising=False)
    monkeypatch.delenv("MOONSHOT_MODEL", raising=False)
    monkeypatch.setenv("MOONSHOT_API_KEY", "test-key")
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    result = runner.invoke(app, ["ai-provider", "list", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    by_provider = {row["provider"]: row for row in data}
    assert by_provider["kimi"]["configured"] is True
    assert by_provider["openai"]["configured"] is False
    assert by_provider["ollama"]["configured"] is True
    assert by_provider["no_provider"]["configured"] is True


def test_ai_provider_health_non_200_status(monkeypatch) -> None:
    monkeypatch.setenv("MOONSHOT_API_KEY", "test-key")

    mock_resp = MagicMock()
    mock_resp.status = 503
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)

    def mock_urlopen(req, **_kwargs):
        return mock_resp

    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)

    result = runner.invoke(app, ["ai-provider", "health", "--provider", "kimi", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["provider"] == "kimi"
    assert data["configured"] is True
    assert data["reachable"] is False
    assert data["error"] == "Provider returned HTTP 503"


def test_ai_provider_health_http_error(monkeypatch) -> None:
    monkeypatch.setenv("MOONSHOT_API_KEY", "test-key")

    http_error = urllib.error.HTTPError(
        url="https://api.moonshot.cn/v1/models",
        code=401,
        msg="Unauthorized",
        hdrs={},
        fp=None,
    )

    def mock_urlopen(req, **_kwargs):
        raise http_error

    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)

    result = runner.invoke(app, ["ai-provider", "health", "--provider", "kimi", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["reachable"] is False
    assert data["error"] == "Provider returned HTTP 401"


def test_ai_provider_health_url_error(monkeypatch) -> None:
    monkeypatch.setenv("MOONSHOT_API_KEY", "test-key")

    def mock_urlopen(req, **_kwargs):
        raise urllib.error.URLError("Connection refused")

    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)

    result = runner.invoke(app, ["ai-provider", "health", "--provider", "kimi", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["reachable"] is False
    assert "Connection refused" in data["error"]


def test_ai_provider_health_timeout(monkeypatch) -> None:
    monkeypatch.setenv("MOONSHOT_API_KEY", "test-key")

    def mock_urlopen(req, **_kwargs):
        raise TimeoutError("Request timed out")

    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)

    result = runner.invoke(app, ["ai-provider", "health", "--provider", "kimi", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["reachable"] is False
    assert data["error"] == "Provider health check timed out"


def test_ai_provider_health_unexpected_error_redacts_secret(monkeypatch) -> None:
    monkeypatch.setenv("MOONSHOT_API_KEY", "super-secret-key")

    def mock_urlopen(req, **_kwargs):
        raise RuntimeError("leaked header: Bearer super-secret-key")

    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)

    result = runner.invoke(app, ["ai-provider", "health", "--provider", "kimi", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["reachable"] is False
    assert "super-secret-key" not in json.dumps(data)
    assert "[REDACTED]" in data["error"]


def test_cli_agent_loop_json_output(sample_repo: Path, monkeypatch) -> None:
    from modelops_core.ai.agent_loop import AgentLoopResult

    expected = AgentLoopResult(
        goal="Add a new attribute.",
        iterations=1,
        final_status="valid_proposal",
        proposal_id="PP-AGENT-TEST-001",
        proposal_path=str(sample_repo / "model" / "patch-proposals" / "PP-AGENT-TEST-001.md"),
        validation_status="valid",
        impact={"high_risk": False, "requires_approval": False, "affected_objects_count": 0},
        assumptions=["Assumption 1"],
        human_checks=["Check 1"],
        log=[],
    )
    monkeypatch.setattr(
        "modelops_core.commands.standalone.run_agent_loop",
        lambda **_: expected,
    )

    result = runner.invoke(
        app,
        [
            "agent-loop",
            "--goal",
            "Add a new attribute.",
            "--repo",
            str(sample_repo),
            "--json",
        ],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["goal"] == "Add a new attribute."
    assert data["iterations"] == 1
    assert data["final_status"] == "valid_proposal"
    assert data["proposal_id"] == "PP-AGENT-TEST-001"
    assert data["validation_status"] == "valid"
    assert "impact" in data
    assert "log" in data


def test_cli_agent_loop_human_output(sample_repo: Path, monkeypatch) -> None:
    from modelops_core.ai.agent_loop import AgentLoopResult

    expected = AgentLoopResult(
        goal="Add a new attribute.",
        iterations=2,
        final_status="valid_proposal",
        proposal_id="PP-AGENT-TEST-002",
        proposal_path=str(sample_repo / "model" / "patch-proposals" / "PP-AGENT-TEST-002.md"),
        validation_status="valid",
        impact={"high_risk": False, "requires_approval": False, "affected_objects_count": 1},
        assumptions=["Assumption 1"],
        human_checks=["Check 1"],
        log=[],
    )
    monkeypatch.setattr(
        "modelops_core.commands.standalone.run_agent_loop",
        lambda **_: expected,
    )

    result = runner.invoke(
        app,
        [
            "agent-loop",
            "--goal",
            "Add a new attribute.",
            "--repo",
            str(sample_repo),
        ],
    )
    assert result.exit_code == 0
    assert "Status: valid_proposal" in result.output
    assert "Iterations: 2" in result.output
    assert "Proposal:   PP-AGENT-TEST-002" in result.output


@pytest.mark.parametrize("final_status", ["invalid_proposal", "no_progress", "failed"])
def test_cli_agent_loop_json_exit_code_on_failure(
    sample_repo: Path, monkeypatch, final_status: str
) -> None:
    from modelops_core.ai.agent_loop import AgentLoopResult

    expected = AgentLoopResult(
        goal="Add a new attribute.",
        iterations=1,
        final_status=final_status,
        proposal_id=None,
        proposal_path=None,
        validation_status="invalid",
        impact={},
        assumptions=[],
        human_checks=["Check 1"],
        log=[],
    )
    monkeypatch.setattr(
        "modelops_core.commands.standalone.run_agent_loop",
        lambda **_: expected,
    )

    result = runner.invoke(
        app,
        [
            "agent-loop",
            "--goal",
            "Add a new attribute.",
            "--repo",
            str(sample_repo),
            "--json",
        ],
    )
    assert result.exit_code == 1
    data = json.loads(result.output)
    assert data["final_status"] == final_status


@patch("modelops_core.ai.patch_proposal_service.build_patch_proposal_from_note")
def test_cli_propose_patch_provider_error_json(
    mock_build: MagicMock,
    tmp_path: Path,
) -> None:
    """propose-patch --json should return stable JSON when the provider fails."""
    from modelops_core.ai.provider_adapter import AIProviderError

    repo = tmp_path / "repo"
    repo.mkdir()
    note = repo / "note.md"
    note.write_text("Update Customer Group.", encoding="utf-8")
    mock_build.side_effect = AIProviderError("provider is unavailable")

    result = runner.invoke(
        app,
        ["propose-patch", "--from", str(note), "--repo", str(repo), "--json"],
    )
    assert result.exit_code == 1
    data = json.loads(result.output)
    assert data["is_safe"] is False
    assert data["proposal"] is None
    assert data["validation"] == []
    assert "error" in data
    assert "provider is unavailable" in data["error"]


@patch("modelops_core.ai.patch_proposal_service.build_patch_proposal_from_note")
def test_cli_propose_patch_value_error_human(
    mock_build: MagicMock,
    tmp_path: Path,
) -> None:
    """propose-patch without --json should print a clear error and exit non-zero."""
    repo = tmp_path / "repo"
    repo.mkdir()
    note = repo / "note.md"
    note.write_text("Update Customer Group.", encoding="utf-8")
    mock_build.side_effect = ValueError("Unknown AI provider 'unknown_provider'.")

    result = runner.invoke(
        app,
        ["propose-patch", "--from", str(note), "--repo", str(repo)],
    )
    assert result.exit_code == 1
    assert "Patch proposal failed" in result.output
    assert "unknown_provider" in result.output
