"""Lightweight unit tests (no Mneme / LLM required)."""

from __future__ import annotations

from mneme_rag.mneme_client import Hit, format_context


def test_format_context_empty() -> None:
    assert format_context([]) == "(无检索结果)"


def test_format_context_hit() -> None:
    hit = Hit(
        id="c1",
        path="notes/a.md",
        title="A",
        heading="Intro",
        snippet="short",
        score=0.5,
        source="hybrid",
        start_line=3,
        text="full body",
        kind="text",
    )
    ctx = format_context([hit])
    assert "[1] notes/a.md:3 · Intro" in ctx
    assert "full body" in ctx
    assert "score=0.500" in ctx


def test_hit_to_dict() -> None:
    hit = Hit("1", "p", "t", "", "s", 1.0, "k", 1, "body")
    d = hit.to_dict()
    assert d["path"] == "p"
    assert d["text"] == "body"


if __name__ == "__main__":
    test_format_context_empty()
    test_format_context_hit()
    test_hit_to_dict()
    print("ok")
