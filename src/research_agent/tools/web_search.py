from __future__ import annotations

from research_agent.domain import ToolResult
from research_agent.tools.base import ToolContext
from research_agent.web_search.cache import WebSearchCache
from research_agent.web_search.client import WebSearchClient, WebSearchError


class WebSearchTool:
    name = "web_search"

    def __init__(
        self,
        client: WebSearchClient,
        cache: WebSearchCache,
        max_results: int = 5,
    ) -> None:
        self.client = client
        self.cache = cache
        self.max_results = max_results

    def run(self, context: ToolContext) -> ToolResult:
        query = context.original_query or context.enhanced_query

        cached = self.cache.get(query)
        if cached is not None:
            return self._build_result(cached, from_cache=True)

        try:
            response = self.client.search(query, max_results=self.max_results)
        except WebSearchError as exc:
            return ToolResult(
                tool_name=self.name,
                summary=f"Web search failed: {exc}",
                raw_output={"query": query, "results": [], "error": str(exc)},
                citations=[],
            )

        if not response.results:
            return ToolResult(
                tool_name=self.name,
                summary="Web search returned no results.",
                raw_output={"query": query, "results": []},
                citations=[],
            )

        self.cache.save(query, response)
        return self._build_result(response, from_cache=False)

    def _build_result(self, response, from_cache: bool) -> ToolResult:
        citations = [r.url for r in response.results]
        cache_note = " (cached)" if from_cache else ""
        snippets = [
            f"{r.title} — {r.url}\n  {r.snippet}"
            for r in response.results
        ]
        return ToolResult(
            tool_name=self.name,
            summary=f"Web search results{cache_note}:\n" + "\n".join(snippets),
            raw_output={
                "query": response.query,
                "results": [
                    {"title": r.title, "url": r.url, "snippet": r.snippet}
                    for r in response.results
                ],
                "cached": from_cache,
            },
            citations=citations,
        )
