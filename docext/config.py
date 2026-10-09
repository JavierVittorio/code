"""Runtime configuration, read from environment (12-factor). One frozen object per process."""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from pathlib import Path

try:  # optional: local dev convenience; in Docker the env comes from compose
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover
    pass


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


def _default_threshold() -> str:
    """Explicit env wins; else the threshold chosen by tools/calibrate.py; else 0.5."""
    if "ABSTAIN_THRESHOLD" in os.environ:
        return os.environ["ABSTAIN_THRESHOLD"]
    try:
        return str(json.loads((Path(__file__).with_name("calibration.json")).read_text())["abstain_threshold"])
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        return "0.5"


@dataclass(frozen=True)
class Settings:
    base_url: str = field(default_factory=lambda: _env("LLM_BASE_URL", "https://openrouter.ai/api/v1"))
    api_key: str = field(default_factory=lambda: _env("LLM_API_KEY", "") or _env("OPENROUTER_API_KEY", ""), repr=False)
    model: str = field(default_factory=lambda: _env("LLM_MODEL", "google/gemma-4-31b-it:free"))
    fallback_models: tuple[str, ...] = field(
        default_factory=lambda: tuple(m.strip() for m in _env("LLM_FALLBACK_MODELS", "").split(",") if m.strip())
    )
    price_in_per_mtok: float = field(default_factory=lambda: float(_env("PRICE_IN_PER_MTOK", "0.25")))
    price_out_per_mtok: float = field(default_factory=lambda: float(_env("PRICE_OUT_PER_MTOK", "0.75")))
    max_concurrency: int = field(default_factory=lambda: int(_env("MAX_CONCURRENCY", "3")))
    timeout_s: float = field(default_factory=lambda: float(_env("LLM_TIMEOUT_S", "120")))
    max_retries: int = field(default_factory=lambda: int(_env("LLM_MAX_RETRIES", "4")))
    image_profile: str = field(default_factory=lambda: _env("IMAGE_PROFILE", "optimized"))
    output_format: str = field(default_factory=lambda: _env("OUTPUT_FORMAT", "verbose"))  # verbose | compact
    abstain_threshold: float = field(default_factory=lambda: float(_default_threshold()))
    cache_dir: str = field(default_factory=lambda: _env("CACHE_DIR", ".cache/llm"))
    cache_enabled: bool = field(default_factory=lambda: _env("CACHE_ENABLED", "1") == "1")
    max_pages: int = field(default_factory=lambda: int(_env("MAX_PAGES", "8")))

    def fingerprint(self) -> str:
        """Hash of every setting that can change extraction output (excludes secrets / plumbing)."""
        d = asdict(self)
        for k in ("api_key", "cache_dir", "cache_enabled", "max_concurrency", "timeout_s", "max_retries"):
            d.pop(k)
        return hashlib.sha256(json.dumps(d, sort_keys=True).encode()).hexdigest()[:12]

    def public(self) -> dict:
        d = asdict(self)
        d.pop("api_key")
        return d


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
