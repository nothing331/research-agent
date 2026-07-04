from __future__ import annotations

from research_agent.domain import Evaluation, Report, ResearchRun, Session, SessionMessage, ToolCallRecord


class InMemoryRepository:
    """Executable stand-in for a future Postgres adapter."""

    def __init__(self) -> None:
        self.sessions: dict[str, Session] = {}
        self.messages: dict[str, SessionMessage] = {}
        self.runs: dict[str, ResearchRun] = {}
        self.tool_calls: dict[str, ToolCallRecord] = {}
        self.reports: dict[str, Report] = {}
        self.evaluations: dict[str, Evaluation] = {}

    def create_session(self, session: Session) -> None:
        self.sessions[str(session.id)] = session

    def append_message(self, message: SessionMessage) -> None:
        self.messages[str(message.id)] = message

    def list_messages(self, session_id) -> list[SessionMessage]:
        return sorted(
            [message for message in self.messages.values() if message.session_id == session_id],
            key=lambda item: item.message_index,
        )

    def create_research_run(self, run: ResearchRun) -> None:
        self.runs[str(run.id)] = run

    def update_research_run(self, run: ResearchRun) -> None:
        self.runs[str(run.id)] = run

    def record_tool_call(self, tool_call: ToolCallRecord) -> None:
        self.tool_calls[str(tool_call.id)] = tool_call

    def save_report(self, report: Report) -> None:
        self.reports[str(report.id)] = report

    def save_evaluation(self, evaluation: Evaluation) -> None:
        self.evaluations[str(evaluation.id)] = evaluation
