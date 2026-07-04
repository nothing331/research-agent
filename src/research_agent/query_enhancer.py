from __future__ import annotations


class QueryEnhancer:
    """Small deterministic placeholder for future planner behavior."""

    def enhance(self, query: str) -> str:
        trimmed = query.strip()
        if not trimmed:
            return trimmed
        return (
            f"{trimmed}\n\n"
            "Research requirements:\n"
            "- identify key facts\n"
            "- surface supporting evidence\n"
            "- note uncertainty or missing information"
        )
