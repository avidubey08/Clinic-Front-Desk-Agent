"""LLM Integration Layer for Sunrise Clinic Front Desk Agent.

Supports:
- Gemini (via GEMINI_API_KEY)
- OpenAI (via OPENAI_API_KEY)
- Groq (via GROQ_API_KEY)
- Fallback Deterministic Grounded Engine (when running offline or during runner.py tests)

Allows natural language conversation, intent proposal, and live chatting.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Optional


def call_gemini(prompt: str, api_key: str) -> Optional[str]:
    """Calls Gemini REST API directly using standard urllib."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.0,
            "maxOutputTokens": 800,
        },
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            candidates = data.get("candidates", [])
            if candidates:
                return candidates[0]["content"]["parts"][0]["text"]
    except Exception as e:
        print(f"Gemini API error: {e}")
    return None


def call_openai(messages: list[dict[str, str]], api_key: str) -> Optional[str]:
    """Calls OpenAI REST API directly using standard urllib."""
    url = "https://api.openai.com/v1/chat/completions"
    payload = {
        "model": "gpt-4o-mini",
        "messages": messages,
        "temperature": 0.0,
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"OpenAI API error: {e}")
    return None


def get_configured_model_name() -> str:
    """Returns the active model name for reporting in README and UI."""
    if os.environ.get("GEMINI_API_KEY"):
        return "Google Gemini 1.5 Flash"
    elif os.environ.get("OPENAI_API_KEY"):
        return "OpenAI GPT-4o-mini"
    elif os.environ.get("GROQ_API_KEY"):
        return "Groq Llama-3.3-70b"
    return "Sunrise Grounded Linguistic Engine (Deterministic Fallback)"
