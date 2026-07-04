from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from research_agent.domain import Evaluation, Report, ResearchRun, Session, SessionMessage, ToolCallRecord
from research_agent.persistence.memory import InMemoryRepository


class FileRepository(InMemoryRepository):
    """Stores conversation and artifacts locally in text files for v1."""

    def __init__(self, base_dir: str) -> None:
        super().__init__()
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def create_session(self, session: Session) -> None:
        super().create_session(session)
        session_dir = self._session_dir(session.id)
        session_dir.mkdir(parents=True, exist_ok=True)
        self._append_text(
            session_dir / "conversation.txt",
            f"Session {session.id} started at {session.created_at.isoformat()}\n\n",
        )

    def append_message(self, message: SessionMessage) -> None:
        super().append_message(message)
        block = (
            f"[{message.created_at.isoformat()}] {message.role.upper()} "
            f"(index={message.message_index})\n{message.content}\n\n"
        )
        self._append_text(self._session_dir(message.session_id) / "conversation.txt", block)

    def create_research_run(self, run: ResearchRun) -> None:
        super().create_research_run(run)
        self._append_artifact(run.session_id, "research_runs.txt", asdict(run))

    def update_research_run(self, run: ResearchRun) -> None:
        super().update_research_run(run)
        self._append_artifact(run.session_id, "research_runs.txt", asdict(run))

    def record_tool_call(self, tool_call: ToolCallRecord) -> None:
        super().record_tool_call(tool_call)
        run = self.runs[str(tool_call.research_run_id)]
        self._append_artifact(run.session_id, "tool_calls.txt", asdict(tool_call))

    def save_report(self, report: Report) -> None:
        super().save_report(report)
        run = self.runs[str(report.research_run_id)]
        self._append_artifact(run.session_id, "reports.txt", asdict(report))

    def save_evaluation(self, evaluation: Evaluation) -> None:
        super().save_evaluation(evaluation)
        run = self.runs[str(evaluation.research_run_id)]
        self._append_artifact(run.session_id, "evaluations.txt", asdict(evaluation))

    def _session_dir(self, session_id) -> Path:
        return self.base_dir / "sessions" / str(session_id)

    def _append_artifact(self, session_id, filename: str, payload: dict) -> None:
        path = self._session_dir(session_id) / filename
        self._append_text(path, f"{json.dumps(payload, default=str)}\n")

    def _append_text(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(content)
