from __future__ import annotations

import json
import subprocess
from pathlib import Path

from agentflow.domain.worktrees import WorktreeRecord
from agentflow.infrastructure.repository_discovery import FilesystemRepositoryDiscovery


class GitWorktreeService:
    def __init__(self, discovery: FilesystemRepositoryDiscovery) -> None:
        self._discovery = discovery

    def ensure_task_worktree(self, path: Path, task_id: str) -> WorktreeRecord:
        inspection = self._discovery.inspect(path)
        if inspection.repository_root is None:
            raise ValueError("Current path is not inside a Git repository.")
        repository_root = inspection.repository_root
        task_root = repository_root / ".agentflow" / "tasks" / task_id
        if not task_root.exists():
            raise ValueError(f"Task {task_id} was not found.")

        metadata_path = task_root / "worktree.json"
        if metadata_path.exists():
            record = WorktreeRecord.model_validate(json.loads(metadata_path.read_text(encoding="utf-8")))
            if Path(record.path).exists():
                return record

        branch = f"task/{task_id}"
        worktree_root = repository_root.parent / ".worktrees" / repository_root.name / task_id
        worktree_root.parent.mkdir(parents=True, exist_ok=True)

        self._run(["git", "rev-parse", "HEAD"], repository_root)
        branch_exists = self._run_optional(["git", "show-ref", "--verify", f"refs/heads/{branch}"], repository_root)
        if not branch_exists:
            self._run(["git", "branch", branch], repository_root)

        if not worktree_root.exists():
            self._run(["git", "worktree", "add", str(worktree_root), branch], repository_root)

        head = self._run(["git", "rev-parse", "HEAD"], worktree_root)
        record = WorktreeRecord(task_id=task_id, branch=branch, path=str(worktree_root), head=head)
        metadata_path.write_text(json.dumps(record.model_dump(mode="json"), indent=2) + "\n", encoding="utf-8")
        return record

    def _run(self, argv: list[str], cwd: Path) -> str:
        completed = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            raise ValueError((completed.stderr or completed.stdout).strip() or f"Command failed: {' '.join(argv)}")
        return completed.stdout.strip()

    def _run_optional(self, argv: list[str], cwd: Path) -> bool:
        completed = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, check=False)
        return completed.returncode == 0
