"""AI provider inspection commands."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

import typer
from rich.table import Table

from modelops_core.commands._common import console

ai_provider_app = typer.Typer(
    help="Inspect and verify configured AI providers.",
    no_args_is_help=True,
)

_PROVIDER_SLOTS: dict[str, dict[str, Any]] = {
    "no_provider": {
        "api_key_env": None,
        "base_url_env": None,
        "model_env": None,
        "default_base_url": None,
        "default_model": None,
        "health_path": None,
    },
    "kimi": {
        "api_key_env": "MOONSHOT_API_KEY",
        "base_url_env": "MOONSHOT_BASE_URL",
        "model_env": "MOONSHOT_MODEL",
        "default_base_url": "https://api.moonshot.cn/v1",
        "default_model": "kimi-latest",
        "health_path": "/models",
    },
    "openai": {
        "api_key_env": "OPENAI_API_KEY",
        "base_url_env": "OPENAI_BASE_URL",
        "model_env": "OPENAI_MODEL",
        "default_base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
        "health_path": "/models",
    },
    "ollama": {
        "api_key_env": None,
        "base_url_env": "OLLAMA_BASE_URL",
        "model_env": "OLLAMA_MODEL",
        "default_base_url": "http://localhost:11434",
        "default_model": "llama3.1",
        "health_path": "/api/tags",
    },
}


def _env_set(env_name: str | None) -> bool:
    return env_name is not None and os.getenv(env_name) not in {None, ""}


def _provider_health(provider: str) -> dict[str, Any]:
    """Return a health status dict for the named provider slot."""
    if not provider:
        provider = "no_provider"
    config = _PROVIDER_SLOTS.get(provider)
    if config is None:
        return {
            "provider": provider,
            "configured": False,
            "reachable": False,
            "model": None,
            "error": f"Unknown provider: {provider}",
        }

    api_key_env = config["api_key_env"]
    if api_key_env is not None and not _env_set(api_key_env):
        return {
            "provider": provider,
            "configured": False,
            "reachable": False,
            "model": None,
            "error": f"{api_key_env} not set",
        }

    if provider == "no_provider":
        return {
            "provider": provider,
            "configured": True,
            "reachable": True,
            "model": None,
            "error": None,
        }

    base_url = os.getenv(config["base_url_env"], config["default_base_url"])
    model = os.getenv(config["model_env"], config["default_model"])
    health_url = f"{base_url}{config['health_path']}"

    api_key = os.getenv(api_key_env, "") if api_key_env is not None else ""
    req = urllib.request.Request(health_url, method="GET")
    if api_key:
        req.add_header("Authorization", f"Bearer {api_key}")

    error_msg: str | None = None
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                return {
                    "provider": provider,
                    "configured": True,
                    "reachable": True,
                    "model": model,
                    "error": None,
                }
            error_msg = f"Provider returned HTTP {resp.status}"
    except urllib.error.HTTPError as exc:
        error_msg = f"Provider returned HTTP {exc.code}"
    except urllib.error.URLError as exc:
        error_msg = f"Provider request failed: {exc.reason}"
    except TimeoutError:
        error_msg = "Provider health check timed out"
    except Exception as exc:
        # Redact API key from any unexpected error text before returning it.
        raw_msg = f"{type(exc).__name__}: {exc}"
        error_msg = raw_msg.replace(api_key, "[REDACTED]") if api_key else raw_msg

    return {
        "provider": provider,
        "configured": True,
        "reachable": False,
        "model": model,
        "error": error_msg,
    }


@ai_provider_app.command("list")
def ai_provider_list(
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """List available AI provider slots and their required environment variables."""
    rows: list[dict[str, Any]] = []
    for provider, config in _PROVIDER_SLOTS.items():
        required: list[str] = []
        if config["api_key_env"]:
            required.append(config["api_key_env"])
        # Base URL and model are optional for all providers because defaults exist.
        configured = True if provider == "no_provider" else all(_env_set(v) for v in required)
        rows.append(
            {
                "provider": provider,
                "required_env_vars": required,
                "configured": configured,
            }
        )

    if json_output:
        print(json.dumps(rows, indent=2, default=str))
        raise typer.Exit()

    table = Table("Provider", "Required Env Vars", "Configured")
    for row in rows:
        vars_text = ", ".join(row["required_env_vars"]) if row["required_env_vars"] else "—"
        table.add_row(row["provider"], vars_text, "Yes" if row["configured"] else "No")
    console.print(table)


@ai_provider_app.command("health")
def ai_provider_health(
    provider: str | None = typer.Option(
        None,
        "--provider",
        help="Provider slot to check (defaults to MARTENWEAVE_AI_PROVIDER env var).",
    ),
    json_output: bool = typer.Option(False, "--json", help="Output stable JSON."),
) -> None:
    """Check the health of a configured AI provider."""
    provider_name = provider or os.getenv("MARTENWEAVE_AI_PROVIDER", "no_provider")
    status = _provider_health(provider_name)

    if json_output:
        print(json.dumps(status, indent=2, default=str))
        raise typer.Exit()

    table = Table("Field", "Value")
    table.add_row("Provider", status["provider"])
    table.add_row("Configured", "Yes" if status["configured"] else "No")
    table.add_row("Reachable", "Yes" if status["reachable"] else "No")
    table.add_row("Model", status["model"] or "—")
    table.add_row("Error", status["error"] or "—")
    console.print(table)
