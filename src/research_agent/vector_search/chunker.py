from __future__ import annotations

from pathlib import Path

from research_agent.vector_search.types import DocumentChunk, ParsedPage


class SlidingWindowChunker:
    def __init__(self, chunk_size: int, chunk_overlap: int) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive.")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative.")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size.")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_pages(self, document_id: str, pdf_path: Path, pages: list[ParsedPage]) -> list[DocumentChunk]:
        chunks: list[DocumentChunk] = []
        step = self.chunk_size - self.chunk_overlap
        filename = pdf_path.name

        for page in pages:
            text = page.text
            if len(text) <= self.chunk_size:
                chunks.append(
                    DocumentChunk(
                        chunk_id=f"{document_id}-p{page.page_number}-c0",
                        document_id=document_id,
                        filename=filename,
                        page_number=page.page_number,
                        chunk_index=0,
                        text=text,
                    )
                )
                continue

            chunk_index = 0
            for start in range(0, len(text), step):
                window = text[start : start + self.chunk_size].strip()
                if not window:
                    continue
                chunks.append(
                    DocumentChunk(
                        chunk_id=f"{document_id}-p{page.page_number}-c{chunk_index}",
                        document_id=document_id,
                        filename=filename,
                        page_number=page.page_number,
                        chunk_index=chunk_index,
                        text=window,
                    )
                )
                chunk_index += 1
                if start + self.chunk_size >= len(text):
                    break

        return chunks
