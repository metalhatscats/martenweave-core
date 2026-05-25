"""Connector adapters for external integrations."""

from __future__ import annotations

from modelops_core.connectors.adapter import (
    ConnectorAdapter,
    ConnectorError,
    ConnectorSourceInfo,
)
from modelops_core.connectors.google_sheets import GoogleSheetsConnector
from modelops_core.connectors.local_file import LocalFileConnector

__all__ = [
    "ConnectorAdapter",
    "ConnectorError",
    "ConnectorSourceInfo",
    "LocalFileConnector",
    "GoogleSheetsConnector",
]
