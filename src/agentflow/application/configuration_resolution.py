from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from agentflow.configuration.models import ResolvedConfig, ResolvedSetting
from agentflow.infrastructure.repository_discovery import FilesystemRepositoryDiscovery


class ConfigurationResolutionService:
    def __init__(self, discovery: FilesystemRepositoryDiscovery) -> None:
        self._discovery = discovery

    def show_project(self, path: Path) -> dict[str, Any]:
        repository_root = self._repository_root(path)
        project_config_path = repository_root / ".agentflow" / "config.yaml"
        if not project_config_path.exists():
            return {}
        return self._load_yaml(project_config_path)

    def resolve(self, path: Path, task_id: str | None = None) -> ResolvedConfig:
        repository_root = self._repository_root(path)
        layers = [
            ("built-in", self._built_in_defaults()),
        ]

        user_config_path = self._user_config_path()
        if user_config_path.exists():
            layers.append((f"user:{user_config_path}", self._load_yaml(user_config_path)))

        project_config_path = repository_root / ".agentflow" / "config.yaml"
        if project_config_path.exists():
            layers.append((f"project:{project_config_path.relative_to(repository_root)}", self._load_yaml(project_config_path)))

        if task_id is not None:
            task_override_path = repository_root / ".agentflow" / "tasks" / task_id / "task.yaml"
            if task_override_path.exists():
                task_data = self._load_yaml(task_override_path)
                task_overrides = task_data.get("overrides", {})
                if task_overrides and not isinstance(task_overrides, dict):
                    raise ValueError(f"Task override file {task_override_path} must contain a mapping under overrides.")
                if task_overrides:
                    layers.append(
                        (
                            f"task:.agentflow/tasks/{task_id}/task.yaml",
                            task_overrides,
                        )
                    )

        resolved_values: dict[str, Any] = {}
        resolved_origins: dict[str, str] = {}

        for origin, layer in layers:
            self._merge_layer(layer, origin, (), resolved_values, resolved_origins)

        settings = {
            key: ResolvedSetting(value=value, origin=resolved_origins[key])
            for key, value in self._flatten_values(resolved_values).items()
        }
        return ResolvedConfig(settings=settings)

    def _repository_root(self, path: Path) -> Path:
        inspection = self._discovery.inspect(path)
        if inspection.repository_root is None:
            raise ValueError("Current path is not inside a Git repository.")
        return inspection.repository_root

    def _user_config_path(self) -> Path:
        override = os.environ.get("AGENTFLOW_USER_CONFIG")
        if override:
            return Path(override).expanduser()
        xdg_home = os.environ.get("XDG_CONFIG_HOME")
        if xdg_home:
            return Path(xdg_home).expanduser() / "agentflow" / "config.yaml"
        return Path.home() / ".config" / "agentflow" / "config.yaml"

    def _built_in_defaults(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "autonomy": {
                "plan_requires_approval": True,
                "code_edits_require_approval": False,
                "scope_expansion_requires_approval": True,
                "command_approval_mode": "allowlist",
                "maximum_repair_iterations": 4,
                "commit_requires_approval": True,
                "push_allowed": False,
            },
            "efficiency": {
                "prefer_minimal_context": True,
                "max_context_files": 12,
                "max_context_file_bytes": 80000,
                "max_prompt_chars": 24000,
                "require_diff_scoped_repair_context": True,
                "summarize_large_logs": True,
            },
        }

    def _load_yaml(self, path: Path) -> dict[str, Any]:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
        if loaded is None:
            return {}
        if not isinstance(loaded, dict):
            raise ValueError(f"Configuration file {path} must contain a mapping.")
        return loaded

    def _merge_layer(
        self,
        incoming: dict[str, Any],
        origin: str,
        prefix: tuple[str, ...],
        resolved_values: dict[str, Any],
        resolved_origins: dict[str, str],
    ) -> None:
        for key, value in incoming.items():
            dotted = prefix + (key,)
            dotted_key = ".".join(dotted)
            if isinstance(value, dict):
                self._merge_nested(value, origin, dotted, resolved_values, resolved_origins)
                continue
            self._set_nested_value(resolved_values, dotted, value)
            resolved_origins[dotted_key] = origin

    def _merge_nested(
        self,
        incoming: dict[str, Any],
        origin: str,
        prefix: tuple[str, ...],
        resolved_values: dict[str, Any],
        resolved_origins: dict[str, str],
    ) -> None:
        for key, value in incoming.items():
            dotted = prefix + (key,)
            dotted_key = ".".join(dotted)
            if isinstance(value, dict):
                self._merge_nested(value, origin, dotted, resolved_values, resolved_origins)
                continue
            self._set_nested_value(resolved_values, dotted, value)
            resolved_origins[dotted_key] = origin

    def _set_nested_value(self, target: dict[str, Any], path: tuple[str, ...], value: Any) -> None:
        current = target
        for part in path[:-1]:
            next_value = current.get(part)
            if not isinstance(next_value, dict):
                next_value = {}
                current[part] = next_value
            current = next_value
        current[path[-1]] = value

    def _flatten_values(self, values: dict[str, Any], prefix: tuple[str, ...] = ()) -> dict[str, Any]:
        flattened: dict[str, Any] = {}
        for key, value in values.items():
            dotted = prefix + (key,)
            if isinstance(value, dict):
                flattened.update(self._flatten_values(value, dotted))
            else:
                flattened[".".join(dotted)] = value
        return flattened
