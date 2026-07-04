from __future__ import annotations

from research_agent.domain import Evaluation, Report, ResearchRun, Session, SessionMessage, ToolCallRecord


class PostgresRepository:
    """
    Placeholder adapter for the future real Postgres implementation.

    The boundary exists now so the orchestrator and domain model do not need
    to change once a driver such as psycopg is introduced.
    """

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def create_session(self, session: Session) -> None:
        raise NotImplementedError("Wire this to psycopg or SQLAlchemy in the next step.")

    def append_message(self, message: SessionMessage) -> None:
        raise NotImplementedError("Wire this to psycopg or SQLAlchemy in the next step.")

    def list_messages(self, session_id) -> list[SessionMessage]:
        raise NotImplementedError("Wire this to psycopg or SQLAlchemy in the next step.")

    def create_research_run(self, run: ResearchRun) -> None:
        raise NotImplementedError("Wire this to psycopg or SQLAlchemy in the next step.")

    def update_research_run(self, run: ResearchRun) -> None:
        raise NotImplementedError("Wire this to psycopg or SQLAlchemy in the next step.")

    def record_tool_call(self, tool_call: ToolCallRecord) -> None:
        raise NotImplementedError("Wire this to psycopg or SQLAlchemy in the next step.")

    def save_report(self, report: Report) -> None:
        raise NotImplementedError("Wire this to psycopg or SQLAlchemy in the next step.")

    def save_evaluation(self, evaluation: Evaluation) -> None:
        raise NotImplementedError("Wire this to psycopg or SQLAlchemy in the next step.")
