from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class WebSearchResult:
    title: str
    url: str
    snippet: str


@dataclass(slots=True)
class WebSearchResponse:
    query: str
    results: list[WebSearchResult]
    cached: bool = False
    cached_at: datetime | None = None
