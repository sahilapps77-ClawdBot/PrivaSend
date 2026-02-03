"""PrivaSend configuration — environment variables with defaults."""

import os

# ---------------------------------------------------------------------------
# Confidence bucketing thresholds (for user review UI)
# ---------------------------------------------------------------------------

CONFIDENCE_HIGH = 0.85  # >= this: pre-checked in UI (high confidence)
CONFIDENCE_LOW = 0.50   # < this: ignored (low confidence)
# Between CONFIDENCE_LOW and CONFIDENCE_HIGH: shown for review (medium confidence)

# ---------------------------------------------------------------------------
# LLM validation toggle (disabled for MVP)
# ---------------------------------------------------------------------------

USE_LLM_VALIDATION = os.getenv("USE_LLM_VALIDATION", "false").lower() == "true"

# ---------------------------------------------------------------------------
# OpenRouter API settings (for Send to AI feature)
# ---------------------------------------------------------------------------

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# ---------------------------------------------------------------------------
# Legacy: Ollama LLM settings (kept for future use, disabled by default)
# ---------------------------------------------------------------------------

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3:8b")

# LLM validation thresholds — only validate entities in this confidence band
LLM_CONFIDENCE_LOW = 0.60
LLM_CONFIDENCE_HIGH = 0.85

# Redaction threshold — entities below this final confidence are left as-is
REDACTION_THRESHOLD = 0.65

# Context window — chars each side of entity sent to LLM
LLM_CONTEXT_CHARS = 50

# LLM request timeout in seconds (per entity)
LLM_TIMEOUT = 15.0

# Total time budget for all LLM calls in one request (seconds)
LLM_TOTAL_BUDGET = 45.0
