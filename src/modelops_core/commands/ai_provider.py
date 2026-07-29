"""AI provider inspection commands."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import typer
from rich.table import Table

from modelops_core.ai.provider_capabilities import (
    PROVIDER_SLOTS as _PROVIDER_SLOTS,
)
from modelops_core.ai.provider_capabilities import (
    ai_capabilities,
)
from modelops_core.ai.provider_capabilities import (
    provider_health as _provider_health,
)
from modelops_core.commands._common import console

ai_provider_app = typer.Typer(
    help="Inspect and verify configured AI providers.",
    no_args_is_help=False,
)


@ai_provider_app.callback(invoke_without_command=True)
def ai_provider_capabilities(
    ctx: typer.Context,
    repo: Path | None = typer.Option(  # noqa: B008
        None, "--repo", help="Optional local model repository."
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output the stable capability contract."
    ),
) -> None:
    """Show the active provider-neutral contract when no subcommand is selected."""
    if ctx.invoked_subcommand is not None:
        return
    capabilities = ai_capabilities(repo)
    if json_output:
        print(json.dumps(capabilities, indent=2, default=str))
        return
    console.print("[bold]Optional AI capability contract[/bold]")
    console.print(capabilities["no_provider_message"])
    for provider in capabilities["providers"]:
        operations = ", ".join(provider["supported_operations"]) or "No AI operations"
        console.print(
            f"  {provider['label']}: {provider['endpoint_class']} · {operations} · "
            f"configured={provider['configured']}"
        )


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
        configured = True if provider == "no_provider" else all(os.getenv(v) for v in required)
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
