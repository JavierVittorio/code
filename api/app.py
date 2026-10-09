"""HTTP API.

POST /extract          multipart file           -> ExtractionResult
POST /extract/batch    multipart files[]        -> {results: [...], summary: {...}}
GET  /health           liveness + config fingerprint
GET  /metrics          cumulative tokens / cost / latency
"""
from __future__ import annotations

import logging
import time

from fastapi import FastAPI, File, HTTPException, UploadFile

from docext.batch import Metrics, extract_many
from docext.config import get_settings
from docext.extract import Extractor
from docext.prompts import PROMPT_VERSION
from docext.schema import ExtractionResult

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
settings = get_settings()
extractor = Extractor(settings)
metrics = Metrics()
app = FastAPI(title="docext - invoice extraction", version="1.0")

MAX_BYTES = 25 * 1024 * 1024
MAX_BATCH = 50


async def _read(f: UploadFile) -> bytes:
    data = await f.read()
    if not data:
        raise HTTPException(400, f"{f.filename}: empty file")
    if len(data) > MAX_BYTES:
        raise HTTPException(413, f"{f.filename}: larger than {MAX_BYTES // 2**20} MB")
    return data


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "model": settings.model, "prompt_version": PROMPT_VERSION,
            "image_profile": settings.image_profile, "config_fingerprint": settings.fingerprint(),
            "api_key_configured": bool(settings.api_key)}


@app.get("/metrics")
def get_metrics() -> dict:
    return metrics.snapshot()


@app.post("/extract", response_model=ExtractionResult)
async def extract(file: UploadFile = File(...)) -> ExtractionResult:
    data = await _read(file)
    r = await extractor.extract(data, file.filename or "", file.filename)
    metrics.record(r)
    return r


@app.post("/extract/batch")
async def extract_batch(files: list[UploadFile] = File(...)) -> dict:
    if len(files) > MAX_BATCH:
        raise HTTPException(413, f"at most {MAX_BATCH} files per batch")
    docs = [(f.filename or f"doc{i}", await _read(f), f.filename or "") for i, f in enumerate(files)]
    t0 = time.perf_counter()
    results = await extract_many(extractor, docs, settings.max_concurrency)
    for r in results:
        metrics.record(r)
    wall = (time.perf_counter() - t0) * 1000
    return {
        "results": [r.model_dump(mode="json") for r in results],
        "summary": {
            "documents": len(results), "failed": sum(r.status == "failed" for r in results),
            "wall_ms": round(wall, 1), "sum_latency_ms": round(sum(r.usage.latency_ms for r in results), 1),
            "input_tokens": sum(r.usage.input_tokens for r in results),
            "output_tokens": sum(r.usage.output_tokens for r in results),
            "cost_usd": round(sum(r.usage.cost_usd for r in results), 6),
            "list_cost_usd": round(sum(r.usage.list_cost_usd for r in results), 6),
        },
    }
