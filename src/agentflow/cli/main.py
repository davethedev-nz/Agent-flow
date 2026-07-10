from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from agentflow import __version__
from agentflow.application.project_init import ProjectInitService
from agentflow.application.project_inspection import ProjectInspectionService
from agentflow.domain.init import InitApplyResult, InitProposal
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


def _project_init_service() -> ProjectInitService:
    return ProjectInitService(FilesystemRepositoryDiscovery())


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


def _print_init_preview(proposal: InitProposal) -> None:
    table = Table(title="AgentFlow init preview")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("Requested path", str(proposal.requested_path))
    table.add_row("Repository root", str(proposal.repository_root) if proposal.repository_root else "not found")
    table.add_row("Profile", proposal.selected_profile or "none")
    table.add_row("Stack hints", ", ".join(proposal.stack_hints) if proposal.stack_hints else "none")
    table.add_row("Can write", "yes" if proposal.can_write else "no")
    table.add_row("Source paths", ", ".join(proposal.proposed_paths.source) or "none")
    table.add_row("Test paths", ", ".join(proposal.proposed_paths.tests) or "none")
    table.add_row("Docs paths", ", ".join(proposal.proposed_paths.documentation) or "none")
    table.add_row("Infra paths", ", ".join(proposal.proposed_paths.infrastructure) or "none")
    console.print(table)

    files_table = Table(title="Planned files")
    files_table.add_column("Path")
    files_table.add_column("Status")
    for file_status in proposal.files:
        files_table.add_row(file_status.relative_path, file_status.status)
    console.print(files_table)

    for warning in proposal.warnings:
        console.print(f"warning: {warning}")


def _print_init_apply_result(result: InitApplyResult) -> None:
    table = Table(title="AgentFlow init result")
    table.add_column("Category")
    table.add_column("Files")
    table.add_row("Written", ", ".join(result.written_files) or "none")
    table.add_row("Unchanged", ", ".join(result.unchanged_files) or "none")
    table.add_row("Conflicts", ", ".join(result.conflict_files) or "none")
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
def init(
    path: Path = typer.Argument(Path.cwd(), help="Path to initialize."),
    profile: str | None = typer.Option(None, "--profile", help="Override the detected project profile."),
    write: bool = typer.Option(False, "--write", help="Write the proposed files to disk."),
    as_json: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Preview or write a safe AgentFlow project initialization."""
    service = _project_init_service()

    if write:
        try:
            result = service.apply(path, profile)
        except ValueError as error:
            payload = {"status": "error", "message": str(error)}
            if as_json:
                _print_json(payload)
            else:
                console.print(payload)
            raise typer.Exit(1) from error

        if as_json:
            _print_json(result.model_dump(mode="json"))
        else:
            _print_init_apply_result(result)

        if result.conflict_files:
            raise typer.Exit(1)
        return

    proposal = service.preview(path, profile)
    if as_json:
        _print_json(proposal.model_dump(mode="json"))
    else:
        _print_init_preview(proposal)

    if not proposal.is_git_repository:
        raise typer.Exit(1)


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
