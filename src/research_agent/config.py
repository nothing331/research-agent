from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path


def load_dotenv_file(dotenv_path: str = ".env") -> None:
    path = Path(dotenv_path)
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


@dataclass(slots=True)
class Settings:
    app_name: str = "research-agent"
    postgres_dsn: str = field(default_factory=lambda: os.getenv("POSTGRES_DSN", ""))
    evaluator_min_score: int = field(default_factory=lambda: int(os.getenv("EVALUATOR_MIN_SCORE", "7")))
    gemini_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    gemini_model: str = field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-2.0-flash"))
    open_router_api_key: str = field(default_factory=lambda: os.getenv("OPEN_ROUTER_API", ""))
    embedding_model: str = field(default_factory=lambda: os.getenv("EMBEDDING_MODEL", "openai/text-embedding-3-small"))
    data_dir: str = field(default_factory=lambda: os.getenv("RESEARCH_AGENT_DATA_DIR", "runtime_data"))
    logs_dir: str = field(default_factory=lambda: os.getenv("RESEARCH_AGENT_LOG_DIR", "runtime_logs"))
    vector_search_documents_dir: str = field(default_factory=lambda: os.getenv("VECTOR_SEARCH_DOCUMENTS_DIR", "documents"))
    vector_search_cache_dir: str = field(default_factory=lambda: os.getenv("VECTOR_SEARCH_CACHE_DIR", "runtime_data/vector_cache"))
    vector_search_chunk_size: int = field(default_factory=lambda: int(os.getenv("VECTOR_SEARCH_CHUNK_SIZE", "1200")))
    vector_search_chunk_overlap: int = field(default_factory=lambda: int(os.getenv("VECTOR_SEARCH_CHUNK_OVERLAP", "200")))
    vector_search_top_k: int = field(default_factory=lambda: int(os.getenv("VECTOR_SEARCH_TOP_K", "3")))
    system_prompt: str = field(
        default_factory=lambda: os.getenv(
            "RESEARCH_AGENT_SYSTEM_PROMPT",
            (
                "You are a helpful AI research assistant. Answer conversationally, "
                "use the provided report and evaluation notes when relevant, and be honest "
                "about missing evidence or tool limitations."
            ),
        )
    )


def load_settings() -> Settings:
    load_dotenv_file()
    return Settings()
