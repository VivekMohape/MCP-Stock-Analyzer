import os, time, json
from typing import Any, Dict
from adapters.groq_adapter import groq_chat

LANGGRAPH_API_KEY = os.getenv("LANGGRAPH_API_KEY")
LANGGRAPH_BASE = os.getenv("LANGGRAPH_BASE", "https://api.langgraph.com/v1")

def _local_short(text: str, max_chars: int = 400):
    if not text:
        return ""
    t = text.strip()
    if len(t) <= max_chars:
        return t
    cut = t[:max_chars]
    last_dot = max(cut.rfind("."), cut.rfind("!"), cut.rfind("?"))
    if last_dot > int(max_chars * 0.6):
        return cut[: last_dot + 1] + " ..."
    return cut + " ..."

def _pack_envelope_text(envelope: Dict[str, Any]) -> str:
    parts = []
    slots = envelope.get("slots", {})
    if slots.get("system_instructions"):
        parts.append("SYSTEM: " + _local_short(slots["system_instructions"].get("content",""), 800))
    if slots.get("user_query"):
        parts.append("USER QUERY: " + _local_short(slots["user_query"].get("content",""), 800))
    for t in slots.get("tool_outputs", []):
        parts.append(f"{t.get('step')}: { _local_short(t.get('snippet',''), 800)}")
    return "\n\n".join(parts)

def _groq_multi_agent_fallback(envelope: Dict[str, Any]) -> Dict[str, Any]:
    """
    Use Groq to emulate Technical + Fundamental analyzers when LangGraph is not configured.
    Each agent receives a system prompt + the compact envelope.
    Expect Groq to return JSON strings (we try to parse).
    """
    envelope_text = _pack_envelope_text(envelope)
    # Technical agent prompt
    tech_system = {
        "role": "system",
        "content": "You are a Technical Analysis agent. Return strictly JSON with keys: technical_report (markdown), technical_signals (array of {name,value,confidence}), chart_actions (list), confidence (0-1)."
    }
    tech_user = {"role": "user", "content": "ENVELOPE:\n\n" + envelope_text + "\n\nRespond with JSON as described."}
    tech_resp = groq_chat([tech_system, tech_user], temperature=0.2, max_tokens=512)
    tech_content = tech_resp.get("content","")
    try:
        tech_json = json.loads(tech_content)
    except Exception:
        # minimal fallback if parsing fails
        tech_json = {"technical_report": tech_content[:800], "technical_signals": [], "chart_actions": [], "confidence": 0.5}

    # Fundamental agent prompt
    fund_system = {
        "role": "system",
        "content": "You are a Fundamental Analysis agent. Return strictly JSON with keys: fundamental_report (markdown), fundamental_metrics (object), thesis (string), actions (list), confidence (0-1)."
    }
    fund_user = {"role": "user", "content": "ENVELOPE:\n\n" + envelope_text + "\n\nRespond with JSON as described."}
    fund_resp = groq_chat([fund_system, fund_user], temperature=0.2, max_tokens=512)
    fund_content = fund_resp.get("content","")
    try:
        fund_json = json.loads(fund_content)
    except Exception:
        fund_json = {"fundamental_report": fund_content[:800], "fundamental_metrics": {}, "thesis": "", "actions": [], "confidence": 0.5}

    return {"source": "groq_local_fallback", "technical": tech_json, "fundamental": fund_json, "generated_at": time.time()}

def run_workflow(workflow_name: str, envelope: Dict[str, Any], timeout: int = 30) -> Dict[str, Any]:
    """
    Orchestrator-centric call to LangGraph workflow.
    If LANGGRAPH_API_KEY present, call LangGraph; otherwise try Groq-based local multi-agent fallback.
    """
    if LANGGRAPH_API_KEY:
        import requests
        url = f"{LANGGRAPH_BASE}/workflows/{workflow_name}/run"
        headers = {"Authorization": f"Bearer {LANGGRAPH_API_KEY}", "Content-Type": "application/json"}
        payload = {"input": {"envelope": envelope}}
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
            resp.raise_for_status()
            return {"source": "langgraph", "payload": resp.json()}
        except Exception as e:
            # fallback to Groq if LangGraph fails
            return {"source": "langgraph_error", "error": str(e), "fallback": _groq_multi_agent_fallback(envelope)}
    # No LangGraph key — use Groq local multi-agent
    return _groq_multi_agent_fallback(envelope)
