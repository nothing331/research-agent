from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

from research_agent.vector_search.types import ParsedPage


class PdfLoader:
    def load_pages(self, pdf_path: Path) -> list[ParsedPage]:
        reader = PdfReader(str(pdf_path))
        pages: list[ParsedPage] = []
        for index, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            normalized = " ".join(text.split())
            if normalized:
                pages.append(ParsedPage(page_number=index, text=normalized))
        return pages
