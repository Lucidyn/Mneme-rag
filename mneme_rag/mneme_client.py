from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Iterator

import httpx

from .config import settings


@dataclass
class Hit:
    id: str
    path: str
    title: str
    heading: str
    snippet: str
    score: float
    source: str
    start_line: int
    text: str
    kind: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "path": self.path,
            "title": self.title,
            "heading": self.heading,
            "snippet": self.snippet,
            "score": self.score,
            "source": self.source,
            "start_line": self.start_line,
            "kind": self.kind,
            "text": self.text,
        }


class MnemeClient:
    """Thin HTTP client for Mneme search + chunk APIs."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float | None = None,
        *,
        fetch_chunk_text: bool = True,
        max_workers: int = 6,
    ):
        self.base_url = (base_url or settings.mneme_base_url).rstrip("/")
        self.fetch_chunk_text = fetch_chunk_text
        self.max_workers = max_workers
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout if timeout is not None else settings.request_timeout,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "MnemeClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def health(self) -> dict[str, Any]:
        r = self._client.get("/api/health")
        r.raise_for_status()
        return r.json()

    def meta(self) -> dict[str, Any]:
        r = self._client.get("/api/meta")
        r.raise_for_status()
        return r.json()

    def search(
        self,
        query: str,
        *,
        mode: str | None = None,
        kind: str | None = None,
        limit: int | None = None,
        fetch_text: bool | None = None,
    ) -> list[Hit]:
        params = {
            "q": query,
            "mode": mode or settings.search_mode,
            "kind": kind or settings.search_kind,
            "limit": str(limit or settings.search_limit),
        }
        r = self._client.get("/api/search", params=params)
        r.raise_for_status()
        payload = r.json()
        raw_hits = payload.get("hits") or []

        should_fetch = (
            fetch_text if fetch_text is not None else self.fetch_chunk_text
        )
        texts: dict[str, str] = {}
        if should_fetch and raw_hits:
            texts = self._fetch_texts([str(item.get("id", "")) for item in raw_hits])

        hits: list[Hit] = []
        for item in raw_hits:
            chunk_id = str(item.get("id", ""))
            chunk_text = texts.get(chunk_id) or item.get("snippet") or ""
            hits.append(
                Hit(
                    id=chunk_id,
                    path=str(item.get("path", "")),
                    title=str(item.get("title", "")),
                    heading=str(item.get("heading", "")),
                    snippet=str(item.get("snippet", "")),
                    score=float(item.get("score") or 0),
                    source=str(item.get("source", "")),
                    start_line=int(item.get("startLine") or 1),
                    kind=str(item.get("kind", "")),
                    text=str(chunk_text),
                )
            )
        return hits

    def chunk(self, chunk_id: str) -> dict[str, Any] | None:
        if not chunk_id:
            return None
        r = self._client.get("/api/chunk", params={"id": chunk_id})
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()

    def _chunk_text(self, chunk_id: str) -> str:
        try:
            data = self.chunk(chunk_id)
            if not data:
                return ""
            return str(data.get("text") or "")
        except httpx.HTTPError:
            return ""

    def _fetch_texts(self, chunk_ids: list[str]) -> dict[str, str]:
        unique = [cid for cid in dict.fromkeys(chunk_ids) if cid]
        if not unique:
            return {}
        if len(unique) == 1:
            return {unique[0]: self._chunk_text(unique[0])}

        out: dict[str, str] = {}
        workers = min(self.max_workers, len(unique))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(self._chunk_text, cid): cid for cid in unique}
            for fut in as_completed(futures):
                cid = futures[fut]
                out[cid] = fut.result()
        return out


def format_context(hits: list[Hit], *, max_chars: int | None = None) -> str:
    if not hits:
        return "(无检索结果)"
    blocks: list[str] = []
    total = 0
    for i, hit in enumerate(hits, start=1):
        heading = f" · {hit.heading}" if hit.heading else ""
        kind = f" kind={hit.kind}" if hit.kind else ""
        body = (hit.text or hit.snippet).strip()
        block = (
            f"[{i}] {hit.path}:{hit.start_line}{heading}\n"
            f"来源={hit.source} score={hit.score:.3f}{kind}\n{body}"
        )
        if max_chars is not None and total + len(block) > max_chars and blocks:
            break
        blocks.append(block)
        total += len(block) + 8
    return "\n\n---\n\n".join(blocks)


def iter_hit_summaries(hits: list[Hit]) -> Iterator[str]:
    for i, hit in enumerate(hits, start=1):
        yield f"[{i}] {hit.path}:{hit.start_line}  ({hit.source}, {hit.score:.3f})"
