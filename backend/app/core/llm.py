"""LLM client for OpenAI-compatible APIs (OpenRouter, Bluesminds, etc.).
"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

from openai import OpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: OpenAI | None = None

# Free models available on OpenRouter (Jun 2026) — highest quality first
_FALLBACK_MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "qwen/qwen3-coder:free",
    "openai/gpt-oss-120b:free",
    "nousresearch/hermes-3-llama-3.1-405b:free",
    "meta-llama/llama-3.2-3b-instruct:free",
]


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        key = settings.openrouter_api_key or settings.gemini_api_key
        if not key:
            raise RuntimeError(
                "No API key found. Set OPENROUTER_API_KEY in backend/.env"
            )
        _client = OpenAI(
            base_url=settings.openrouter_base_url,
            api_key=key,
            default_headers={
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "ATS Resume Optimizer",
            },
        )
    return _client


def _is_retryable(e: Exception) -> bool:
    msg = str(e)
    return (
        "429" in msg
        or "rate limit" in msg.lower()
        or "quota" in msg.lower()
        or "502" in msg
        or "503" in msg
    )


def _call_with_retry(
    messages: list[dict[str, str]],
    temperature: float = 0.4,
    json_mode: bool = True,
) -> str:
    """Call OpenRouter with retry + model fallback + JSON-mode fallback."""
    client = _get_client()

    models_to_try = [settings.model_name]
    # Only use fallback models with default OpenRouter URL
    if settings.openrouter_base_url == "https://openrouter.ai/api/v1":
        for m in _FALLBACK_MODELS:
            if m not in models_to_try:
                models_to_try.append(m)

    # Two formats to try: with response_format (json) and without (prompt-based)
    formats: list[dict | None] = [{"type": "json_object"}] if json_mode else [None]
    formats.append(None)  # always fall back to prompt-based JSON

    last_error: Exception | None = None

    for attempt in range(10):
        model_idx = attempt // 3  # 3 tries per model (with json, without, retry)
        if model_idx >= len(models_to_try):
            break
        model = models_to_try[model_idx]
        fmt_idx = attempt % 3

        kwargs: dict[str, Any] = {"temperature": temperature}
        if fmt_idx == 0 and json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        else:
            kwargs.pop("response_format", None)

        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                **kwargs,
            )
            text = (response.choices[0].message.content or "").strip()
            if text:
                return text
        except Exception as e:
            last_error = e
            if _is_retryable(e):
                delay = 5 + (attempt * 10)
                logger.warning(
                    "LLM retryable error on model=%s attempt=%d — retrying in %ds: %s",
                    model, attempt, delay, e,
                )
                time.sleep(delay)
                continue
            # Non-retryable (400 bad request, etc.) — try next format/model
            logger.warning("LLM non-retryable error on model=%s: %s", model, e)
            continue

    raise RuntimeError(
        f"OpenRouter request failed after all retries: {last_error}"
    ) from last_error


def _build_messages(prompt: str, system: str | None = None) -> list[dict[str, str]]:
    msgs: list[dict[str, str]] = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    return msgs


def generate_json(
    prompt: str,
    system: str | None = None,
    temperature: float = 0.4,
) -> dict[str, Any]:
    """Call OpenRouter and parse the response as JSON."""
    messages = _build_messages(prompt, system)
    text = _call_with_retry(messages, temperature, json_mode=True)

    return _parse_json_from_text(text, prompt, system, temperature)


def _parse_json_from_text(
    text: str,
    original_prompt: str,
    system: str | None = None,
    temperature: float = 0.4,
    max_retries: int = 2,
) -> dict[str, Any]:
    """Aggressively parse JSON from LLM response text with retries."""
    last_error: Exception | None = None

    for attempt in range(max_retries + 1):
        raw = text
        cleaned = raw

        # 1. Strip markdown fences
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned).strip()

        # 2. Strip control characters (except newlines/tabs)
        cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", cleaned)

        # 3. Extract the first { ... } block
        brace_start = cleaned.find("{")
        brace_end = cleaned.rfind("}")
        if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
            cleaned = cleaned[brace_start : brace_end + 1]

        # 4. Try to parse
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            last_error = e
            if attempt < max_retries:
                logger.warning(
                    "JSON parse failed (attempt %d/%d), retrying without json_mode",
                    attempt + 1, max_retries,
                )
                msgs = _build_messages(original_prompt, system)
                text = _call_with_retry(msgs, temperature, json_mode=False)
                continue
            break

    logger.error("Failed to parse JSON after %d attempts. Raw:\n%s", max_retries + 1, text)
    raise RuntimeError(f"LLM returned invalid JSON: {last_error}") from last_error


def generate_text(
    prompt: str,
    system: str | None = None,
    temperature: float = 0.4,
) -> str:
    """Plain text generation."""
    messages = _build_messages(prompt, system)
    return _call_with_retry(messages, temperature, json_mode=False)
