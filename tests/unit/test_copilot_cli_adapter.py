from agentflow.adapters.copilot_cli import CopilotCLIAdapter


def test_copilot_adapter_injects_default_model_before_prompt() -> None:
    command = ["copilot", "--prompt"]

    prepared = CopilotCLIAdapter._command_with_default_model(command, "gpt-4.1-mini")

    assert prepared == ["copilot", "--model", "gpt-4.1-mini", "--prompt"]


def test_copilot_adapter_preserves_explicit_model() -> None:
    command = ["copilot", "--model", "gpt-5-mini", "--prompt"]

    prepared = CopilotCLIAdapter._command_with_default_model(command, "gpt-4.1-mini")

    assert prepared == command


def test_copilot_adapter_does_not_modify_non_copilot_commands() -> None:
    command = ["python", "-c", "print('ok')"]

    prepared = CopilotCLIAdapter._command_with_default_model(command, "gpt-4.1-mini")

    assert prepared == command
