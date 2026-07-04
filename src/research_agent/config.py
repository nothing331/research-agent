from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(slots=True)
class Settings:
    app_name: str = "research-agent"
    postgres_dsn: str = os.getenv("POSTGRES_DSN", "")
    evaluator_min_score: int = int(os.getenv("EVALUATOR_MIN_SCORE", "7"))
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    data_dir: str = os.getenv("RESEARCH_AGENT_DATA_DIR", "runtime_data")
    logs_dir: str = os.getenv("RESEARCH_AGENT_LOG_DIR", "runtime_logs")
    system_prompt: str = os.getenv(
        "RESEARCH_AGENT_SYSTEM_PROMPT",
        (
            "You are a helpful AI research assistant. Answer conversationally, "
            "use the provided report and evaluation notes when relevant, and be honest "
            "about missing evidence or tool limitations."
        ),
    )


def load_settings() -> Settings:
    return Settings()
