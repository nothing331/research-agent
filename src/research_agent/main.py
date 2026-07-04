from __future__ import annotations

from research_agent.answer_compiler import AnswerCompiler
from research_agent.config import load_settings
from research_agent.evaluation import Evaluator
from research_agent.execution_logger import ExecutionLogger
from research_agent.llm.gemini import GeminiClient
from research_agent.orchestrator import ResearchOrchestrator
from research_agent.persistence.file_repository import FileRepository
from research_agent.query_enhancer import QueryEnhancer
from research_agent.reporting import ReportBuilder
from research_agent.tools.calculator import CalculatorTool
from research_agent.tools.vector_search import VectorSearchTool
from research_agent.tools.web_search import WebSearchTool


def build_app() -> ResearchOrchestrator:
    settings = load_settings()
    repository = FileRepository(settings.data_dir)
    tools = [WebSearchTool(), VectorSearchTool(), CalculatorTool()]
    llm_client = None
    if settings.gemini_api_key:
        llm_client = GeminiClient(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
            system_prompt=settings.system_prompt,
        )

    return ResearchOrchestrator(
        repository=repository,
        tools=tools,
        query_enhancer=QueryEnhancer(),
        report_builder=ReportBuilder(),
        evaluator=Evaluator(),
        answer_compiler=AnswerCompiler(llm_client=llm_client),
        execution_logger=ExecutionLogger(settings.logs_dir),
    )


def main() -> None:
    orchestrator = build_app()
    session = orchestrator.create_session()
    print("Research agent terminal v1. Type 'exit' to quit.")
    print("Conversation transcripts are saved under runtime_data and logs under runtime_logs.")

    message_index = 0
    while True:
        query = input("\nYou: ").strip()
        if query.lower() in {"exit", "quit"}:
            break
        if not query:
            print("Please enter a research query.")
            continue

        answer = orchestrator.run(session, query, message_index=message_index)
        message_index += 2
        print(f"\nAssistant:\n{answer}")


if __name__ == "__main__":
    main()
