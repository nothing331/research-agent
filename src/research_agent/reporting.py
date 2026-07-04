from __future__ import annotations

from .domain import Report, ToolResult


class ReportBuilder:
    def build(self, research_run_id, results: list[ToolResult]) -> Report:
        sections: list[str] = []
        citations: list[str] = []

        for result in results:
            sections.append(f"{result.tool_name}: {result.summary}")
            citations.extend(result.citations)

        content = "\n\n".join(sections) if sections else "No tool data was collected."
        return Report(
            research_run_id=research_run_id,
            version=1,
            content=content,
            citations=sorted(set(citations)),
        )
