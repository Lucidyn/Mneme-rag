from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from .config import settings
from .mneme_client import Hit, MnemeClient, format_context

SYSTEM_PROMPT = """你是本地第二大脑助手。只根据「检索上下文」回答用户问题。
规则：
1. 优先引用上下文中的路径与要点；不确定就明确说不知道。
2. 不要编造上下文里没有的文件或结论。
3. 回答简洁，可用中文；必要时用列表。
4. 文末用「参考：」列出用到的 [编号] 与路径。
5. 若检索上下文为「(无检索结果)」，说明知识库里没找到相关内容，并给出可尝试的检索词建议。"""

PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        (
            "human",
            "检索上下文：\n{context}\n\n用户问题：{question}",
        ),
    ]
)


@dataclass
class AskResult:
    answer: str
    hits: list[Hit]
    context: str
    question: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "question": self.question,
            "answer": self.answer,
            "hits": [h.to_dict() for h in self.hits],
            "context": self.context,
        }


def build_llm(*, streaming: bool = False) -> ChatOpenAI:
    kwargs: dict[str, Any] = {
        "base_url": settings.llm_base_url,
        "api_key": settings.llm_api_key,
        "model": settings.llm_model,
        "temperature": settings.llm_temperature,
        "streaming": streaming,
    }
    if settings.llm_max_tokens is not None and settings.llm_max_tokens > 0:
        kwargs["max_tokens"] = settings.llm_max_tokens
    return ChatOpenAI(**kwargs)


def _retrieve(
    question: str,
    client: MnemeClient,
    *,
    mode: str | None = None,
    kind: str | None = None,
    limit: int | None = None,
) -> tuple[list[Hit], str]:
    hits = client.search(question, mode=mode, kind=kind, limit=limit)
    return hits, format_context(hits)


def ask(
    question: str,
    client: MnemeClient | None = None,
    *,
    mode: str | None = None,
    kind: str | None = None,
    limit: int | None = None,
) -> AskResult:
    """Retrieve from Mneme, then generate with LangChain LCEL."""
    owns_client = client is None
    client = client or MnemeClient()
    try:
        hits, context = _retrieve(
            question, client, mode=mode, kind=kind, limit=limit
        )
        chain = PROMPT | build_llm() | StrOutputParser()
        answer = chain.invoke({"context": context, "question": question})
        return AskResult(
            answer=answer.strip(),
            hits=hits,
            context=context,
            question=question,
        )
    finally:
        if owns_client:
            client.close()


def ask_stream(
    question: str,
    client: MnemeClient | None = None,
    *,
    mode: str | None = None,
    kind: str | None = None,
    limit: int | None = None,
) -> tuple[list[Hit], str, Iterator[str]]:
    """Retrieve first, then yield answer tokens.

    Returns ``(hits, context, token_iterator)``.
    """
    owns_client = client is None
    client = client or MnemeClient()
    try:
        hits, context = _retrieve(
            question, client, mode=mode, kind=kind, limit=limit
        )
    finally:
        if owns_client:
            client.close()

    chain = PROMPT | build_llm(streaming=True) | StrOutputParser()

    def _tokens() -> Iterator[str]:
        for chunk in chain.stream({"context": context, "question": question}):
            if chunk:
                yield chunk

    return hits, context, _tokens()
