from __future__ import annotations

import math
from pathlib import Path

from research_agent.vector_search.cache import VectorCache
from research_agent.vector_search.chunker import SlidingWindowChunker
from research_agent.vector_search.embeddings import OpenRouterEmbeddingClient
from research_agent.vector_search.pdf_loader import PdfLoader
from research_agent.vector_search.types import DocumentChunk, SearchMatch, SearchResult


class InMemoryVectorIndex:
    def __init__(
        self,
        documents_dir: str,
        embedding_client: OpenRouterEmbeddingClient,
        cache: VectorCache,
        chunker: SlidingWindowChunker,
    ) -> None:
        self.documents_dir = Path(documents_dir)
        self.embedding_client = embedding_client
        self.cache = cache
        self.chunker = chunker
        self.pdf_loader = PdfLoader()
        self.chunks: list[DocumentChunk] = []
        self._ready = False

    def ensure_ready(self) -> None:
        if self._ready:
            return

        self.documents_dir.mkdir(parents=True, exist_ok=True)
        pdf_paths = sorted(self.documents_dir.glob("*.pdf"))
        loaded_chunks: list[DocumentChunk] = []

        for pdf_path in pdf_paths:
            document_id = pdf_path.stem
            cached = self.cache.load_chunks(
                document_id=document_id,
                source_path=pdf_path,
                embedding_model=self.embedding_client.model,
                chunk_size=self.chunker.chunk_size,
                chunk_overlap=self.chunker.chunk_overlap,
            )
            if cached is not None:
                loaded_chunks.extend(cached)
                continue

            pages = self.pdf_loader.load_pages(pdf_path)
            chunks = self.chunker.chunk_pages(document_id=document_id, pdf_path=pdf_path, pages=pages)
            if not chunks:
                continue

            embeddings = self._embed_chunks(chunks, title=pdf_path.name)
            for chunk, embedding in zip(chunks, embeddings, strict=True):
                chunk.embedding = embedding

            self.cache.save_chunks(
                document_id=document_id,
                source_path=pdf_path,
                embedding_model=self.embedding_client.model,
                chunk_size=self.chunker.chunk_size,
                chunk_overlap=self.chunker.chunk_overlap,
                chunks=chunks,
            )
            loaded_chunks.extend(chunks)

        self.chunks = loaded_chunks
        self._ready = True

    def search(self, query: str, top_k: int) -> SearchResult:
        self.ensure_ready()
        if not self.chunks:
            return SearchResult(query=query, top_k=top_k, matches=[])

        query_embedding = self.embedding_client.embed_query(query)
        scored = []
        for chunk in self.chunks:
            if not chunk.embedding:
                continue
            score = cosine_similarity(query_embedding, chunk.embedding)
            scored.append(
                SearchMatch(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    filename=chunk.filename,
                    page_number=chunk.page_number,
                    score=score,
                    text=chunk.text,
                )
            )

        ranked = sorted(scored, key=lambda item: item.score, reverse=True)[:top_k]
        return SearchResult(query=query, top_k=top_k, matches=ranked)

    def _embed_chunks(self, chunks: list[DocumentChunk], title: str) -> list[list[float]]:
        all_embeddings: list[list[float]] = []
        batch_size = 16
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start : start + batch_size]
            embeddings = self.embedding_client.embed_texts([chunk.text for chunk in batch], title=title)
            all_embeddings.extend(embeddings)
        return all_embeddings


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0

    numerator = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)
