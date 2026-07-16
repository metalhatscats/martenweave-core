from __future__ import annotations

from pathlib import Path

import typer

from modelops_core.commands._common import app, console, _resolve_repo
from modelops_core.config import resolve_model_path


@app.command("serve")
def serve(
    host: str = typer.Option("127.0.0.1", "--host", help="Bind host."),
    port: int = typer.Option(8000, "--port", help="Bind port."),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    mutation_token: str | None = typer.Option(
        None, "--mutation-token", help="Optional token required for API mutations."
    ),
) -> None:
    """Start the local API server."""
    try:
        import uvicorn
    except ImportError as exc:
        console.print(
            "[red]uvicorn is required for the API server. "
            "Install it with: pip install uvicorn[/red]"
        )
        raise typer.Exit(code=1) from exc

    repo_root = _resolve_repo(repo)
    console.print(f"[green]Starting API server at http://{host}:{port}[/green]")
    console.print(f"  Repository: {repo_root}")

    from modelops_core.api.app import app as api_app
    from modelops_core.api.workspace import configure_workspace

    configure_workspace(repo_root, mutation_token=mutation_token)
    uvicorn.run(api_app, host=host, port=port)


@app.command("workbench")
def workbench(
    host: str = typer.Option("127.0.0.1", "--host", help="Bind host."),
    port: int = typer.Option(8000, "--port", help="Bind port."),
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    no_open: bool = typer.Option(False, "--no-open", help="Do not open a browser tab."),
) -> None:
    """Launch the local Martenweave Workbench (API + packaged UI)."""
    try:
        import uvicorn
    except ImportError as exc:
        console.print(
            "[red]uvicorn is required for the workbench. Install it with: pip install uvicorn[/red]"
        )
        raise typer.Exit(code=1) from exc

    import importlib.resources
    import webbrowser
    from threading import Timer

    repo_root = _resolve_repo(repo)
    model_path = resolve_model_path(repo_root)
    if not model_path.exists():
        console.print(f"[red]Repository not found or missing model/ directory: {repo_root}[/red]")
        raise typer.Exit(code=1)

    # Prefer the in-tree frontend/dist during development; fall back to the
    # packaged workbench_static directory shipped inside the wheel.
    static_dir = Path("frontend/dist").resolve()
    if not static_dir.is_dir():
        static_dir = Path(str(importlib.resources.files("modelops_core") / "workbench_static"))

    if not static_dir.is_dir():
        console.print(
            "[red]Workbench static files not found. Build the frontend first:\n"
            "  cd frontend && npm run build[/red]"
        )
        raise typer.Exit(code=1)

    from modelops_core.api.workbench_app import create_workbench_app

    workbench_app = create_workbench_app(repo_root, static_dir)
    url = f"http://{host}:{port}"

    console.print(f"[green]Starting Martenweave Workbench at {url}[/green]")
    console.print(f"  Repository: {repo_root}")
    console.print(f"  Static files: {static_dir}")

    if not no_open:
        Timer(1.0, lambda: webbrowser.open(url)).start()

    try:
        uvicorn.run(workbench_app, host=host, port=port)
    except SystemExit as exc:
        # uvicorn raises SystemExit on startup failure (e.g. port in use).
        raise typer.Exit(code=exc.code) from exc


@app.command("mcp")
def mcp_server_cmd(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    transport: str = typer.Option("stdio", "--transport", help="Transport: stdio or sse."),
) -> None:
    """Start the MCP server for agent integration."""
    try:
        from modelops_core.mcp_server import create_mcp_server
    except ImportError as exc:
        console.print(
            "[red]The MCP server requires the 'mcp' package. Install it with: pip install mcp[/red]"
        )
        raise typer.Exit(code=1) from exc

    repo_root = _resolve_repo(repo)
    console.print(f"[green]Starting MCP server ({transport})[/green]")
    console.print(f"  Repository: {repo_root}")

    mcp = create_mcp_server(repo=str(repo_root))
    if transport == "stdio":
        mcp.run(transport="stdio")
    elif transport == "sse":
        mcp.run(transport="sse")
    else:
        console.print(f"[red]Unknown transport: {transport}. Use 'stdio' or 'sse'.[/red]")
        raise typer.Exit(code=1)
