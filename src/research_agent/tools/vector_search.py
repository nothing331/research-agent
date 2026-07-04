from __future__ import annotations

from research_agent.domain import ToolResult
from research_agent.tools.base import ToolContext
from research_agent.vector_search.index import InMemoryVectorIndex


class VectorSearchTool:
    name = "vector_search"

    def __init__(self, index: InMemoryVectorIndex, top_k: int) -> None:
        self.index = index
        self.top_k = top_k

    def run(self, context: ToolContext) -> ToolResult:
        try:
            result = self.index.search(context.enhanced_query, top_k=self.top_k)
        except Exception as exc:
            return ToolResult(
                tool_name=self.name,
                summary=f"Vector search could not run: {exc}",
                raw_output={"query": context.enhanced_query, "matches": [], "error": str(exc)},
                citations=[],
            )

        if not result.matches:
            return ToolResult(
                tool_name=self.name,
                summary="Vector search found no indexed document chunks.",
                raw_output={"query": result.query, "matches": []},
                citations=[],
            )

        citations = [
            f"{match.filename}#page={match.page_number}"
            for match in result.matches
        ]
        snippets = [
            f"{match.filename} page {match.page_number} score={match.score:.3f}: {match.text[:180]}"
            for match in result.matches
        ]
        return ToolResult(
            tool_name=self.name,
            summary="Vector search retrieved relevant document chunks.\n" + "\n".join(snippets),
            raw_output={
                "query": result.query,
                "top_k": result.top_k,
                "matches": [
                    {
                        "chunk_id": match.chunk_id,
                        "document_id": match.document_id,
                        "filename": match.filename,
                        "page_number": match.page_number,
                        "score": match.score,
                        "text": match.text,
                    }
                    for match in result.matches
                ],
            },
            citations=citations,
        )
