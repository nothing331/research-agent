from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from research_agent.domain import ToolResult


@dataclass(slots=True)
class ToolContext:
    enhanced_query: str
    original_query: str = ""


class ResearchTool(Protocol):
    name: str

    def run(self, context: ToolContext) -> ToolResult: ...
