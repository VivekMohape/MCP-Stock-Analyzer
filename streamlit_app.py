import streamlit as st
from local_orchestrator import run_analysis
from audit_model import list_runs, get_trace

st.set_page_config(page_title="MCP Stock Analyzer — Groq", layout="wide")
st.title("📈 MCP Stock Analyzer — Using Groq gpt-oss-120b")

ticker = st.text_input("Enter stock ticker", "AAPL")
period = st.selectbox("History period", ["1mo", "3mo", "6mo"], index=0)

if st.button("Run MCP Pipeline"):
    with st.spinner("Running MCP Orchestrator..."):
        resp = run_analysis(ticker, {"period": period})

    st.success("Analysis complete!")

    st.subheader("LLM Final Output")
    st.write(resp["result"]["text"])

    st.subheader("Full MCP Trace")
    for i, step in enumerate(resp["trace"]):
        with st.expander(f"Step {i+1}: {step['name']} ({step['tool']})"):
            st.json(step)

st.sidebar.header("Past Runs")
runs = list_runs()
for r in runs:
    with st.sidebar.expander(f"{r['run_id']} ({r['steps']} steps)"):
        trace = get_trace(r["run_id"])
        st.json(trace)
