from __future__ import annotations

from pathlib import Path
from uuid import UUID

from research_agent.domain import utc_now


class ExecutionLogger:
    def __init__(self, logs_dir: str) -> None:
        self.base_dir = Path(logs_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.global_log_path = self.base_dir / "execution_log.txt"

    def log(self, session_id: UUID, run_id: UUID | None, step: str, detail: str) -> None:
        timestamp = utc_now().isoformat()
        line = (
            f"[{timestamp}] session={session_id} "
            f"run={run_id or 'none'} step={step} detail={detail}\n"
        )
        self._append(self.global_log_path, line)
        session_log = self.base_dir / f"session_{session_id}.txt"
        self._append(session_log, line)

    def _append(self, path: Path, text: str) -> None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(text)
