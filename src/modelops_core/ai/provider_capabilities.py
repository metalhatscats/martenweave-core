"""Provider-neutral local AI configuration and capability reporting."""

from __future__ import annotations

import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from modelops_core.config import load_repo_config

PROVIDER_SLOTS: dict[str, dict[str, Any]] = {
    "no_provider": {
        "label": "No provider",
        "endpoint_class": "none",
        "api_key_env": None,
        "base_url_env": None,
        "model_env": None,
        "default_base_url": None,
        "default_model": None,
        "health_path": None,
    },
    "kimi": {
        "label": "Kimi (OpenAI-compatible)",
        "endpoint_class": "openai_compatible",
        "api_key_env": "MOONSHOT_API_KEY",
        "base_url_env": "MOONSHOT_BASE_URL",
        "model_env": "MOONSHOT_MODEL",
        "default_base_url": "https://api.moonshot.cn/v1",
        "default_model": "kimi-latest",
        "health_path": "/models",
    },
    "openai": {
        "label": "OpenAI-compatible",
        "endpoint_class": "openai_compatible",
        "api_key_env": "OPENAI_API_KEY",
        "base_url_env": "OPENAI_BASE_URL",
        "model_env": "OPENAI_MODEL",
        "default_base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
        "health_path": "/models",
    },
    "ollama": {
        "label": "Ollama",
        "endpoint_class": "local_ollama",
        "api_key_env": None,
        "base_url_env": "OLLAMA_BASE_URL",
        "model_env": "OLLAMA_MODEL",
        "default_base_url": "http://localhost:11434",
        "default_model": "llama3.1",
        "health_path": "/api/tags",
    },
}

SUPPORTED_OPERATIONS = ["draft_patch_proposal"]


def _env_set(env_name: str | None) -> bool:
    return env_name is not None and os.getenv(env_name) not in {None, ""}


def configured_provider_names(repo_root: Path | None = None) -> list[str]:
    """Resolve the declared provider order without sending a network request."""
    raw = os.getenv("MARTENWEAVE_AI_PROVIDER")
    if raw is None and repo_root is not None:
        config = load_repo_config(repo_root)
        if config is not None and config.ai is not None:
            providers = config.ai.get("providers")
            if isinstance(providers, list):
                raw = ",".join(str(provider) for provider in providers if provider)
    names = [name.strip() for name in (raw or "no_provider").split(",") if name.strip()]
    return names or ["no_provider"]


def _health(provider: str) -> dict[str, Any]:
    """Perform an explicit safe health check for one configured provider."""
    config = PROVIDER_SLOTS.get(provider)
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
    request = urllib.request.Request(health_url, method="GET")
    if api_key:
        request.add_header("Authorization", f"Bearer {api_key}")
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            if response.status == 200:
                return {
                    "provider": provider,
                    "configured": True,
                    "reachable": True,
                    "model": model,
                    "error": None,
                }
            error = f"Provider returned HTTP {response.status}"
    except urllib.error.HTTPError as exc:
        error = f"Provider returned HTTP {exc.code}"
    except urllib.error.URLError as exc:
        error = f"Provider request failed: {exc.reason}"
    except TimeoutError:
        error = "Provider health check timed out"
    except Exception as exc:  # pragma: no cover - defensive credential redaction
        raw_error = f"{type(exc).__name__}: {exc}"
        error = raw_error.replace(api_key, "[REDACTED]") if api_key else raw_error
    return {
        "provider": provider,
        "configured": True,
        "reachable": False,
        "model": model,
        "error": error,
    }


def provider_health(provider: str) -> dict[str, Any]:
    """Public health entry point used by CLI and API diagnostics."""
    return _health(provider or "no_provider")


def provider_descriptor(provider: str, *, include_health: bool = False) -> dict[str, Any]:
    """Describe configuration without exposing provider credentials or sending data."""
    config = PROVIDER_SLOTS.get(provider)
    if config is None:
        health = provider_health(provider) if include_health else None
        return {
            "provider": provider,
            "label": provider,
            "configured": False,
            "model_identity": None,
            "endpoint_class": "unknown",
            "supported_operations": [],
            "required_env_vars": [],
            "health": (
                {
                    "state": "invalid",
                    "reachable": health["reachable"],
                    "error": health["error"],
                }
                if health is not None
                else {"state": "invalid"}
            ),
        }
    required = [config["api_key_env"]] if config["api_key_env"] else []
    configured = provider == "no_provider" or all(_env_set(value) for value in required)
    descriptor = {
        "provider": provider,
        "label": config["label"],
        "configured": configured,
        "model_identity": os.getenv(config["model_env"], config["default_model"])
        if config["model_env"]
        else None,
        "endpoint_class": config["endpoint_class"],
        "supported_operations": SUPPORTED_OPERATIONS,
        "required_env_vars": required,
        "health": {"state": "not_checked"},
    }
    if include_health:
        health = provider_health(provider)
        descriptor["health"] = {
            "state": "healthy" if health["reachable"] else "unavailable",
            "reachable": health["reachable"],
            "error": health["error"],
        }
    return descriptor


def ai_capabilities(
    repo_root: Path | None = None, *, include_health: bool = False
) -> dict[str, Any]:
    """Return the stable contract consumed by CLI, local API, and Workbench."""
    active = configured_provider_names(repo_root)
    config = load_repo_config(repo_root) if repo_root is not None else None
    ai_config = config.ai if config is not None and config.ai is not None else {}
    configured_mcp = ai_config.get("mcp_servers", []) if isinstance(ai_config, dict) else []
    external_agents = ai_config.get("external_agents", []) if isinstance(ai_config, dict) else []
    return {
        "mode": "optional_local_assistance",
        "no_provider_message": (
            "No-provider mode keeps profiling, validation, readiness, and controlled review "
            "fully local."
        ),
        "active_providers": active,
        "providers": [
            provider_descriptor(provider, include_health=include_health) for provider in active
        ],
        "supported_providers": list(PROVIDER_SLOTS),
        "configuration_locations": [
            "MARTENWEAVE_AI_PROVIDER",
            "modelops.config.yaml: ai.providers",
            "provider-specific environment variables",
        ],
        "mcp_agent_discovery": {
            "supported": True,
            "configured_servers": [str(server) for server in configured_mcp if server],
            "external_agents": [str(agent) for agent in external_agents if agent],
            "local_command": "martenweave mcp",
        },
        "safety": {
            "raw_dataset_samples_default": "redacted",
            "canonical_mutation": "requires separate human review and approval",
            "automatic_provider_selection": False,
        },
    }
