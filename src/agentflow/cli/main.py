from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from agentflow import __version__

app = typer.Typer(help="AgentFlow CLI")
project_app = typer.Typer(help="Project inspection and initialization commands")
config_app = typer.Typer(help="Configuration commands")
task_app = typer.Typer(help="Task management commands")
console = Console()

app.add_typer(project_app, name="project")
app.add_typer(config_app, name="config")
app.add_typer(task_app, name="task")


@app.callback()
def main() -> None:
    """AgentFlow command group."""


@app.command("version")
def version() -> None:
    """Print the installed AgentFlow version."""
    console.print(f"AgentFlow {__version__}")


@app.command("doctor")
def doctor() -> None:
    """Run a minimal environment check stub."""
    table = Table(title="AgentFlow doctor")
    table.add_column("Check")
    table.add_column("Status")
    table.add_row("Python package import", "ok")
    table.add_row("Repository discovery", "not implemented")
    table.add_row("Provider adapters", "not implemented")
    console.print(table)


@app.command("init")
def init() -> None:
    """Show an initialization stub."""
    console.print(
        {
            "status": "stub",
            "message": "Repository discovery and safe initialization land in slices 1 and 2.",
        }
    )


@project_app.command("inspect")
def project_inspect(path: Path = Path.cwd()) -> None:
    """Print a small project inspection stub."""
    console.print(
        {
            "path": str(path.resolve()),
            "status": "stub",
            "message": "Project discovery will be implemented in slice 1 and slice 2.",
        }
    )


@config_app.command("show")
def config_show(resolved: bool = False) -> None:
    """Print a configuration display stub."""
    console.print(
        {
            "status": "stub",
            "resolved": resolved,
            "message": "Configuration resolution is planned for slice 3.",
        }
    )


@task_app.command("create")
def task_create(task_id: str) -> None:
    """Print a task creation stub."""
    console.print(
        {
            "task_id": task_id,
            "status": "stub",
            "message": "Task persistence is planned for slice 4.",
        }
    )


if __name__ == "__main__":
    app()
