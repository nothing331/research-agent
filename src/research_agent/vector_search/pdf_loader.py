from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

import pdfplumber

from research_agent.vector_search.types import ParsedPage


class PdfLoader:
    def __init__(self, header_footer_filter: bool = True) -> None:
        self.header_footer_filter = header_footer_filter

    def load_pages(self, pdf_path: Path) -> list[ParsedPage]:
        with pdfplumber.open(str(pdf_path)) as pdf:
            raw_pages: list[tuple[int, str]] = []
            for i, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                text = text.strip()
                if text:
                    raw_pages.append((i, text))

        if self.header_footer_filter and len(raw_pages) > 1:
            filtered = self._filter_headers_footers(raw_pages)
        else:
            filtered = raw_pages

        return [ParsedPage(page_number=num, text=text) for num, text in filtered]

    def _filter_headers_footers(self, pages: list[tuple[int, str]]) -> list[tuple[int, str]]:
        line_pages: dict[str, set[int]] = {}
        for page_num, text in pages:
            lines = text.split("\n")
            for line in lines:
                normalized = self._normalize_line(line)
                if normalized:
                    line_pages.setdefault(normalized, set()).add(page_num)

        total_pages = len(pages)
        repeated_lines: set[str] = set()
        for line_text, page_set in line_pages.items():
            if len(page_set) >= max(2, total_pages * 0.5):
                repeated_lines.add(line_text)

        page_number_pattern = re.compile(r"^\d+$")
        filtered_pages: list[tuple[int, str]] = []

        for page_num, text in pages:
            lines = text.split("\n")
            clean_lines: list[str] = []
            for line in lines:
                normalized = self._normalize_line(line)
                if normalized in repeated_lines:
                    continue
                if page_number_pattern.match(normalized):
                    continue
                clean_lines.append(line)
            filtered_pages.append((page_num, "\n".join(clean_lines).strip()))

        return filtered_pages

    @staticmethod
    def _normalize_line(line: str) -> str:
        return re.sub(r"\s+", " ", line.strip().lower())
