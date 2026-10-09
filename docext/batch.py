"""Bounded-concurrency batch extraction with per-document isolation and run-level accounting."""
from __future__ import annotations

import asyncio
import statistics
import threading
import time
from collections.abc import Iterable

from .extract import Extractor
from .schema import ExtractionResult


async def extract_many(extractor: Extractor, docs: Iterable[tuple[str, bytes, str]],
                       concurrency: int) -> list[ExtractionResult]:
    """docs: (doc_id, bytes, filename). Order of results matches input order."""
    sem = asyncio.Semaphore(max(1, concurrency))

    async def one(doc_id: str, data: bytes, fname: str) -> ExtractionResult:
        async with sem:
            return await extractor.extract(data, fname, doc_id)

    return await asyncio.gather(*(one(*d) for d in docs))


class Metrics:
    """Process-wide counters exposed on /metrics. Thread-safe, no external deps."""

    def __init__(self):
        self._lock = threading.Lock()
        self.started = time.time()
        self.docs = self.failed = self.calls = self.cache_hits = 0
        self.input_tokens = self.output_tokens = 0
        self.cost_usd = self.list_cost_usd = 0.0
        self._latencies: list[float] = []

    def record(self, r: ExtractionResult) -> None:
        with self._lock:
            self.docs += 1
            self.failed += r.status == "failed"
            self.calls += r.usage.calls
            self.cache_hits += r.usage.cache_hit
            self.input_tokens += r.usage.input_tokens
            self.output_tokens += r.usage.output_tokens
            self.cost_usd += r.usage.cost_usd
            self.list_cost_usd += r.usage.list_cost_usd
            self._latencies.append(r.usage.latency_ms)
            self._latencies = self._latencies[-5000:]

    def snapshot(self) -> dict:
        with self._lock:
            lat = sorted(self._latencies)
            q = (lambda p: lat[min(len(lat) - 1, int(p * len(lat)))]) if lat else (lambda p: None)
            return {
                "uptime_s": round(time.time() - self.started, 1), "documents": self.docs, "failed": self.failed,
                "llm_calls": self.calls, "cache_hits": self.cache_hits, "input_tokens": self.input_tokens,
                "output_tokens": self.output_tokens, "cost_usd": round(self.cost_usd, 6),
                "list_cost_usd": round(self.list_cost_usd, 6),
                "latency_ms": {"p50": q(0.5), "p95": q(0.95), "mean": round(statistics.fmean(lat), 1) if lat else None},
            }
