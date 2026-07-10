from __future__ import annotations

from pathlib import Path

from agentflow.domain.project import DoctorCheck, DoctorReport, ProjectInspection
from agentflow.infrastructure.repository_discovery import FilesystemRepositoryDiscovery


class ProjectInspectionService:
    def __init__(self, discovery: FilesystemRepositoryDiscovery) -> None:
        self._discovery = discovery

    def inspect(self, path: Path) -> ProjectInspection:
        return self._discovery.inspect(path)

    def doctor(self, path: Path) -> DoctorReport:
        inspection = self.inspect(path)
        checks = [DoctorCheck(name="Python package import", status="ok", details="agentflow package importable")]

        if inspection.is_git_repository and inspection.repository_root is not None:
            checks.append(
                DoctorCheck(
                    name="Repository discovery",
                    status="ok",
                    details=f"Repository root: {inspection.repository_root}",
                )
            )
        else:
            checks.append(
                DoctorCheck(
                    name="Repository discovery",
                    status="warning",
                    details="Current path is not inside a Git repository.",
                )
            )

        if inspection.stack_hints:
            checks.append(
                DoctorCheck(
                    name="Stack detection",
                    status="ok",
                    details=", ".join(inspection.stack_hints),
                )
            )
        else:
            checks.append(
                DoctorCheck(
                    name="Stack detection",
                    status="warning",
                    details="No supported stack hints detected.",
                )
            )

        return DoctorReport(
            requested_path=inspection.requested_path,
            repository_root=inspection.repository_root,
            checks=checks,
        )