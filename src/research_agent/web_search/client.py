from __future__ import annotations

from ddgs import DDGS

from research_agent.web_search.types import WebSearchResponse, WebSearchResult


class WebSearchError(Exception):
    pass


class WebSearchClient:
    def search(self, query: str, max_results: int = 5) -> WebSearchResponse:
        try:
            ddgs = DDGS()
            raw_results = list(ddgs.text(query, max_results=max_results))
        except Exception as exc:
            raise WebSearchError(f"DuckDuckGo search failed: {exc}") from exc

        results = [
            WebSearchResult(
                title=item.get("title", ""),
                url=item.get("href", ""),
                snippet=item.get("body", ""),
            )
            for item in raw_results
            if item.get("title") and item.get("href")
        ]

        return WebSearchResponse(query=query, results=results)
