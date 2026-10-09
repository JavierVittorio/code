"""Thin async client for any OpenAI-compatible chat endpoint (OpenRouter, Gemini, Ollama, vLLM...).

Responsibilities: retries with backoff (429/5xx/timeouts), model fallback, JSON-mode negotiation,
usage + latency capture, and response caching. No extraction logic lives here.
"""
from __future__ import annotations

import asyncio
import logging
import random
import time
from dataclasses import dataclass, field

import openai
from openai import AsyncOpenAI

from .cache import DiskCache, payload_key
from .config import Settings

log = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    text: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    cache_hit: bool = False
    attempts: int = 1
    extra: dict = field(default_factory=dict)


class LLMError(RuntimeError):
    pass


class LLMClient:
    def __init__(self, settings: Settings, cache: DiskCache | None = None):
        self.s = settings
        self.cache = cache or DiskCache(settings.cache_dir, settings.cache_enabled)
        self._client = AsyncOpenAI(
            base_url=settings.base_url,
            api_key=settings.api_key or "not-needed",  # local servers (Ollama) ignore the key
            timeout=settings.timeout_s,
            max_retries=0,  # we own retry policy
        )
        # Models that rejected response_format once; don't send it again (per process).
        self._no_json_mode: set[str] = set()

    async def chat(self, messages: list[dict], *, temperature: float = 0.0, max_tokens: int = 4096,
                   use_cache: bool = True) -> LLMResponse:
        models = (self.s.model, *self.s.fallback_models)
        last_err: Exception | None = None
        for model in models:
            payload = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
            key = payload_key(payload)
            if use_cache and (hit := self.cache.get(key)):
                return LLMResponse(**{**hit, "cache_hit": True, "latency_ms": 0.0})
            try:
                resp = await self._call_with_retries(payload)
            except LLMError as e:
                last_err = e
                log.warning("model %s failed (%s); trying fallback", model, e)
                continue
            if use_cache:
                self.cache.set(key, {k: v for k, v in resp.__dict__.items() if k != "cache_hit"})
            return resp
        raise LLMError(f"all models failed: {last_err}")

    async def _call_with_retries(self, payload: dict) -> LLMResponse:
        delay = 2.0
        for attempt in range(1, self.s.max_retries + 2):
            t0 = time.perf_counter()
            try:
                kwargs = dict(payload)
                if payload["model"] not in self._no_json_mode:
                    kwargs["response_format"] = {"type": "json_object"}
                r = await self._client.chat.completions.create(**kwargs, extra_body={"usage": {"include": True}})
            except openai.BadRequestError as e:
                if "response_format" in kwargs and _mentions_json_mode(e):
                    self._no_json_mode.add(payload["model"])
                    continue
                raise LLMError(f"bad request: {e}") from e
            except (openai.RateLimitError, openai.APITimeoutError, openai.APIConnectionError,
                    openai.InternalServerError) as e:
                if attempt > self.s.max_retries:
                    raise LLMError(f"{type(e).__name__} after {attempt} attempts: {e}") from e
                wait = _retry_after(e) or delay * (0.75 + random.random() / 2)
                log.info("retryable %s (attempt %d); sleeping %.1fs", type(e).__name__, attempt, wait)
                await asyncio.sleep(wait)
                delay = min(delay * 2, 60)
                continue
            except openai.APIStatusError as e:  # 402/403/404 etc: not retryable on this model
                raise LLMError(f"HTTP {e.status_code}: {e}") from e

            latency = (time.perf_counter() - t0) * 1000
            if not r.choices:  # OpenRouter surfaces upstream errors as 200 with an error body
                err = getattr(r, "error", None) or (r.model_extra or {}).get("error")
                if attempt > self.s.max_retries:
                    raise LLMError(f"empty choices: {err}")
                await asyncio.sleep(delay)
                delay = min(delay * 2, 60)
                continue
            text = r.choices[0].message.content or ""
            u = r.usage
            in_tok = getattr(u, "prompt_tokens", 0) or 0
            out_tok = getattr(u, "completion_tokens", 0) or 0
            cost = float((u.model_extra or {}).get("cost", 0.0) or 0.0) if u is not None else 0.0
            return LLMResponse(text=text, model=r.model or payload["model"], input_tokens=in_tok,
                               output_tokens=out_tok, cost_usd=cost, latency_ms=latency, attempts=attempt,
                               extra={"finish_reason": r.choices[0].finish_reason})
        raise LLMError("retries exhausted")


def _mentions_json_mode(e: Exception) -> bool:
    s = str(e).lower()
    return "response_format" in s or "json" in s


def _retry_after(e: Exception) -> float | None:
    resp = getattr(e, "response", None)
    if resp is None:
        return None
    v = resp.headers.get("retry-after")
    try:
        return min(float(v), 90.0) if v else None
    except ValueError:
        return None
