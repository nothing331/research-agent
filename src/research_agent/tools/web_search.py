from __future__ import annotations

from research_agent.domain import ToolResult
from research_agent.tools.base import ToolContext


class WebSearchTool:
    name = "web_search"

    def run(self, context: ToolContext) -> ToolResult:
        return ToolResult(
            tool_name=self.name,
            summary=(
                "Web search is currently a stub. Replace this with a real search adapter "
                "and store source metadata for each result."
            ),
            raw_output={"results": [], "query_excerpt": context.enhanced_query[:80]},
            citations=[],
        )
