from __future__ import annotations

from pathlib import Path

from agentflow.adapters.subprocess_text import SubprocessTextAgentAdapter


DEFAULT_COPILOT_CLI_MODEL = "claude-haiku-4.5"


class CopilotCLIAdapter(SubprocessTextAgentAdapter):
    provider_name = "copilot-cli"

    def __init__(self, command: list[str], model: str = DEFAULT_COPILOT_CLI_MODEL) -> None:
        super().__init__(self._command_with_default_model(command, model))

    @staticmethod
    def _command_with_default_model(command: list[str], model: str) -> list[str]:
        if not command:
            return command

        executable_name = Path(command[0]).name
        if executable_name != "copilot":
            return command

        if "--model" in command or any(token.startswith("--model=") for token in command):
            return command

        if "--prompt" in command:
            prompt_index = command.index("--prompt")
            return [*command[:prompt_index], "--model", model, *command[prompt_index:]]

        return [*command, "--model", model]