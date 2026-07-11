from __future__ import annotations

import subprocess
from pathlib import Path


class GitChangedFileService:
    def list_changed_files(self, repository_root: Path) -> list[Path]:
        completed = subprocess.run(
            ["git", "status", "--porcelain=1", "--untracked-files=all"],
            cwd=repository_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            message = (completed.stderr or completed.stdout).strip() or "Unable to inspect Git changes."
            if "not a git repository" in message.lower():
                return []
            raise ValueError(message)

        changed_files: list[Path] = []
        for line in completed.stdout.splitlines():
            if not line.strip():
                continue
            relative_path = line[3:]
            if " -> " in relative_path:
                relative_path = relative_path.split(" -> ", 1)[1]
            changed_files.append(Path(relative_path))

        return changed_files