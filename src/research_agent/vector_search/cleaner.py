from __future__ import annotations

from research_agent.vector_search.types import ParsedPage


class BoilerplateCleaner:
    def __init__(self, threshold: float = 0.8) -> None:
        if not 0 < threshold <= 1:
            raise ValueError("threshold must be in (0, 1]")
        self.threshold = threshold

    def clean(self, pages: list[ParsedPage]) -> list[ParsedPage]:
        if len(pages) < 2:
            return pages

        line_page_counts: dict[str, set[int]] = {}
        for page in pages:
            seen_on_page = set()
            for line in page.text.split("\n"):
                stripped = line.strip()
                if not stripped:
                    continue
                if stripped not in line_page_counts:
                    line_page_counts[stripped] = set()
                seen_on_page.add(stripped)
            for stripped in seen_on_page:
                line_page_counts[stripped].add(page.page_number)

        num_pages = len(pages)
        boilerplate_lines = {
            line
            for line, pages_set in line_page_counts.items()
            if len(pages_set) / num_pages >= self.threshold
        }

        cleaned_pages: list[ParsedPage] = []
        for page in pages:
            cleaned_lines = [
                line
                for line in page.text.split("\n")
                if line.strip() not in boilerplate_lines
            ]
            text = " ".join(" ".join(cleaned_lines).split())
            cleaned_pages.append(ParsedPage(page_number=page.page_number, text=text))

        return cleaned_pages
