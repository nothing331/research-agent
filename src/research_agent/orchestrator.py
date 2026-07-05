from __future__ import annotations

from uuid import UUID

from research_agent.answer_compiler import AnswerCompiler
from research_agent.domain import RunStatus, Session, SessionMessage, ToolCallRecord, ToolCallStatus, utc_now
from research_agent.evaluation import Evaluator
from research_agent.execution_logger import ExecutionLogger
from research_agent.persistence.base import Repository
from research_agent.query_enhancer import QueryEnhancer
from research_agent.reporting import ReportBuilder
from research_agent.tools.base import ResearchTool, ToolContext


class ResearchOrchestrator:
    def __init__(
        self,
        repository: Repository,
        tools: list[ResearchTool],
        query_enhancer: QueryEnhancer,
        report_builder: ReportBuilder,
        evaluator: Evaluator,
        answer_compiler: AnswerCompiler,
        execution_logger: ExecutionLogger,
    ) -> None:
        self.repository = repository
        self.tools = tools
        self.query_enhancer = query_enhancer
        self.report_builder = report_builder
        self.evaluator = evaluator
        self.answer_compiler = answer_compiler
        self.execution_logger = execution_logger

    def create_session(self) -> Session:
        session = Session()
        self.repository.create_session(session)
        self.execution_logger.log(
            session_id=session.id,
            run_id=None,
            step="session_created",
            detail=f"Session {session.id} created.",
        )
        return session

    def run(self, session: Session, query: str, message_index: int) -> str:
        user_message = SessionMessage(
            session_id=session.id,
            role="user",
            content=query,
            message_index=message_index,
        )
        self.repository.append_message(user_message)
        self.execution_logger.log(
            session_id=session.id,
            run_id=None,
            step="user_message_saved",
            detail=f"Stored user message {user_message.id}.",
        )

        from research_agent.domain import ResearchRun

        research_run = ResearchRun(
            session_id=session.id,
            user_message_id=user_message.id,
            query=query,
        )
        self.repository.create_research_run(research_run)
        self._log_run(session.id, research_run.id, "research_run_created", f"Created run for query: {query}")

        research_run.enhanced_query = self.query_enhancer.enhance(query)
        research_run.status = RunStatus.ENHANCED
        research_run.updated_at = utc_now()
        self.repository.update_research_run(research_run)
        self._log_run(session.id, research_run.id, "query_enhanced", research_run.enhanced_query)

        research_run.status = RunStatus.RUNNING_TOOLS
        research_run.updated_at = utc_now()
        self.repository.update_research_run(research_run)
        self._log_run(session.id, research_run.id, "tools_started", "Beginning tool execution.")

        context = ToolContext(
            enhanced_query=research_run.enhanced_query,
            original_query=research_run.query,
        )
        results = []

        for tool in self.tools:
            tool_call = ToolCallRecord(
                research_run_id=research_run.id,
                tool_name=tool.name,
                input_payload={"enhanced_query": context.enhanced_query},
            )
            self.repository.record_tool_call(tool_call)
            self._log_run(session.id, research_run.id, "tool_call_started", f"{tool.name} started.")

            try:
                result = tool.run(context)
                tool_call.status = ToolCallStatus.SUCCEEDED
                tool_call.output_payload = result.raw_output
                tool_call.completed_at = utc_now()
                self.repository.record_tool_call(tool_call)
                self._log_run(
                    session.id,
                    research_run.id,
                    "tool_call_succeeded",
                    f"{tool.name} completed with summary: {result.summary}",
                )
                results.append(result)
            except Exception as exc:
                tool_call.status = ToolCallStatus.FAILED
                tool_call.error_message = str(exc)
                tool_call.completed_at = utc_now()
                self.repository.record_tool_call(tool_call)
                research_run.status = RunStatus.FAILED
                research_run.updated_at = utc_now()
                research_run.completed_at = utc_now()
                self.repository.update_research_run(research_run)
                self._log_run(session.id, research_run.id, "tool_call_failed", f"{tool.name} failed: {exc}")
                raise

        report = self.report_builder.build(research_run.id, results)
        self.repository.save_report(report)
        research_run.status = RunStatus.REPORT_GENERATED
        research_run.updated_at = utc_now()
        self.repository.update_research_run(research_run)
        self._log_run(session.id, research_run.id, "report_generated", report.content)

        evaluation = self.evaluator.evaluate(research_run.id, report)
        self.repository.save_evaluation(evaluation)
        research_run.status = RunStatus.EVALUATED
        research_run.updated_at = utc_now()
        self.repository.update_research_run(research_run)
        self._log_run(
            session.id,
            research_run.id,
            "report_evaluated",
            f"Score={evaluation.score} Feedback={'; '.join(evaluation.feedback)}",
        )

        conversation_history = self.repository.list_messages(session.id)
        final_answer = self.answer_compiler.compile(report, evaluation, conversation_history=conversation_history)
        assistant_message = SessionMessage(
            session_id=session.id,
            role="assistant",
            content=final_answer,
            message_index=message_index + 1,
        )
        self.repository.append_message(assistant_message)
        self._log_run(session.id, research_run.id, "assistant_message_saved", f"Stored assistant message {assistant_message.id}.")

        research_run.status = RunStatus.COMPLETED
        research_run.updated_at = utc_now()
        research_run.completed_at = utc_now()
        self.repository.update_research_run(research_run)
        self._log_run(session.id, research_run.id, "research_run_completed", "Run completed successfully.")

        return final_answer

    def _log_run(self, session_id: UUID, run_id: UUID, step: str, detail: str) -> None:
        self.execution_logger.log(session_id=session_id, run_id=run_id, step=step, detail=detail)
