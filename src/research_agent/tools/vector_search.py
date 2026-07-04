from __future__ import annotations

from research_agent.domain import ToolResult
from research_agent.tools.base import ToolContext


class VectorSearchTool:
    name = "vector_search"

    def run(self, context: ToolContext) -> ToolResult:
        return ToolResult(
            tool_name=self.name,
            summary="Vector search is stubbed in v1 until the document corpus is available.",
            raw_output={"matches": [], "query_excerpt": context.enhanced_query[:80]},
            citations=[],
        )
