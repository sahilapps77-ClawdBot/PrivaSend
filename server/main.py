"""PrivaSend — FastAPI server for PII detection and redaction."""

from __future__ import annotations

import io
import logging
import shutil
import tempfile
import time
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from tools.detect_pii import detect, bucket_entities, DetectedEntity, PIIType
from tools.redact import redact, deredact, RedactionResult
from tools.pii_categories import get_category, get_category_order
from tools.openrouter import send_prompt, get_available_models, OpenRouterError
from tools.file_extractor import extract_text_from_file, ExtractionError, UNSUPPORTED_TYPES

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

# CORS: Restrict to known origins
ALLOWED_ORIGINS = [
    "https://test.smcloud.cloud",
    "http://localhost:8000",
    "http://localhost:8100",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:8100",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
    allow_credentials=False,
)

# Rate limiting: protect expensive AI endpoints from abuse
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
# New models for review flow
# ---------------------------------------------------------------------------


class ReviewResponse(BaseModel):
    """Response with entities grouped by category for user review."""
    entities: list[EntityOut]
    categories: dict[str, list[int]]  # category name -> list of entity indices
    category_order: list[str]  # display order for categories
    high_confidence_indices: list[int]  # indices of entities >= 0.85 confidence
    elapsed_ms: float


class RedactSelectedInput(BaseModel):
    """Request to redact only selected entities."""
    text: str = Field(..., min_length=1, max_length=MAX_TEXT_LENGTH)
    selected_indices: list[int]


class SendToAIInput(BaseModel):
    """Request to redact and send to AI."""
    text: str = Field(..., min_length=1, max_length=MAX_TEXT_LENGTH)
    selected_indices: list[int]
    model: str = "openai/gpt-4o-mini"
    prompt: str = Field(..., min_length=1)
    api_key: str | None = None


class AIResponse(BaseModel):
    """Response from AI with redacted input."""
    redacted_input: str
    ai_response: str
    model_used: str
    elapsed_ms: float


class ModelsResponse(BaseModel):
    """Available AI models."""
    models: dict[str, str]  # model_id -> display_name


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
# New endpoints for review flow
# ---------------------------------------------------------------------------


@app.post("/api/analyze-for-review", response_model=ReviewResponse)
async def api_analyze_for_review(body: TextInput):
    """
    Detect PII and return entities grouped by category for user review.

    High-confidence entities (>= 0.85) are marked for pre-selection in the UI.
    LLM validation is disabled for this endpoint.
    """
    log.info("POST /api/analyze-for-review  len=%d", len(body.text))
    t0 = time.perf_counter()

    # Detect without LLM validation
    entities = detect(body.text, use_presidio=True, use_llm=False)

    # Group entity indices by category
    categories: dict[str, list[int]] = {}
    high_confidence_indices: list[int] = []

    for i, e in enumerate(entities):
        cat = get_category(e.pii_type)
        categories.setdefault(cat, []).append(i)

        # Track high-confidence entities for pre-selection
        if e.confidence >= 0.85:
            high_confidence_indices.append(i)

    elapsed = (time.perf_counter() - t0) * 1000
    log.info("  analyzed %d entities in %.0f ms", len(entities), elapsed)

    return ReviewResponse(
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
        categories=categories,
        category_order=get_category_order(),
        high_confidence_indices=high_confidence_indices,
        elapsed_ms=round(elapsed, 1),
    )


@app.post("/api/redact-selected", response_model=RedactResponse)
async def api_redact_selected(body: RedactSelectedInput):
    """
    Redact only the entities selected by the user.

    This endpoint re-detects entities to ensure consistency,
    then filters to only the selected indices.
    """
    log.info("POST /api/redact-selected  len=%d, selected=%d", len(body.text), len(body.selected_indices))
    t0 = time.perf_counter()

    # Re-detect to get entities (ensures consistency)
    entities = detect(body.text, use_presidio=True, use_llm=False)

    # Filter to only selected entities
    selected_indices = set(body.selected_indices)
    selected_entities = [
        entities[i] for i in range(len(entities))
        if i in selected_indices
    ]

    # Redact only selected
    result = redact(body.text, selected_entities)

    elapsed = (time.perf_counter() - t0) * 1000
    log.info("  redacted %d of %d entities in %.0f ms", len(selected_entities), len(entities), elapsed)

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
            for e in selected_entities
        ],
        entity_count=result.entity_count,
        elapsed_ms=round(elapsed, 1),
    )


@app.post("/api/send-to-ai", response_model=AIResponse)
@limiter.limit("10/minute")
async def api_send_to_ai(request: Request, body: SendToAIInput):
    """
    Redact selected entities and send to AI via OpenRouter.

    1. Re-detect and filter to selected entities
    2. Redact the text
    3. Send redacted text + user prompt to AI
    4. Return AI response
    """
    log.info("POST /api/send-to-ai  len=%d, model=%s", len(body.text), body.model)
    t0 = time.perf_counter()

    # Re-detect and filter to selected
    entities = detect(body.text, use_presidio=True, use_llm=False)
    selected_indices = set(body.selected_indices)
    selected_entities = [
        entities[i] for i in range(len(entities))
        if i in selected_indices
    ]

    # Redact
    result = redact(body.text, selected_entities)

    # Build full prompt with redacted text
    full_prompt = f"{body.prompt}\n\n---\n\n{result.redacted_text}"

    # Send to AI
    try:
        ai_response = await send_prompt(
            prompt=full_prompt,
            model=body.model,
            api_key=body.api_key,
        )
    except OpenRouterError as e:
        log.error("OpenRouter error: %s", str(e))
        raise HTTPException(
            status_code=e.status_code or 500,
            detail=str(e),
        )
    except ValueError as e:
        log.error("Configuration error: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))

    elapsed = (time.perf_counter() - t0) * 1000
    log.info("  AI response received in %.0f ms", elapsed)

    return AIResponse(
        redacted_input=result.redacted_text,
        ai_response=ai_response,
        model_used=body.model,
        elapsed_ms=round(elapsed, 1),
    )


@app.get("/api/models", response_model=ModelsResponse)
async def api_get_models():
    """Get available AI models for the Send to AI feature."""
    return ModelsResponse(models=get_available_models())


# ---------------------------------------------------------------------------
# File upload endpoint
# ---------------------------------------------------------------------------

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@app.post("/api/upload")
async def api_upload_file(
    file: UploadFile = File(...),
):
    """
    Upload and extract text from PDF, DOCX, TXT, or image files.
    
    Returns extracted text which can then be sent to /api/analyze-for-review
    """
    log.info("POST /api/upload  filename=%s content_type=%s", file.filename, file.content_type)
    
    # Check file type
    content_type = file.content_type
    if content_type not in SUPPORTED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {content_type}. Supported: {', '.join(SUPPORTED_TYPES.keys())}"
        )
    
    # Read file content
    try:
        file_bytes = await file.read()
    except Exception as e:
        log.error("Failed to read uploaded file: %s", e)
        raise HTTPException(status_code=400, detail="Could not read file")
    
    # Check file size
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large: {len(file_bytes)} bytes. Max: {MAX_FILE_SIZE} bytes (10MB)"
        )
    
    # Extract text
    t0 = time.perf_counter()
    try:
        extracted_text = extract_text_from_file(file_bytes, content_type)
    except ExtractionError as e:
        log.error("Extraction failed: %s", e)
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        log.error("Unexpected extraction error: %s", e)
        raise HTTPException(status_code=500, detail="Failed to extract text from file")
    
    elapsed = (time.perf_counter() - t0) * 1000
    log.info("  extracted %d chars in %.0f ms", len(extracted_text), elapsed)
    
    # Check if we got any text
    if not extracted_text or not extracted_text.strip():
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "filename": file.filename,
                "content_type": content_type,
                "text": "",
                "char_count": 0,
                "warning": "No text found in file. It may be a scanned image without OCR support or an empty document.",
                "elapsed_ms": round(elapsed, 1),
            }
        )
    
    return {
        "success": True,
        "filename": file.filename,
        "content_type": content_type,
        "text": extracted_text,
        "char_count": len(extracted_text),
        "elapsed_ms": round(elapsed, 1),
    }


# ---------------------------------------------------------------------------
# Static files — serve frontend
# ---------------------------------------------------------------------------

app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
