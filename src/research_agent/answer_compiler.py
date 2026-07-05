from __future__ import annotations

from research_agent.domain import SessionMessage
from .domain import Evaluation, Report
from .llm.openrouter import OpenRouterChatClient


class AnswerCompiler:
    def __init__(self, llm_client: OpenRouterChatClient | None = None) -> None:
        self.llm_client = llm_client

    def compile(
        self,
        report: Report,
        evaluation: Evaluation,
        conversation_history: list[SessionMessage] | None = None,
    ) -> str:
        if self.llm_client is not None:
            try:
                return self.llm_client.generate_answer(
                    conversation_history=conversation_history or [],
                    report=report.content,
                    evaluation_score=evaluation.score,
                    evaluation_feedback=evaluation.feedback,
                    citations=report.citations,
                )
            except Exception as exc:
                fallback_reason = f"Gemini generation failed, falling back to local formatter: {exc}"
                feedback = evaluation.feedback + [fallback_reason]
                evaluation = Evaluation(
                    research_run_id=evaluation.research_run_id,
                    report_id=evaluation.report_id,
                    score=evaluation.score,
                    feedback=feedback,
                )

        feedback = "\n".join(f"- {item}" for item in evaluation.feedback)
        citations = "\n".join(f"- {citation}" for citation in report.citations) or "- none"
        return (
            "Final answer\n"
            f"{report.content}\n\n"
            f"Evaluation score: {evaluation.score}/10\n"
            "Feedback:\n"
            f"{feedback}\n\n"
            "Citations:\n"
            f"{citations}"
        )
