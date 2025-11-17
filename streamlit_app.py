import streamlit as st
from local_orchestrator import run_analysis
from audit_model import list_runs, get_trace
import os

st.set_page_config(page_title="MCP Stock Analyzer — Groq", layout="wide")
st.title("📈 MCP Stock Analyzer")

# --- Diagnostic: detect GROQ key sources ---
def detect_groq_source():
    env = bool(os.getenv("GROQ_API_KEY"))
    secrets_source = None
    try:
        # streamlit.secrets is available in the Streamlit runtime
        if hasattr(st, "secrets"):
            # st.secrets could be a dict-like; check presence without revealing value
            if st.secrets.get("GROQ_API_KEY"):
                secrets_source = True
    except Exception:
        secrets_source = None
    if env:
        return "env"
    if secrets_source:
        return "secrets"
    return "none"

groq_source = detect_groq_source()
if groq_source == "env":
    st.toast("GROQ_API_KEY found in environment variables.", icon="🔒")
elif groq_source == "secrets":
    st.toast("GROQ_API_KEY found in Streamlit secrets.", icon="🔑")
else:
    st.warning("No GROQ API key detected. Add GROQ_API_KEY to Streamlit Secrets (recommended) or environment variables.")

# UI controls
ticker = st.text_input("Enter stock ticker", "AAPL")
period = st.selectbox("History period", ["1mo", "3mo", "6mo"], index=0)

col1, col2 = st.columns([2,1])

with col1:
    if st.button("Run MCP Pipeline"):
        with st.spinner("Running MCP Orchestrator..."):
            resp = run_analysis(ticker, {"period": period})

        # show if it was a mock or real response
        debug = resp.get("result", {}).get("debug") or (resp.get("result") if isinstance(resp.get("result"), dict) else None)
        is_mock = False
        try:
            is_mock = resp["result"].get("mock", False) if isinstance(resp.get("result"), dict) else False
        except Exception:
            is_mock = False

        st.success("Analysis complete!")

        st.subheader("LLM Final Output")
        # resp["result"] could be the llm_resp dict returned from make_llm_call
        llm_result = resp.get("result")
        if isinstance(llm_result, dict) and llm_result.get("mock"):
            st.error("LLM returned a mock response (no key or an error). See debug below.")
            st.text(llm_result.get("text"))
            st.write("Debug:", llm_result.get("debug"))
        else:
            # if llm_result is the structured object with text
            if isinstance(llm_result, dict) and "text" in llm_result:
                st.write(llm_result["text"])
            else:
                # fallback: display raw
                st.json(llm_result)

        st.subheader("Full MCP Trace")
        for i, step in enumerate(resp["trace"]):
            with st.expander(f"Step {i+1}: {step['name']} ({step['tool']})"):
                st.json(step)

with col2:
    st.subheader("Past Runs")
    runs = list_runs()
    if not runs:
        st.info("No past runs in this session (audit DB is ephemeral on Streamlit Cloud).")
    for r in runs:
        with st.expander(f"{r['run_id']} ({r['steps']} steps)"):
            trace = get_trace(r["run_id"])
            st.json(trace)

st.markdown("---")
st.markdown(
    "Troubleshooting:\n\n"
    "- If the message says no GROQ key is found, make sure you set **GROQ_API_KEY** under **App -> Settings -> Secrets** in Streamlit Cloud, then click **Deploy / Redeploy**.\n"
    "- If you added the secret after the app was deployed, press **Deploy -> Redeploy** or push a tiny commit to force a restart.\n"
    "- Check app logs (Manage app -> Logs) for HTTP errors from Groq (401/403 = invalid key, 429 = rate limit)."
)
