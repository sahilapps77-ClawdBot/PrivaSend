"""
OpenRouter API client for sending redacted prompts to AI models.

OpenRouter provides a unified API for multiple AI providers:
- OpenAI (GPT-4o, GPT-4o-mini)
- Anthropic (Claude 3.5 Sonnet)
- Google (Gemini Pro)
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from tools.config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL

log = logging.getLogger("privasend.openrouter")

# Supported models with display names
MODELS: dict[str, str] = {
    "openai/gpt-4o-mini": "GPT-4o Mini (Fast)",
    "openai/gpt-4o": "GPT-4o (Best)",
    "anthropic/claude-3.5-sonnet": "Claude 3.5 Sonnet",
    "google/gemini-pro": "Gemini Pro",
}


class OpenRouterError(Exception):
    """Raised when OpenRouter API call fails."""

    def __init__(self, message: str, status_code: int | None = None, response: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


async def send_prompt(
    prompt: str,
    model: str = "openai/gpt-4o-mini",
    api_key: str | None = None,
    timeout: float = 60.0,
    system_prompt: str | None = None,
) -> str:
    """
    Send a prompt to OpenRouter and return the AI response.

    Args:
        prompt: The user prompt to send.
        model: OpenRouter model ID (e.g., "openai/gpt-4o-mini").
        api_key: Optional API key. Falls back to OPENROUTER_API_KEY env var.
        timeout: Request timeout in seconds.
        system_prompt: Optional system prompt to set context.

    Returns:
        The AI's response text.

    Raises:
        OpenRouterError: If the API call fails.
        ValueError: If no API key is configured.
    """
    key = api_key or OPENROUTER_API_KEY
    if not key:
        raise ValueError(
            "No OpenRouter API key configured. "
            "Set OPENROUTER_API_KEY in .env or pass api_key parameter."
        )

    # Validate API key format (OpenRouter keys start with sk-or-v1-)
    if not key.startswith("sk-or-v1-"):
        raise ValueError("Invalid API key format. OpenRouter keys start with 'sk-or-v1-'.")

    # Log key source (not the key itself)
    log.info("Using %s OpenRouter key", "user-provided" if api_key else "server")

    # Build messages array
    messages: list[dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    log.info("Sending request to OpenRouter: model=%s, prompt_len=%d", model, len(prompt))

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {key}",
                    "HTTP-Referer": "https://privasend.app",
                    "X-Title": "PrivaSend",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                },
                timeout=timeout,
            )

            if response.status_code != 200:
                error_body = _safe_json(response)
                error_msg = error_body.get("error", {}).get("message", response.text)
                log.error("OpenRouter error: status=%d, message=%s", response.status_code, error_msg)
                raise OpenRouterError(
                    f"OpenRouter API error: {error_msg}",
                    status_code=response.status_code,
                    response=error_body,
                )

            data = response.json()
            content = data["choices"][0]["message"]["content"]
            log.info("OpenRouter response received: len=%d", len(content))
            return content

    except httpx.TimeoutException as e:
        log.error("OpenRouter timeout: %s", str(e))
        raise OpenRouterError(f"Request timed out after {timeout}s") from e
    except httpx.RequestError as e:
        log.error("OpenRouter request error: %s", str(e))
        raise OpenRouterError(f"Request failed: {str(e)}") from e


def _safe_json(response: httpx.Response) -> dict[str, Any]:
    """Safely parse JSON from response, returning empty dict on failure."""
    try:
        return response.json()
    except Exception:
        return {}


def get_available_models() -> dict[str, str]:
    """Return dictionary of available models: {model_id: display_name}."""
    return MODELS.copy()


def is_valid_model(model: str) -> bool:
    """Check if a model ID is valid."""
    return model in MODELS
