from __future__ import annotations

from research_agent.domain import ToolResult
from research_agent.tools.base import ToolContext


class CalculatorTool:
    name = "calculator"

    def run(self, context: ToolContext) -> ToolResult:
        return ToolResult(
            tool_name=self.name,
            summary="Calculator tool is available for future numeric sub-tasks.",
            raw_output={"ready": True, "query_excerpt": context.enhanced_query[:80]},
            citations=[],
        )
