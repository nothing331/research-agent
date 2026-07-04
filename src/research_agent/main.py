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
from research_agent.tools.india_tool import IndiaTool
from research_agent.tools.vector_search import VectorSearchTool
from research_agent.tools.web_search import WebSearchTool
from research_agent.vector_search.cache import VectorCache
from research_agent.vector_search.chunker import SlidingWindowChunker
from research_agent.vector_search.embeddings import OpenRouterEmbeddingClient
from research_agent.vector_search.index import InMemoryVectorIndex


def build_app() -> ResearchOrchestrator:
    settings = load_settings()
    repository = FileRepository(settings.data_dir)
    vector_index = InMemoryVectorIndex(
        documents_dir=settings.vector_search_documents_dir,
        embedding_client=OpenRouterEmbeddingClient(
            api_key=settings.open_router_api_key,
            model=settings.embedding_model,
        ),
        cache=VectorCache(settings.vector_search_cache_dir),
        chunker=SlidingWindowChunker(
            chunk_size=settings.vector_search_chunk_size,
            chunk_overlap=settings.vector_search_chunk_overlap,
        ),
    )
    tools = [
        WebSearchTool(),
        VectorSearchTool(index=vector_index, top_k=settings.vector_search_top_k),
        CalculatorTool(),
        IndiaTool(),
    ]
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
