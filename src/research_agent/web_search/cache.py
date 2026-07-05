from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from research_agent.web_search.types import WebSearchResponse, WebSearchResult


class WebSearchCache:
    def __init__(self, cache_dir: str, ttl_hours: int = 24) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_hours = ttl_hours

    def _make_key(self, query: str) -> str:
        normalized = query.strip().lower()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def _make_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"

    def get(self, query: str) -> WebSearchResponse | None:
        key = self._make_key(query)
        path = self._make_path(key)

        if not path.exists():
            return None

        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

        cached_at_str = raw.get("cached_at")
        if not cached_at_str:
            return None

        try:
            cached_at = datetime.fromisoformat(cached_at_str)
        except ValueError:
            return None

        if datetime.now(timezone.utc) - cached_at > timedelta(hours=self.ttl_hours):
            return None

        results = [
            WebSearchResult(
                title=r["title"],
                url=r["url"],
                snippet=r["snippet"],
            )
            for r in raw.get("results", [])
        ]

        return WebSearchResponse(
            query=raw.get("query", query),
            results=results,
            cached=True,
            cached_at=cached_at,
        )

    def save(self, query: str, response: WebSearchResponse) -> None:
        key = self._make_key(query)
        path = self._make_path(key)

        data = {
            "query": response.query,
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "ttl_hours": self.ttl_hours,
            "results": [
                {"title": r.title, "url": r.url, "snippet": r.snippet}
                for r in response.results
            ],
        }

        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
