"""Tests for the AI prompt registry."""

from __future__ import annotations

from pathlib import Path

import pytest

from modelops_core.ai.prompt_registry import PromptRegistry, PromptTemplate


def test_registry_loads_builtin_prompts() -> None:
    registry = PromptRegistry()
    prompts = registry.list_prompts()
    ids = {p["prompt_id"] for p in prompts}
    assert "file_to_model" in ids
    assert "chat_to_model" in ids
    assert "explain_trace" in ids
    assert "explain_impact" in ids
    assert "suggest_metadata" in ids
    assert "suggest_lov" in ids


def test_get_prompt_by_id() -> None:
    registry = PromptRegistry()
    template = registry.get("file_to_model")
    assert template.prompt_id == "file_to_model"
    assert template.version == "1.0.0"
    assert template.workflow == "file-to-model"
    assert "modeling assistant" in template.system_instructions.lower()


def test_get_prompt_by_id_and_version() -> None:
    registry = PromptRegistry()
    template = registry.get("file_to_model", version="1.0.0")
    assert template.version == "1.0.0"


def test_get_prompt_missing_raises() -> None:
    registry = PromptRegistry()
    with pytest.raises(KeyError):
        registry.get("nonexistent_prompt")


def test_get_for_workflow() -> None:
    registry = PromptRegistry()
    template = registry.get_for_workflow("chat-to-model")
    assert template.prompt_id == "chat_to_model"


def test_get_for_workflow_missing_raises() -> None:
    registry = PromptRegistry()
    with pytest.raises(KeyError):
        registry.get_for_workflow("nonexistent-workflow")


def test_render_system_prompt() -> None:
    registry = PromptRegistry()
    template = registry.get("explain_trace")
    prompt = template.render_system_prompt()
    assert "lineage" in prompt.lower()


def test_render_user_prompt() -> None:
    registry = PromptRegistry()
    template = registry.get("explain_impact")
    user = template.render_user_prompt(
        {"proposal_id": "PROP-1", "affected_objects": [], "high_risk": True}
    )
    assert "PROP-1" in user
    assert "high_risk" in user


def test_to_metadata() -> None:
    registry = PromptRegistry()
    template = registry.get("suggest_metadata")
    meta = template.to_metadata()
    assert meta["prompt_id"] == "suggest_metadata"
    assert meta["version"] == "1.0.0"
    assert meta["workflow"] == "metadata-gap-suggestion"
    assert "context_requirements" in meta


def test_prompt_template_dataclass() -> None:
    template = PromptTemplate(
        prompt_id="test",
        version="0.1.0",
        workflow="test-workflow",
        system_instructions="Test instructions.",
        safety_rules=["Rule 1"],
    )
    assert template.render_system_prompt() == "Test instructions."
    assert template.safety_rules == ["Rule 1"]


def test_registry_from_custom_dir(tmp_path: Path) -> None:
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    (prompts_dir / "custom_v1.yaml").write_text(
        "prompt_id: custom\nversion: \"1.0.0\"\n"
        "workflow: custom-workflow\n"
        "system_instructions: Do something.\n",
        encoding="utf-8",
    )
    registry = PromptRegistry(prompts_dir)
    template = registry.get("custom")
    assert template.workflow == "custom-workflow"
