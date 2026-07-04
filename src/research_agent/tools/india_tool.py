
from __future__ import annotations

from research_agent.domain import ToolResult
from research_agent.tools.base import ToolContext


class IndiaTool:
    name = "india"

    def run(self, context: ToolContext) -> ToolResult:
        return ToolResult(
            tool_name=self.name,
            summary=(
                "India tool is available for India-related sub-tasks. "
                "It currently returns a placeholder result until real retrieval logic is added."
            ),
            raw_output={"ready": True, "query_excerpt": context.enhanced_query[:80]},
            citations=[],
        )
