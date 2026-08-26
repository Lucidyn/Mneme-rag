#!/usr/bin/env python3
"""CLI: ask your Mneme index via LangChain RAG.

Prereq:
  1) Mneme serving (see https://github.com/Lucidyn/Mneme)
  2) OpenAI-compatible LLM (Ollama recommended)
  3) cp .env.example .env && edit if needed
"""

from __future__ import annotations

import argparse
import json
import sys

import httpx

from mneme_rag.chain import ask, ask_stream
from mneme_rag.config import settings
from mneme_rag.mneme_client import MnemeClient


def cmd_health() -> int:
    try:
        with MnemeClient() as client:
            data = client.health()
    except httpx.HTTPError as exc:
        print(f"Mneme 不可达 ({settings.mneme_base_url}): {exc}", file=sys.stderr)
        return 1

    indexed = data.get("indexed")
    meta = data.get("meta") or {}
    print(f"mneme: {settings.mneme_base_url}")
    print(f"indexed: {indexed}")
    print(f"files: {meta.get('fileCount')}  chunks: {meta.get('chunkCount')}")
    print(f"ocr={meta.get('ocr')} embed={meta.get('embed')}")
    print(f"watch={data.get('watch')} embedderReady={data.get('embedderReady')}")
    print(f"llm: {settings.llm_model} @ {settings.llm_base_url}")
    print(f"search: mode={settings.search_mode} limit={settings.search_limit} kind={settings.search_kind}")
    return 0


def _print_hits(hits) -> None:
    print("=== 检索命中 ===")
    if not hits:
        print("(无)")
    for i, hit in enumerate(hits, start=1):
        kind = f", {hit.kind}" if hit.kind else ""
        print(f"[{i}] {hit.path}:{hit.start_line}  ({hit.source}, {hit.score:.3f}{kind})")
        snippet = hit.snippet[:120]
        print(f"    {snippet}{'…' if len(hit.snippet) > 120 else ''}")
    print()


def cmd_ask(
    question: str,
    *,
    show_hits: bool,
    as_json: bool,
    stream: bool,
    mode: str | None,
    kind: str | None,
    limit: int | None,
) -> int:
    try:
        if as_json:
            result = ask(question, mode=mode, kind=kind, limit=limit)
            print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
            return 0

        if stream:
            hits, _context, tokens = ask_stream(
                question, mode=mode, kind=kind, limit=limit
            )
            if show_hits:
                _print_hits(hits)
            print("=== 回答 ===")
            for token in tokens:
                print(token, end="", flush=True)
            print()
            return 0

        result = ask(question, mode=mode, kind=kind, limit=limit)
    except httpx.HTTPError as exc:
        print(f"检索失败（请先启动 Mneme）: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 — surface LLM/config errors to CLI
        print(f"生成失败: {exc}", file=sys.stderr)
        return 1

    if show_hits:
        _print_hits(result.hits)

    print("=== 回答 ===")
    print(result.answer)
    return 0


def cmd_search(
    question: str,
    *,
    mode: str | None,
    kind: str | None,
    limit: int | None,
    as_json: bool,
) -> int:
    try:
        with MnemeClient() as client:
            hits = client.search(question, mode=mode, kind=kind, limit=limit)
    except httpx.HTTPError as exc:
        print(f"检索失败（请先启动 Mneme）: {exc}", file=sys.stderr)
        return 1

    if as_json:
        print(json.dumps([h.to_dict() for h in hits], ensure_ascii=False, indent=2))
        return 0

    _print_hits(hits)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mneme-rag",
        description="Ask Mneme with LangChain RAG",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("health", help="Check Mneme + print LLM / search settings")

    p_ask = sub.add_parser("ask", help="Retrieve + answer")
    p_ask.add_argument("question", nargs="+", help="Question text")
    p_ask.add_argument("--hits", action="store_true", help="Show retrieval hits")
    p_ask.add_argument("--json", action="store_true", help="Print full result as JSON")
    p_ask.add_argument("--stream", action="store_true", help="Stream answer tokens")
    p_ask.add_argument(
        "--mode",
        choices=("hybrid", "keyword", "semantic"),
        default=None,
        help="Override SEARCH_MODE",
    )
    p_ask.add_argument(
        "--kind",
        default=None,
        help="Chunk kind filter (default from SEARCH_KIND / all)",
    )
    p_ask.add_argument("--limit", type=int, default=None, help="Override SEARCH_LIMIT")

    p_search = sub.add_parser("search", help="Retrieve only (no LLM)")
    p_search.add_argument("question", nargs="+", help="Query text")
    p_search.add_argument("--json", action="store_true", help="Print hits as JSON")
    p_search.add_argument(
        "--mode",
        choices=("hybrid", "keyword", "semantic"),
        default=None,
        help="Override SEARCH_MODE",
    )
    p_search.add_argument("--kind", default=None, help="Chunk kind filter")
    p_search.add_argument("--limit", type=int, default=None, help="Override SEARCH_LIMIT")

    return parser


def main(argv: list[str] | None = None) -> None:
    raise SystemExit(_run(argv))


def _run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.cmd == "health":
        return cmd_health()
    if args.cmd == "ask":
        if args.json and args.stream:
            print("--json 与 --stream 不能同时使用", file=sys.stderr)
            return 2
        return cmd_ask(
            " ".join(args.question),
            show_hits=args.hits,
            as_json=args.json,
            stream=args.stream,
            mode=args.mode,
            kind=args.kind,
            limit=args.limit,
        )
    if args.cmd == "search":
        return cmd_search(
            " ".join(args.question),
            mode=args.mode,
            kind=args.kind,
            limit=args.limit,
            as_json=args.json,
        )
    return 2


if __name__ == "__main__":
    main()
