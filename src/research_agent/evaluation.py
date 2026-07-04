from __future__ import annotations

from .domain import Evaluation, Report


class Evaluator:
    def evaluate(self, research_run_id, report: Report) -> Evaluation:
        feedback: list[str] = []
        score = 10

        if "No tool data" in report.content:
            score -= 5
            feedback.append("No evidence was collected from tools.")
        if not report.citations:
            score -= 2
            feedback.append("The report has no citations yet.")
        if len(report.content.split()) < 30:
            score -= 1
            feedback.append("The report is brief and may need deeper synthesis.")

        if not feedback:
            feedback.append("The report satisfies the current v1 quality checks.")

        return Evaluation(
            research_run_id=research_run_id,
            report_id=report.id,
            score=max(score, 1),
            feedback=feedback,
        )
