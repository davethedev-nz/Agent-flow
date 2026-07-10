from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from agentflow import __version__
from agentflow.application.project_inspection import ProjectInspectionService
from agentflow.domain.project import DoctorReport, ProjectInspection
from agentflow.infrastructure.repository_discovery import FilesystemRepositoryDiscovery

app = typer.Typer(help="AgentFlow CLI")
project_app = typer.Typer(help="Project inspection and initialization commands")
config_app = typer.Typer(help="Configuration commands")
task_app = typer.Typer(help="Task management commands")
console = Console()

app.add_typer(project_app, name="project")
app.add_typer(config_app, name="config")
app.add_typer(task_app, name="task")


def _project_inspection_service() -> ProjectInspectionService:
    return ProjectInspectionService(FilesystemRepositoryDiscovery())


def _print_json(payload: object) -> None:
    console.print_json(json.dumps(payload, indent=2))


def _print_project_inspection(inspection: ProjectInspection) -> None:
    table = Table(title="AgentFlow project inspect")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("Requested path", str(inspection.requested_path))
    table.add_row("Git repository", "yes" if inspection.is_git_repository else "no")
    table.add_row("Repository root", str(inspection.repository_root) if inspection.repository_root else "not found")
    table.add_row("AgentFlow initialized", "yes" if inspection.agentflow_initialized else "no")
    table.add_row("Stack hints", ", ".join(inspection.stack_hints) if inspection.stack_hints else "none")
    console.print(table)


def _print_doctor_report(report: DoctorReport) -> None:
    table = Table(title="AgentFlow doctor")
    table.add_column("Check")
    table.add_column("Status")
    table.add_column("Details")

    for check in report.checks:
        table.add_row(check.name, check.status, check.details)

    console.print(table)


@app.callback()
def main() -> None:
    """AgentFlow command group."""


@app.command("version")
def version() -> None:
    """Print the installed AgentFlow version."""
    console.print(f"AgentFlow {__version__}")


@app.command("doctor")
def doctor(
    path: Path = typer.Argument(Path.cwd(), help="Path to inspect."),
    as_json: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Run a minimal environment and repository check."""
    report = _project_inspection_service().doctor(path)

    if as_json:
        _print_json(report.model_dump(mode="json"))
        return

    _print_doctor_report(report)


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
def project_inspect(
    path: Path = typer.Argument(Path.cwd(), help="Path to inspect."),
    as_json: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Inspect the current path and locate the enclosing repository."""
    inspection = _project_inspection_service().inspect(path)

    if as_json:
        _print_json(inspection.model_dump(mode="json"))
        return

    _print_project_inspection(inspection)


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
