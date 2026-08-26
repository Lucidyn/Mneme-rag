"""Mneme + LangChain RAG helpers.

Retrieve from a running Mneme instance, then answer with any OpenAI-compatible LLM.
"""

from .chain import AskResult, ask, ask_stream, build_llm
from .config import Settings, settings
from .mneme_client import Hit, MnemeClient, format_context

__all__ = [
    "AskResult",
    "Hit",
    "MnemeClient",
    "Settings",
    "ask",
    "ask_stream",
    "build_llm",
    "format_context",
    "settings",
]

__version__ = "0.2.0"
