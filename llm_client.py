import os
import json
import requests
from typing import Any, Dict, Optional

# Try to import official openai client for fallback
try:
    import openai
except Exception:
    openai = None  # not required if using Groq

# Environment keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Model names - Groq OpenAI-compatible uses "openai/gpt-oss-120b" to reference GPT-OSS 120B
GROQ_MODEL = "openai/gpt-oss-120b"
OPENAI_MODEL = "gpt-4o-mini"  # fallback default if OPENAI used; change if you have another model

# Groq OpenAI-compatible endpoint (chat completions)
GROQ_OPENAI_COMPAT_URL = "https://api.groq.com/openai/v1/chat/completions"


def _call_groq_chat(prompt: str, model: str = GROQ_MODEL, max_tokens: int = 800, temperature: float = 0.0) -> Dict[str, Any]:
    """
    Call Groq's OpenAI-compatible Chat Completions endpoint using requests.
    Returns the parsed content (text) and raw response dict.
    """
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not set")

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    resp = requests.post(GROQ_OPENAI_COMPAT_URL, headers=headers, data=json.dumps(payload), timeout=120)
    resp.raise_for_status()
    data = resp.json()

    # Groq returns an OpenAI-compatible response structure for chat completions; extract message content if present
    text = None
    try:
        text = data["choices"][0]["message"]["content"]
    except Exception:
        # fallback: stringified raw response
        text = json.dumps(data)

    return {"mock": False, "text": text, "raw": data}


def _call_openai_chat(prompt: str, model: str = OPENAI_MODEL, max_tokens: int = 800, temperature: float = 0.0) -> Dict[str, Any]:
    """
    Call official OpenAI ChatCompletion as fallback.
    Requires openai package and OPENAI_API_KEY set in environment.
    """
    if not OPENAI_API_KEY or openai is None:
        raise RuntimeError("OPENAI_API_KEY not set or openai client unavailable")

    openai.api_key = OPENAI_API_KEY
    resp = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=temperature,
    )

    # extract text safely
    try:
        text = resp["choices"][0]["message"]["content"]
    except Exception:
        text = str(resp)

    return {"mock": False, "text": text, "raw": resp}


def make_llm_call(prompt: str, max_tokens: int = 800, temperature: float = 0.0) -> Dict[str, Any]:
    """
    Universal wrapper used by the orchestrator.
    Priority:
      1) GROQ_API_KEY -> call Groq OpenAI-compatible endpoint with gpt-oss-120b
      2) OPENAI_API_KEY -> call OpenAI ChatCompletion (fallback)
      3) No keys -> return a mocked response for demo purposes.
    """
    # 1) Try Groq
    if GROQ_API_KEY:
        try:
            return _call_groq_chat(prompt, model=GROQ_MODEL, max_tokens=max_tokens, temperature=temperature)
        except Exception as e:
            # if Groq call fails unexpectedly, try fallback to OpenAI (if available)
            fallback_err = str(e)
            if OPENAI_API_KEY and openai is not None:
                try:
                    res = _call_openai_chat(prompt, model=OPENAI_MODEL, max_tokens=max_tokens, temperature=temperature)
                    res["fallback_from"] = {"groq_error": fallback_err}
                    return res
                except Exception:
                    # fall through to mocked response
                    pass
            return {"mock": True, "text": f"Groq call failed: {fallback_err}", "raw": {"error": fallback_err}}

    # 2) Try OpenAI official
    if OPENAI_API_KEY and openai is not None:
        try:
            return _call_openai_chat(prompt, model=OPENAI_MODEL, max_tokens=max_tokens, temperature=temperature)
        except Exception as e:
            return {"mock": True, "text": f"OpenAI call failed: {str(e)}", "raw": {"error": str(e)}}

    # 3) No API keys; return mock response
    demo_text = (
        "Demo mode (no GROQ_API_KEY or OPENAI_API_KEY found). "
        "Set GROQ_API_KEY to call Groq with gpt-oss-120b or OPENAI_API_KEY to use OpenAI."
    )
    return {"mock": True, "text": demo_text, "raw": None}
