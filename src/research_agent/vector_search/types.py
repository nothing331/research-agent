from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from research_agent.domain import utc_now


@dataclass(slots=True)
class ParsedPage:
    page_number: int
    text: str


@dataclass(slots=True)
class DocumentChunk:
    chunk_id: str
    document_id: str
    filename: str
    page_number: int
    chunk_index: int
    text: str
    embedding: list[float] = field(default_factory=list)
    created_at: datetime = field(default_factory=utc_now)


@dataclass(slots=True)
class SearchMatch:
    chunk_id: str
    document_id: str
    filename: str
    page_number: int
    score: float
    text: str


@dataclass(slots=True)
class SearchResult:
    query: str
    top_k: int
    matches: list[SearchMatch]
