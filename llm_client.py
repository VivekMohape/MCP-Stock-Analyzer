import os
import json
import requests
from typing import Dict, Any

# Groq endpoints / model
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-120b"

# Try to import streamlit to read secrets when running inside the Streamlit runtime
try:
    import streamlit as _st
except Exception:
    _st = None

def _get_key_from_env_or_secrets() -> (str, str):
    # 1) environment
    env_key = os.getenv("GROQ_API_KEY")
    if env_key:
        return env_key, "env"
    # 2) streamlit secrets (common in Streamlit Cloud)
    if _st is not None:
        try:
            # st.secrets supports mapping access; handle a few shapes safely
            s = _st.secrets
            # typical usage: st.secrets["GROQ_API_KEY"]
            if isinstance(s, dict):
                key = s.get("GROQ_API_KEY")
                if key:
                    return key, "secrets"
            else:
                # Some runtimes present st.secrets as a Secrets object with mapping behavior
                try:
                    key = s["GROQ_API_KEY"]
                    if key:
                        return key, "secrets"
                except Exception:
                    # fallback: attributes
                    if hasattr(s, "get"):
                        key = s.get("GROQ_API_KEY")
                        if key:
                            return key, "secrets"
        except Exception:
            # swallow but continue
            pass
    return None, "none"

def _mask_key(k: str) -> str:
    if not k:
        return ""
    # show prefix and length only, do not reveal remainder
    prefix = k[:4]
    return f"{prefix}... (len={len(k)})"

def _probe_groq_key(key: str, timeout: int = 10) -> Dict[str, Any]:
    """
    Do a minimal call to Groq to sanity-check key validity.
    We send a tiny prompt and return status or error.
    """
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": "You are a test assistant."},
            {"role": "user", "content": "ping"}
        ],
        "max_tokens": 10,
        "temperature": 0.0,
    }
    try:
        resp = requests.post(GROQ_URL, headers=headers, json=payload, timeout=timeout)
        # Return status code and limited body info (not full data)
        try:
            body = resp.json()
        except Exception:
            body = {"text": resp.text[:200]}
        return {"ok": resp.ok, "status_code": resp.status_code, "body_summary": (body if isinstance(body, dict) else str(body)[:200])}
    except Exception as e:
        return {"ok": False, "status_code": None, "error": str(e)}

def make_llm_call(prompt: str, max_tokens: int = 800, temperature: float = 0.0) -> Dict[str, Any]:
    # Find key
    key, source = _get_key_from_env_or_secrets()
    debug = {"found": bool(key), "source": source, "masked": _mask_key(key) if key else None}

    if not key:
        return {"mock": True, "text": "No GROQ_API_KEY set. Using mock response.", "raw": None, "debug": debug}

    # Probe the key once for diagnostics (this will consume a tiny amount of quota)
    probe = _probe_groq_key(key)
    debug["probe"] = probe

    # If probe indicates not ok, return diagnostic immediately (avoid full prompt)
    if not probe.get("ok"):
        return {"mock": True, "text": f"Groq key probe failed (status={probe.get('status_code')}). See debug.", "raw": None, "debug": debug}

    # Proceed to call the model for real
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": "You are a financial analyst."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    try:
        resp = requests.post(GROQ_URL, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return {"mock": True, "text": f"Groq request failed: {str(e)}", "raw": None, "debug": {"found": True, "source": source, "masked": _mask_key(key), "error": str(e)}}

    try:
        text = data["choices"][0]["message"]["content"]
    except Exception:
        text = json.dumps(data)[:10000]

    return {"mock": False, "text": text, "raw": data, "debug": debug}
