"""Workbench launcher: local API plus packaged frontend static files."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

from modelops_core.api.app import app as api_app
from modelops_core.api.workspace import configure_workspace


class _SPAStaticFiles(StaticFiles):
    """StaticFiles subclass that falls back to ``index.html`` for SPA routes."""

    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except Exception as exc:  # noqa: BLE001
            from starlette.exceptions import HTTPException

            if isinstance(exc, HTTPException) and exc.status_code == 404:
                index_path = self.directory / "index.html"
                if index_path.is_file():
                    return FileResponse(index_path)
            raise


def create_workbench_app(repo_root: Path, static_dir: Path) -> FastAPI:
    """Return a FastAPI app that serves the API and the workbench SPA.

    API routes are mounted first so they take precedence over static files.
    The SPA is served with ``html=True`` so client-side routes fall back to
    ``index.html``.
    """
    if not static_dir.is_dir():
        raise ValueError(f"Workbench static files not found: {static_dir}")

    configure_workspace(repo_root)
    workbench_app = FastAPI(
        title="Martenweave Workbench",
        description="Local workbench for the agentic data model registry.",
        version=api_app.version,
    )

    # Include the existing API routes at the root so the workbench and
    # external clients can keep using the same endpoints.
    workbench_app.include_router(api_app.router)

    # Static SPA files are served last; unmatched paths fall back to index.html.
    workbench_app.mount(
        "/",
        _SPAStaticFiles(directory=static_dir, html=True),
        name="workbench_static",
    )

    return workbench_app
