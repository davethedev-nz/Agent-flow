from __future__ import annotations

import re
from pathlib import Path

import yaml

from agentflow.domain.init import InitApplyResult, InitFileStatus, InitProposal, ProposedPaths
from agentflow.domain.project import ProjectInspection
from agentflow.infrastructure.repository_discovery import FilesystemRepositoryDiscovery


class ProjectInitService:
    def __init__(self, discovery: FilesystemRepositoryDiscovery) -> None:
        self._discovery = discovery

    def preview(self, path: Path, profile: str | None = None) -> InitProposal:
        inspection = self._discovery.inspect(path)
        if not inspection.is_git_repository or inspection.repository_root is None:
            return InitProposal(
                requested_path=inspection.requested_path,
                repository_root=None,
                is_git_repository=False,
                agentflow_initialized=False,
                selected_profile=profile,
                stack_hints=inspection.stack_hints,
                warnings=["Current path is not inside a Git repository."],
                can_write=False,
            )

        selected_profile = profile or self._default_profile(inspection)
        proposed_paths = self._propose_paths(inspection.repository_root, selected_profile)
        validation_commands = self._validation_commands(selected_profile, proposed_paths)
        expected_files = self._expected_files(inspection, selected_profile, proposed_paths, validation_commands)
        file_statuses = self._file_statuses(inspection.repository_root, expected_files)
        conflict_exists = any(item.status == "conflict" for item in file_statuses)

        warnings: list[str] = []
        if conflict_exists:
            warnings.append("Existing AgentFlow files differ from the proposed content and will not be overwritten.")

        return InitProposal(
            requested_path=inspection.requested_path,
            repository_root=inspection.repository_root,
            is_git_repository=True,
            agentflow_initialized=inspection.agentflow_initialized,
            selected_profile=selected_profile,
            stack_hints=inspection.stack_hints,
            project_id=self._project_id(inspection.repository_root),
            proposed_paths=proposed_paths,
            validation_commands=validation_commands,
            files=file_statuses,
            warnings=warnings,
            can_write=not conflict_exists,
        )

    def apply(self, path: Path, profile: str | None = None) -> InitApplyResult:
        proposal = self.preview(path, profile)
        if not proposal.is_git_repository or proposal.repository_root is None or proposal.selected_profile is None:
            raise ValueError("Current path is not inside a Git repository.")

        expected_files = self._expected_files(
            self._discovery.inspect(path),
            proposal.selected_profile,
            proposal.proposed_paths,
            proposal.validation_commands,
        )

        written_files: list[str] = []
        unchanged_files: list[str] = []
        conflict_files: list[str] = []

        for relative_path, content in expected_files.items():
            target_path = proposal.repository_root / relative_path
            if target_path.exists():
                existing_content = target_path.read_text(encoding="utf-8")
                if existing_content == content:
                    unchanged_files.append(relative_path)
                    continue
                conflict_files.append(relative_path)
                continue

            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(content, encoding="utf-8")
            written_files.append(relative_path)

        return InitApplyResult(
            repository_root=proposal.repository_root,
            written_files=written_files,
            unchanged_files=unchanged_files,
            conflict_files=conflict_files,
        )

    def _default_profile(self, inspection: ProjectInspection) -> str:
        if inspection.stack_hints:
            return inspection.stack_hints[0]
        return "generic"

    def _project_id(self, repository_root: Path) -> str:
        normalized = re.sub(r"[^a-z0-9]+", "-", repository_root.name.lower()).strip("-")
        return normalized or "agentflow-project"

    def _propose_paths(self, repository_root: Path, selected_profile: str) -> ProposedPaths:
        source = self._existing_dirs(repository_root, ["src", "app", "project", "lib"])
        tests = self._existing_dirs(repository_root, ["tests", "test"])
        documentation = self._existing_dirs(repository_root, ["docs", "doc"])
        infrastructure = ["."] if any(repository_root.rglob("*.tf")) else []

        forbidden = [".git", ".venv", "dist"]
        if selected_profile == "node-typescript":
            forbidden.append("node_modules")

        return ProposedPaths(
            source=source,
            tests=tests,
            documentation=documentation,
            infrastructure=infrastructure,
            forbidden=forbidden,
        )

    def _existing_dirs(self, repository_root: Path, candidates: list[str]) -> list[str]:
        return [candidate for candidate in candidates if (repository_root / candidate).is_dir()]

    def _validation_commands(self, selected_profile: str, proposed_paths: ProposedPaths) -> list[list[str]]:
        if selected_profile in {"python", "django"}:
            type_target = proposed_paths.source[0] if proposed_paths.source else "."
            return [["ruff", "check", "."], ["mypy", type_target], ["pytest"]]
        if selected_profile == "node-typescript":
            return [["npm", "test"]]
        if selected_profile == "dotnet":
            return [["dotnet", "test"]]
        if selected_profile == "terraform":
            return [["terraform", "fmt", "-check"], ["terraform", "validate"]]
        return []

    def _file_statuses(self, repository_root: Path, expected_files: dict[str, str]) -> list[InitFileStatus]:
        statuses: list[InitFileStatus] = []
        for relative_path, content in expected_files.items():
            target_path = repository_root / relative_path
            if not target_path.exists():
                status = "create"
            elif target_path.read_text(encoding="utf-8") == content:
                status = "unchanged"
            else:
                status = "conflict"
            statuses.append(InitFileStatus(relative_path=relative_path, status=status))
        return statuses

    def _expected_files(
        self,
        inspection: ProjectInspection,
        selected_profile: str,
        proposed_paths: ProposedPaths,
        validation_commands: list[list[str]],
    ) -> dict[str, str]:
        repository_root = inspection.repository_root
        if repository_root is None:
            return {}

        project_id = self._project_id(repository_root)
        config = {
            "schema_version": 1,
            "project": {"id": project_id, "stack_profiles": [selected_profile] if selected_profile != "generic" else []},
            "paths": {
                "source": proposed_paths.source,
                "tests": proposed_paths.tests,
                "documentation": proposed_paths.documentation,
                "infrastructure": proposed_paths.infrastructure,
                "forbidden": proposed_paths.forbidden,
            },
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

        validators = []
        for command in validation_commands:
            validator_id = command[0].replace(".", "_")
            validators.append(
                {
                    "validator_id": validator_id,
                    "description": f"Run {' '.join(command)}",
                    "command": command,
                    "timeout_seconds": 600 if validator_id == "pytest" else 300,
                }
            )

        command_allowlist = sorted({command[0] for command in validation_commands} | {"git", "python", "rg"})
        editable_paths = [*proposed_paths.source, *proposed_paths.tests, *proposed_paths.documentation]

        return {
            ".agentflow/config.yaml": yaml.safe_dump(config, sort_keys=False),
            ".agentflow/project-context.md": (
                "# Project Context\n\n"
                "Describe the repository purpose, major modules, and important domain constraints here.\n"
            ),
            ".agentflow/architecture-rules.md": (
                "# Architecture Rules\n\n"
                "- Keep changes scoped to approved task intent.\n"
                "- Preserve deterministic validation before reviewer analysis.\n"
                "- Keep orchestration logic separate from presentation surfaces.\n"
                "- Prefer the smallest context and prompt needed to complete the current step.\n"
            ),
            ".agentflow/validation.yaml": yaml.safe_dump(
                {"schema_version": 1, "validators": validators},
                sort_keys=False,
            ),
            ".agentflow/policies/commands.yaml": yaml.safe_dump(
                {
                    "schema_version": 1,
                    "allowed_executables": command_allowlist,
                    "blocked_patterns": [
                        "sudo",
                        "su",
                        "git push",
                        "git reset --hard",
                        "git clean -fd",
                        "rm -rf",
                    ],
                },
                sort_keys=False,
            ),
            ".agentflow/policies/paths.yaml": yaml.safe_dump(
                {
                    "schema_version": 1,
                    "editable": {
                        "planner": [],
                        "implementer": editable_paths,
                        "reviewer": [],
                        "tester": proposed_paths.tests,
                        "documenter": proposed_paths.documentation,
                    },
                    "read_only": [".agentflow"],
                    "forbidden": proposed_paths.forbidden,
                },
                sort_keys=False,
            ),
            ".agentflow/prompts/planner.md": (
                "# Planner Prompt Override\n\n"
                "Use the built-in planner prompt and repository-local guidance files.\n"
            ),
            ".agentflow/prompts/implementer.md": (
                "# Implementer Prompt Override\n\n"
                "Use the built-in implementer prompt and respect path and command policy files.\n"
            ),
            ".agentflow/tasks/.gitkeep": "",
        }
