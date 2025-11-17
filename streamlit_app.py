import streamlit as st
import requests, os, time, json

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")
API_KEY = os.getenv("MCP_API_KEY", "dev-local-key")
st.set_page_config(page_title="MCP Stock Analyzer", layout="wide")
st.title("MCP Stock Analyzer (Groq OSS-20B)")

st.markdown("Edit the system prompt. This prompt is injected as highest-priority context for the analyzers.")

default_system_prompt = (
    "You are an evidence-first financial research assistant. Use the envelope and include citations. "
    "Produce structured JSON for technical and fundamental analysis."
)

system_prompt = st.text_area("System prompt", value=default_system_prompt, height=160)
symbols_input = st.text_input("Symbols (comma-separated)", value="AAPL, TSLA")
symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]
query = st.text_area("Query", value="Provide technical + fundamental analysis.")
workflow = st.selectbox("Workflow", ["stock-analysis"])
analyze_btn = st.button("Analyze")

st.markdown("Quick LLM test (compose) — uses Groq via server `/llm/compose`")
compose_prompt = st.text_area("LLM prompt (for quick test)", value="Summarize Apple's latest earnings in one paragraph.")
compose_model = st.text_input("compose model (optional)", value="openai-oss-20b")
if st.button("Run LLM compose"):
    headers = {"X-API-KEY": API_KEY}
    messages = [{"role":"system","content":system_prompt},{"role":"user","content":compose_prompt}]
    try:
        r = requests.post(API_BASE + "/llm/compose", json={"messages": messages, "model": compose_model}, headers=headers, timeout=60)
        st.json(r.json())
    except Exception as e:
        st.error(str(e))

if analyze_btn:
    payload = {
        "id": "ui-" + str(int(time.time() * 1000)),
        "system_prompt": system_prompt,
        "query": query,
        "symbols": symbols,
        "workflow": workflow
    }
    headers = {"X-API-KEY": API_KEY}
    try:
        r = requests.post(API_BASE + "/mcp/analyze", json=payload, headers=headers, timeout=120)
    except Exception as e:
        st.error(f"Request failed: {e}")
        st.stop()

    if not r.ok:
        st.error(f"Server error: {r.status_code} {r.text}")
        st.stop()

    data = r.json()
    st.subheader("Audit")
    st.write("audit_hash:", data.get("audit_hash"))
    st.subheader("Step logs")
    for s in data.get("steps", []):
        st.markdown(f"**{s.get('step')}**")
        st.code(json.dumps(s.get("detail"), default=str, indent=2)[:2000])
    st.subheader("Final analysis (LangGraph/Groq fallback)")
    st.json(data.get("langgraph"))
    st.subheader("Final analysis (Raw)")
    st.code(json.dumps(data.get("langgraph"), indent=2))
