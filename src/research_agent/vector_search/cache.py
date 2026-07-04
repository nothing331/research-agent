from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from research_agent.vector_search.types import DocumentChunk


class VectorCache:
    def __init__(self, cache_dir: str) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def load_chunks(
        self,
        document_id: str,
        source_path: Path,
        embedding_model: str,
        chunk_size: int,
        chunk_overlap: int,
    ) -> list[DocumentChunk] | None:
        cache_path = self._cache_path(document_id)
        if not cache_path.exists():
            return None

        payload = json.loads(cache_path.read_text(encoding="utf-8"))
        metadata = payload.get("metadata", {})
        expected = {
            "source_path": str(source_path.resolve()),
            "modified_time": source_path.stat().st_mtime,
            "file_size": source_path.stat().st_size,
            "embedding_model": embedding_model,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
        }
        if metadata != expected:
            return None

        return [
            DocumentChunk(
                chunk_id=item["chunk_id"],
                document_id=item["document_id"],
                filename=item["filename"],
                page_number=item["page_number"],
                chunk_index=item["chunk_index"],
                text=item["text"],
                embedding=item["embedding"],
                created_at=item["created_at"],
            )
            for item in payload.get("chunks", [])
        ]

    def save_chunks(
        self,
        document_id: str,
        source_path: Path,
        embedding_model: str,
        chunk_size: int,
        chunk_overlap: int,
        chunks: list[DocumentChunk],
    ) -> None:
        cache_path = self._cache_path(document_id)
        payload = {
            "metadata": {
                "source_path": str(source_path.resolve()),
                "modified_time": source_path.stat().st_mtime,
                "file_size": source_path.stat().st_size,
                "embedding_model": embedding_model,
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
            },
            "chunks": [asdict(chunk) for chunk in chunks],
        }
        cache_path.write_text(json.dumps(payload, default=str, indent=2), encoding="utf-8")

    def _cache_path(self, document_id: str) -> Path:
        return self.cache_dir / f"{document_id}.json"
