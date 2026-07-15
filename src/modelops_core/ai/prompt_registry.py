"""Versioned prompt template registry for AI workflows."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class PromptTemplate:
    """A versioned prompt template for a specific AI workflow."""

    prompt_id: str
    version: str
    workflow: str
    system_instructions: str
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    safety_rules: list[str] = field(default_factory=list)
    context_requirements: dict[str, Any] = field(default_factory=dict)
    examples: list[dict[str, Any]] = field(default_factory=list)

    def render_system_prompt(self) -> str:
        """Return the system instructions as a single string."""
        return self.system_instructions.strip()

    def render_user_prompt(self, inputs: dict[str, Any]) -> str:
        """Render a user prompt from structured inputs.

        This is a scaffold implementation. Production usage may use
        Jinja2 or another templating engine.
        """
        lines: list[str] = []
        lines.append(f"Workflow: {self.workflow}")
        lines.append(f"Prompt version: {self.version}")
        lines.append("")
        for key, value in inputs.items():
            lines.append(f"## {key}")
            lines.append(yaml.safe_dump(value, default_flow_style=False, allow_unicode=True))
            lines.append("")
        return "\n".join(lines)

    def to_metadata(self) -> dict[str, Any]:
        """Return metadata for telemetry or proposal tracking."""
        return {
            "prompt_id": self.prompt_id,
            "version": self.version,
            "workflow": self.workflow,
            "context_requirements": self.context_requirements,
        }


class PromptRegistry:
    """Loads and retrieves versioned prompt templates from disk."""

    def __init__(self, prompts_dir: Path | None = None) -> None:
        if prompts_dir is None:
            prompts_dir = Path(__file__).parent / "prompts"
        self._prompts_dir = prompts_dir
        self._templates: dict[str, PromptTemplate] = {}
        self._load_all()

    def _load_all(self) -> None:
        if not self._prompts_dir.exists():
            return
        for path in sorted(self._prompts_dir.glob("*.yaml")):
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            if not data:
                continue
            template = PromptTemplate(
                prompt_id=data.get("prompt_id", path.stem),
                version=data.get("version", "0.0.0"),
                workflow=data.get("workflow", "unknown"),
                system_instructions=data.get("system_instructions", ""),
                input_schema=data.get("input_schema", {}),
                output_schema=data.get("output_schema", {}),
                safety_rules=data.get("safety_rules", []),
                context_requirements=data.get("context_requirements", {}),
                examples=data.get("examples", []),
            )
            key = f"{template.prompt_id}_v{template.version}"
            self._templates[key] = template
            # Also register under prompt_id alone for latest lookup
            self._templates[template.prompt_id] = template

    def get(self, prompt_id: str, version: str | None = None) -> PromptTemplate:
        """Retrieve a prompt template by ID and optional version.

        If version is omitted, returns the latest loaded template for that ID.
        """
        if version:
            key = f"{prompt_id}_v{version}"
            if key not in self._templates:
                raise KeyError(f"Prompt template not found: {key}")
            return self._templates[key]

        if prompt_id not in self._templates:
            raise KeyError(f"Prompt template not found: {prompt_id}")
        return self._templates[prompt_id]

    def list_prompts(self) -> list[dict[str, Any]]:
        """List all registered prompt templates with metadata."""
        seen: set[str] = set()
        results: list[dict[str, Any]] = []
        for key, template in self._templates.items():
            if "_v" in key:
                continue  # skip versioned keys, use bare prompt_id
            if template.prompt_id in seen:
                continue
            seen.add(template.prompt_id)
            results.append(
                {
                    "prompt_id": template.prompt_id,
                    "version": template.version,
                    "workflow": template.workflow,
                    "safety_rules_count": len(template.safety_rules),
                    "examples_count": len(template.examples),
                }
            )
        return results

    def get_for_workflow(self, workflow: str) -> PromptTemplate:
        """Retrieve the latest prompt template for a given workflow type."""
        for template in self._templates.values():
            if template.workflow == workflow:
                return template
        raise KeyError(f"No prompt template found for workflow: {workflow}")

    def render_for_workflow(self, workflow: str, inputs: dict[str, Any]) -> tuple[str, str]:
        """Render system and user prompts for a workflow.

        Returns a tuple of (system_prompt, user_prompt). Raises KeyError if
        no template exists for the workflow.
        """
        template = self.get_for_workflow(workflow)
        return template.render_system_prompt(), template.render_user_prompt(inputs)
