import os
import json
import requests

# Try to import streamlit to read st.secrets if available (only used for secret lookup)
try:
    import streamlit as _streamlit  # underscore to avoid using it broadly
except Exception:
    _streamlit = None

GROQ_MODEL = "openai/gpt-oss-120b"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

def _get_groq_key():
    """
    Returns tuple (key_or_None, source_string)
    source_string is 'env' if from env var, 'secrets' if from Streamlit secrets, or 'none'.
    """
    # 1) environment variable
    key = os.getenv("GROQ_API_KEY")
    if key:
        return key, "env"

    # 2) streamlit secrets (if running inside streamlit)
    if _streamlit is not None:
        try:
            s = _streamlit.secrets
            # st.secrets behaves like a dict; use get to avoid KeyError
            key = s.get("GROQ_API_KEY") if isinstance(s, dict) or hasattr(s, "get") else None
            # sometimes users put secrets nested under a key, try that
            if not key and "GROQ_API_KEY" in s:
                key = s["GROQ_API_KEY"]
            if key:
                return key, "secrets"
        except Exception:
            # swallow any streamlit secret access errors and continue
            pass

    return None, "none"

def make_llm_call(prompt: str, max_tokens: int = 800, temperature: float = 0.0):
    """
    Call Groq chat completion. If no key found, returns mock response.
    The returned dict includes a 'debug' field showing where (if anywhere) the key was found.
    """
    key, source = _get_groq_key()

    if not key:
        return {
            "mock": True,
            "text": "No GROQ_API_KEY set. Using mock response.",
            "raw": None,
            "debug": {"source": source}
        }

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }

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
        # If the HTTP request failed, return structured error but do NOT include the key
        return {
            "mock": True,
            "text": f"Groq request failed: {str(e)}",
            "raw": None,
            "debug": {"source": source, "error": str(e)}
        }

    # extract message content (OpenAI-compatible structure)
    try:
        text = data["choices"][0]["message"]["content"]
    except Exception:
        text = json.dumps(data)

    return {
        "mock": False,
        "text": text,
        "raw": data,
        "debug": {"source": source}
    }
