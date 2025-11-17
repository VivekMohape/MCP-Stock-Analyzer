import os
import json
import requests

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Groq OpenAI-compatible endpoint
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-120b"   # OSS-120 model

def make_llm_call(prompt: str, max_tokens=800, temperature=0.0):
    if not GROQ_API_KEY:
        return {
            "mock": True,
            "text": "No GROQ_API_KEY set. Using mock response.",
            "raw": None
        }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
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

    resp = requests.post(GROQ_URL, headers=headers, json=payload, timeout=120)
    data = resp.json()

    try:
        text = data["choices"][0]["message"]["content"]
    except:
        text = json.dumps(data)

    return {"mock": False, "text": text, "raw": data}
