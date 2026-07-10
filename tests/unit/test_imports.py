from agentflow import __version__
from agentflow.cli.main import app


def test_version_is_defined() -> None:
    assert __version__ == "0.1.0"


def test_cli_app_exists() -> None:
    assert app.info.help == "AgentFlow CLI"
