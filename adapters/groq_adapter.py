import os
import requests
import json

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DEFAULT_MODEL = os.getenv("GROQ_MODEL", "openai-oss-20b")
GROQ_CHAT_URL = os.getenv("GROQ_CHAT_URL", "https://api.groq.com/openai/v1/chat/completions")

def groq_chat(messages, model: str = DEFAULT_MODEL, temperature=0.2, max_tokens=512, timeout=30):
    """
    Universal Groq adapter for OSS 20B or any Groq-supported model.
    messages: list of {"role":"system"|"user"|"assistant","content":"..."}
    returns: dict with at least {"role": "...", "content": "..."} for the chosen message
    """
    if not GROQ_API_KEY:
        # local mock
        last = messages[-1]["content"] if messages else ""
        return {"role": "assistant", "content": "[groq-mock] " + last[:400]}

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    resp = requests.post(GROQ_CHAT_URL, json=payload, headers=headers, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    # return first choice message
    try:
        msg = data["choices"][0]["message"]
        # ensure consistent structure
        if isinstance(msg, dict) and "content" in msg:
            return {"role": msg.get("role", "assistant"), "content": msg["content"]}
        # some endpoints return different shapes
        return {"role": "assistant", "content": json.dumps(msg)}
    except Exception:
        return {"role": "assistant", "content": json.dumps(data)}
