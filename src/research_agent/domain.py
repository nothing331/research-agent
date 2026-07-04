from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SessionStatus(StrEnum):
    ACTIVE = "active"
    CLOSED = "closed"


class RunStatus(StrEnum):
    CREATED = "created"
    ENHANCED = "enhanced"
    RUNNING_TOOLS = "running_tools"
    REPORT_GENERATED = "report_generated"
    EVALUATED = "evaluated"
    COMPLETED = "completed"
    FAILED = "failed"


class ToolCallStatus(StrEnum):
    STARTED = "started"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass(slots=True)
class Session:
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    status: SessionStatus = SessionStatus.ACTIVE


@dataclass(slots=True)
class SessionMessage:
    session_id: UUID
    role: str
    content: str
    message_index: int
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utc_now)


@dataclass(slots=True)
class ResearchRun:
    session_id: UUID
    user_message_id: UUID
    query: str
    enhanced_query: str = ""
    status: RunStatus = RunStatus.CREATED
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    completed_at: datetime | None = None


@dataclass(slots=True)
class ToolCallRecord:
    research_run_id: UUID
    tool_name: str
    input_payload: dict[str, Any]
    status: ToolCallStatus = ToolCallStatus.STARTED
    output_payload: dict[str, Any] | None = None
    error_message: str | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utc_now)
    completed_at: datetime | None = None


@dataclass(slots=True)
class ToolResult:
    tool_name: str
    summary: str
    raw_output: dict[str, Any]
    citations: list[str]


@dataclass(slots=True)
class Report:
    research_run_id: UUID
    version: int
    content: str
    citations: list[str]
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utc_now)


@dataclass(slots=True)
class Evaluation:
    research_run_id: UUID
    report_id: UUID
    score: int
    feedback: list[str]
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utc_now)
