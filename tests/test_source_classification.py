"""Tests for source-state classification across the product."""

from __future__ import annotations

from pathlib import Path

from modelops_core.schemas.common import SourceState


def test_source_state_values() -> None:
    assert SourceState.EVIDENCE == "evidence"
    assert SourceState.FINDING == "finding"
    assert SourceState.PROPOSAL == "proposal"
    assert SourceState.CANONICAL == "canonical"
