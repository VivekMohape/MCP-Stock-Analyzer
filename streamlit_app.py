import streamlit as st
import os
from local_orchestrator import run_analysis
from audit_model import list_runs, get_trace

st.set_page_config(page_title="MCP Stock Analyzer — Groq (Diagnostics)", layout="wide")
st.title("📈 MCP Stock Analyzer")

# Display secret detection diagnostics (safe: does NOT reveal the secret)
def detect_and_show_groq():
    found_env = bool(os.getenv("GROQ_API_KEY"))
    found_secrets = False
    masked = None
    try:
        if hasattr(st, "secrets"):
            s = st.secrets
            # try common access patterns
            if isinstance(s, dict):
                key = s.get("GROQ_API_KEY")
            else:
                try:
                    key = s["GROQ_API_KEY"]
                except Exception:
                    key = s.get("GROQ_API_KEY") if hasattr(s, "get") else None
            if key:
                found_secrets = True
                masked = f"{key[:4]}... (len={len(key)})"
    except Exception:
        found_secrets = False

    col1, col2, col3 = st.columns(3)
    with col1:
        st.write("**GROQ key present in env:**", found_env)
    with col2:
        st.write("**GROQ key present in st.secrets:**", found_secrets)
    with col3:
        st.write("**Masked sample (st.secrets):**", masked if masked else "—")

    if not (found_env or found_secrets):
        st.warning("No GROQ_API_KEY detected. Add it under App → Settings → Secrets (value should be the raw key, no surrounding quotes). After adding, Redeploy the app.")
    else:
        st.success("GROQ_API_KEY detected (masked sample shown). If the app still returns 'mock', check probe diagnostics below.")

detect_and_show_groq()

st.markdown("---")
ticker = st.text_input("Enter stock ticker", "AAPL")
period = st.selectbox("History period", ["1mo", "3mo", "6mo"], index=0)

col_left, col_right = st.columns([2,1])

with col_left:
    if st.button("Run MCP Pipeline"):
        with st.spinner("Running MCP Orchestrator..."):
            resp = run_analysis(ticker, {"period": period})

        st.success("Run finished (see results)")

        st.subheader("LLM Final Output / Diagnostic")
        llm = resp.get("result")
        if isinstance(llm, dict) and llm.get("mock"):
            st.error("LLM returned a mock response (no key or probe failed).")
            st.text(llm.get("text"))
            st.write("Debug info (safe):")
            st.json(llm.get("debug"))
        else:
            # good path
            if isinstance(llm, dict) and "text" in llm:
                st.write(llm["text"])
                st.write("Debug info (safe):")
                st.json(llm.get("debug"))
            else:
                st.json(llm)

        st.subheader("Full MCP Trace")
        for i, step in enumerate(resp.get("trace", [])):
            with st.expander(f"Step {i+1}: {step['name']} ({step['tool']})"):
                st.json(step)

with col_right:
    st.subheader("Past Runs / Audit (ephemeral)")
    runs = list_runs()
    if not runs:
        st.info("No past runs in DB yet.")
    for r in runs:
        with st.expander(f"{r['run_id']} ({r['steps']} steps)"):
            trace = get_trace(r['run_id'])
            st.json(trace)

st.markdown("---")
st.caption("If the key is present but probe fails, check app logs (Manage app → Logs) for HTTP errors (401 = invalid key, 403 = forbidden, 429 = rate limit). If you added the secret after deployment, press Redeploy in Streamlit Cloud.")
