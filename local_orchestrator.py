import time
import json
from tools_registry import tools
from audit_model import save_audit_step
from utils import make_run_id, now_iso
from llm_client import make_llm_call

def compose_prompt(ticker, quote, history, fundamentals, params):
    return f"""
Analyze stock {ticker} based on:

Quote: {json.dumps(quote)}
Fundamentals: {json.dumps(fundamentals)}
History sample: {str(history)[:800]}
Params: {params}

Return JSON with:
- technical_summary
- fundamental_summary
- risk_assessment
- final_recommendation
"""

def run_analysis(ticker: str, params={}, run_id=None):
    if run_id is None:
        run_id = make_run_id("mcp")

    trace = []
    idx = 0

    # STEP 1 — QUOTE
    start = time.time()
    quote = tools["quote_tool"](ticker)
    duration = time.time() - start
    save_audit_step(run_id, idx, "quote", "quote_tool", {"ticker": ticker}, quote, duration, now_iso())
    trace.append({"name": "quote", "tool": "quote_tool", "input": {"ticker": ticker}, "output": quote})
    idx += 1

    # STEP 2 — HISTORY
    start = time.time()
    history = tools["history_tool"](ticker, params.get("period", "1mo"))
    duration = time.time() - start
    save_audit_step(run_id, idx, "history", "history_tool", {"ticker": ticker}, history, duration, now_iso())
    trace.append({"name": "history", "tool": "history_tool", "input": {}, "output": history})
    idx += 1

    # STEP 3 — FUNDAMENTALS
    start = time.time()
    fundamentals = tools["fundamentals_tool"](ticker)
    duration = time.time() - start
    save_audit_step(run_id, idx, "fundamentals", "fundamentals_tool", {"ticker": ticker}, fundamentals, duration, now_iso())
    trace.append({"name": "fundamentals", "tool": "fundamentals_tool", "input": {}, "output": fundamentals})
    idx += 1

    # STEP 4 — LLM
    prompt = compose_prompt(ticker, quote, history, fundamentals, params)
    start = time.time()
    llm_resp = make_llm_call(prompt)
    duration = time.time() - start

    save_audit_step(run_id, idx, "llm_analysis", "gpt-oss-120b", {"prompt": prompt[:1500]}, llm_resp, duration, now_iso())
    trace.append({"name": "llm_analysis", "tool": "gpt-oss-120b", "input": {}, "output": llm_resp})

    return {"run_id": run_id, "trace": trace, "result": llm_resp}
