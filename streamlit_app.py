import streamlit as st
import os
import json
from local_orchestrator import run_analysis
from audit_model import list_runs, get_trace

st.set_page_config(page_title="MCP Stock Analyzer", layout="wide")
st.title("📈 MCP Stock Analyzer")

# -----------------------
# Top: Instructions / Diagnostics
# -----------------------
with st.expander("📝 How to use this app — Quick Instructions (click to expand)", expanded=True):
    st.markdown("""
**Steps to run**
1. Add the Groq API key in **Streamlit Cloud → App → Settings → Secrets** with key name: `GROQ_API_KEY`.  
   - **Value** should be the raw key (example: `gsk_xxx`), **no surrounding quotes**.
2. Push this code to GitHub and **Deploy** the app on Streamlit Cloud (or click Redeploy after editing secrets).
3. Enter a stock ticker (e.g. `AAPL`) and choose a history window (1m, 3m, 6m, 1y, 5y).  
4. Click **Run MCP Pipeline** — the UI will show LLM output + a step-by-step audit trace.
5. To inspect past runs, use the right-side **Past Runs** scroll panel (ephemeral storage on Streamlit Cloud).

**Notes & Troubleshooting**
- If you see a mock LLM response: check the top diagnostics (it shows whether the GROQ key is detected) and redeploy after changing secrets.
- Audit DB is ephemeral on Streamlit Cloud (container restarts will clear it). For persistence, use an external DB (Supabase/Postgres).
- For production replace mocked tools in `tools_registry.py` with real fetchers (yfinance, company API).
""")

# Diagnostic: detect GROQ presence (safe; do not print the key)
def detect_groq_source():
    found_env = bool(os.getenv("GROQ_API_KEY"))
    found_secrets = False
    masked = None
    try:
        if hasattr(st, "secrets"):
            s = st.secrets
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

    return {"env": found_env, "secrets": found_secrets, "masked": masked}

diag = detect_groq_source()
col_diag1, col_diag2, col_diag3 = st.columns([1,1,4])
with col_diag1:
    st.write("🔐 Key in env:", diag["env"])
with col_diag2:
    st.write("🔑 Key in st.secrets:", diag["secrets"])
with col_diag3:
    st.write("Masked (secrets):", diag["masked"] or "—")
    if not (diag["env"] or diag["secrets"]):
        st.warning("GROQ_API_KEY not found. Add it under App → Settings → Secrets and Redeploy the app.")

st.markdown("---")

# -----------------------
# Left: Main controls + outputs
# -----------------------
left_col, right_col = st.columns([2, 1])

with left_col:
    st.header("Run MCP Analysis")
    # timeline options: 1m,3m,6m,1y,5y
    ticker = st.text_input("Ticker (e.g. AAPL)", value="AAPL")
    period_map = {
        "1m": "1m",
        "3m": "3m",
        "6m": "6m",
        "1y": "1y",
        "5y": "5y",
    }
    period_label = st.selectbox("History window", list(period_map.keys()), index=0)
    period = period_map[period_label]

    run_button = st.button("▶️ Run MCP Pipeline")

    if run_button:
        if not ticker or not ticker.strip():
            st.error("Please enter a valid ticker.")
        else:
            with st.spinner("Running MCP orchestrator (tools → LLM) ..."):
                resp = run_analysis(ticker.strip(), {"period": period})
            st.success("Run finished — see results below")

            # LLM Final Output
            st.subheader("LLM Final Output")
            llm_result = resp.get("result")
            if isinstance(llm_result, dict) and llm_result.get("mock"):
                st.error("LLM returned a mock response (no key or probe failed). See debug below.")
                st.code(llm_result.get("text"))
                st.json(llm_result.get("debug"))
            else:
                # normally llm_result is dict with "text"
                if isinstance(llm_result, dict) and "text" in llm_result:
                    st.markdown("**Model output (raw):**")
                    st.text_area("LLM output", value=llm_result["text"], height=200)
                else:
                    st.write(llm_result)

            # MCP Trace (expanders)
            st.subheader("Full MCP Trace")
            for i, step in enumerate(resp.get("trace", [])):
                label = f"Step {i+1}: {step.get('name')} — {step.get('tool')}"
                with st.expander(label, expanded=(i == len(resp.get("trace", [])) - 1)):
                    st.write("**Input**")
                    try:
                        st.json(step.get("input", {}))
                    except Exception:
                        st.write(step.get("input", {}))
                    st.write("**Output**")
                    out = step.get("output", {})
                    # If LLM output, show text + debug if available
                    if isinstance(out, dict) and out.get("text"):
                        st.text_area("LLM text (truncated)", value=out.get("text")[:6000], height=140)
                        if out.get("debug"):
                            st.write("LLM Debug (safe):")
                            st.json(out.get("debug"))
                    else:
                        try:
                            st.json(out)
                        except Exception:
                            st.write(str(out))

            # Conclusion area: try to present a short final takeaway
            st.markdown("---")
            st.subheader("Conclusion / Final Recommendation")
            conclusion_text = ""
            # extract from LLM result if available
            if isinstance(llm_result, dict) and llm_result.get("text"):
                # simple heuristic: take first 400 chars or last paragraph as "conclusion"
                text = llm_result.get("text").strip()
                # prefer last paragraph if it's short
                paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
                if len(paragraphs) >= 2:
                    conclusion_text = paragraphs[-1]
                else:
                    conclusion_text = text[:800]
            else:
                conclusion_text = "No LLM conclusion available (mock response or empty output)."
            st.info(conclusion_text)

# -----------------------
# Right: Minimized Past Runs / Audit — scrollable panel (fixed height)
# -----------------------
with right_col:
    st.header("Past Runs (Audit)")
    st.markdown("**Stored runs (ephemeral)** — click an item to expand details.")
    runs = list_runs(limit=50)

    # Build an HTML block with a vertical scroll for compactness
    # We will render a simple list of runs and allow expand via client-side buttons is complex,
    # so we'll provide a compact JSON viewer inside a scrollable box.
    runs_json = []
    for r in runs:
        runs_json.append({
            "run_id": r["run_id"],
            "last_at": r["last_at"],
            "steps": r["steps"]
        })

    # Inline CSS for scrollable box
    scroll_box_style = """
    <style>
      .scroll-box {
        height: 520px;
        overflow-y: auto;
        padding: 8px;
        border: 1px solid #eee;
        border-radius: 6px;
        background: #fafafa;
      }
      .run-item {
        padding: 8px;
        margin-bottom: 6px;
        border-radius: 4px;
        background: white;
        box-shadow: 0 0 0 1px rgba(0,0,0,0.03);
      }
      .run-id { font-weight: 600; }
      .run-meta { font-size: 12px; color: #555; }
      .load-btn { margin-top:6px; }
    </style>
    """

    runs_html = scroll_box_style + "<div class='scroll-box'>"
    if not runs_json:
        runs_html += "<div>No runs available yet. Run an analysis to populate audit log.</div>"
    else:
        for r in runs_json:
            # safe-escape
            rid = r["run_id"]
            last_at = r["last_at"]
            steps = r["steps"]
            runs_html += f"""
              <div class='run-item'>
                <div class='run-id'>{rid}</div>
                <div class='run-meta'>last_at: {last_at} — steps: {steps}</div>
                <div style='margin-top:6px;'>
                  <button onclick="window._st_load_trace && window._st_load_trace('{rid}')">Load</button>
                </div>
              </div>
            """
    runs_html += "</div>"

    # Render the HTML. We will also provide a fallback to load via Python buttons below.
    st.components.v1.html(runs_html, height=560, scrolling=True)

    # Fallback Python-based loader (if user prefers)
    st.markdown("**Load run details (fallback):**")
    run_ids = [r["run_id"] for r in runs_json]
    sel = st.selectbox("Select run id", options=run_ids or ["-"])
    if sel and sel != "-":
        trace = get_trace(sel)
        st.markdown(f"**Trace for {sel}**")
        st.json(trace)

st.markdown("---")
st.caption("UI Notes: Past Runs are shown on the right in a scrollable compact panel to keep the main trace readable. Audit DB is ephemeral on Streamlit Cloud.")

