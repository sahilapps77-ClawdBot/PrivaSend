"""PrivaSend — FastAPI server for PII detection and redaction."""

from __future__ import annotations

import logging
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from tools.detect_pii import detect, DetectedEntity, PIIType
from tools.redact import redact, deredact, RedactionResult

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("privasend")

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(
    title="PrivaSend",
    description="PII detection and redaction API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

MAX_TEXT_LENGTH = 100_000


class TextInput(BaseModel):
    text: str = Field(..., min_length=1, max_length=MAX_TEXT_LENGTH)


class EntityOut(BaseModel):
    start: int
    end: int
    pii_type: str
    value: str
    confidence: float
    source: str
    pre_llm_confidence: float | None = None
    llm_validated: bool = False


class AnalyzeResponse(BaseModel):
    entities: list[EntityOut]
    count: int
    elapsed_ms: float


class RedactResponse(BaseModel):
    redacted_text: str
    mapping: dict[str, str]
    entities: list[EntityOut]
    entity_count: int
    elapsed_ms: float


class DeredactInput(BaseModel):
    text: str = Field(..., min_length=1, max_length=MAX_TEXT_LENGTH)
    mapping: dict[str, str]


class DeredactResponse(BaseModel):
    original_text: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def api_analyze(body: TextInput):
    """Detect PII entities in the given text."""
    log.info("POST /api/analyze  len=%d", len(body.text))
    t0 = time.perf_counter()

    entities = detect(body.text, use_presidio=True, use_llm=True)

    elapsed = (time.perf_counter() - t0) * 1000
    log.info("  detected %d entities in %.0f ms", len(entities), elapsed)

    return AnalyzeResponse(
        entities=[
            EntityOut(
                start=e.start,
                end=e.end,
                pii_type=e.pii_type.value,
                value=e.value,
                confidence=e.confidence,
                source=e.source.value,
                pre_llm_confidence=e.pre_llm_confidence,
                llm_validated=e.llm_validated,
            )
            for e in entities
        ],
        count=len(entities),
        elapsed_ms=round(elapsed, 1),
    )


@app.post("/api/redact", response_model=RedactResponse)
async def api_redact(body: TextInput):
    """Detect and redact PII, returning redacted text + mapping."""
    log.info("POST /api/redact  len=%d", len(body.text))
    t0 = time.perf_counter()

    entities = detect(body.text, use_presidio=True, use_llm=True)
    result = redact(body.text, entities)

    elapsed = (time.perf_counter() - t0) * 1000
    log.info("  redacted %d entities in %.0f ms", result.entity_count, elapsed)

    return RedactResponse(
        redacted_text=result.redacted_text,
        mapping=result.mapping,
        entities=[
            EntityOut(
                start=e.start,
                end=e.end,
                pii_type=e.pii_type.value,
                value=e.value,
                confidence=e.confidence,
                source=e.source.value,
                pre_llm_confidence=e.pre_llm_confidence,
                llm_validated=e.llm_validated,
            )
            for e in entities
        ],
        entity_count=result.entity_count,
        elapsed_ms=round(elapsed, 1),
    )


@app.post("/api/deredact", response_model=DeredactResponse)
async def api_deredact(body: DeredactInput):
    """Restore original values from redacted text + mapping."""
    log.info("POST /api/deredact  len=%d", len(body.text))
    restored = deredact(body.text, body.mapping)
    return DeredactResponse(original_text=restored)


@app.get("/api/health")
async def health():
    import httpx
    from tools.config import OLLAMA_URL
    ollama_ok = False
    try:
        r = httpx.get(f"{OLLAMA_URL}/", timeout=2.0)
        ollama_ok = r.status_code == 200
    except Exception:
        pass
    return {"status": "ok", "ollama_url": OLLAMA_URL, "ollama_reachable": ollama_ok}


# ---------------------------------------------------------------------------
# Static files — serve frontend
# ---------------------------------------------------------------------------

app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
