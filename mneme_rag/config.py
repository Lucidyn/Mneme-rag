from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return float(raw)


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw)


@dataclass(frozen=True)
class Settings:
    mneme_base_url: str = os.getenv("MNEME_BASE_URL", "http://127.0.0.1:8791").rstrip("/")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "http://127.0.0.1:11434/v1").rstrip("/")
    llm_api_key: str = os.getenv("LLM_API_KEY", "ollama")
    llm_model: str = os.getenv("LLM_MODEL", "qwen2.5:7b")
    llm_temperature: float = _env_float("LLM_TEMPERATURE", 0.2)
    llm_max_tokens: int | None = (
        None if os.getenv("LLM_MAX_TOKENS", "").strip() == "" else _env_int("LLM_MAX_TOKENS", 0)
    )
    search_mode: str = os.getenv("SEARCH_MODE", "hybrid")
    search_limit: int = _env_int("SEARCH_LIMIT", 6)
    search_kind: str = os.getenv("SEARCH_KIND", "all")
    request_timeout: float = _env_float("REQUEST_TIMEOUT", 60.0)


settings = Settings()
