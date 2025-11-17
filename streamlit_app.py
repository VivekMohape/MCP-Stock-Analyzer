# streamlit_app.py
import streamlit as st
from local_orchestrator import run_analysis
from audit_model import get_trace, list_runs
import json
from utils import make_run_id

st.set_page_config(page_title="MCP Stock Analyzer (Local)", layout="wide")
st.title("MCP Stock Analyzer — Local Orchestrator (No LangGraph, No Render)")

with st.sidebar:
    st.header("Run Controls")
    history_period = st.selectbox("History period", ["1mo", "3mo", "6mo"], index=0)
    show_recent = st.checkbox("Show recent runs", value=True)

col1, col2 = st.columns([2,1])

with col1:
    st.subheader("Start Analysis")
    ticker = st.text_input("Ticker (e.g. AAPL)", value="AAPL")
    if st.button("Run MCP Analysis"):
        if not ticker.strip():
            st.error("Enter a ticker")
        else:
            params = {"period": history_period}
            with st.spinner("Running local orchestration..."):
                resp = run_analysis(ticker.strip(), params)
            st.success("Run complete")
            st.markdown("### Result (LLM)")
            st.json(resp["result"].get("analysis"))

            st.markdown("### Full MCP Trace")
            for i, step in enumerate(resp["trace"]):
                label = f"Step {i+1}: {step['name']} — {step['tool']} ({step['duration']:.2f}s)"
                with st.expander(label, expanded=(i==len(resp["trace"])-1)):
                    st.markdown("**Input**")
                    st.json(step.get("input"))
                    st.markdown("**Output (truncated if large)**")
                    out = step.get("output")
                    try:
                        # pretty print if dict-like
                        st.text(json.dumps(out)[:8000])
                    except Exception:
                        st.write(str(out))

with col2:
    st.subheader("Audit / Past runs")
    if show_recent:
        runs = list_runs(limit=25)
        for r in runs:
            with st.expander(f"{r['run_id']} — steps {r['steps']} — last: {r['last_at']}"):
                trace = get_trace(r["run_id"])
                st.write(f"Trace length: {len(trace)}")
                for s in trace:
                    st.markdown(f"- **{s['step_index']}. {s['name']}** ({s['tool']}) — {s['duration']:.2f}s")
                if st.button("Load JSON", key=f"load_{r['run_id']}"):
                    st.json(trace)

st.markdown("---")
st.markdown("**Notes:** This demo uses a local orchestrator and stores every step in `data/audit.db`. Replace `tools_registry.py` and `llm_client.py` with production connectors to fetch real data and models.")
