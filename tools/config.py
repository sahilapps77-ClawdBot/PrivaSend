"""PrivaSend configuration — environment variables with defaults."""

import os

# Ollama LLM settings
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
