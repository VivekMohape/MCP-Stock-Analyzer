from fastapi import FastAPI, Body, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import time, os, json, logging

from mcp_core import mcp
from services.finance import get_quote, get_history, fundamentals
from tools_registry import register_tool
from jsonschema import validate, ValidationError

from adapters.langgraph_adapter import run_workflow
from adapters.groq_adapter import groq_chat

from audit_model import init_db, persist_audit
from auth import require_api_key
from rate_limiter import check_rate_limit

app = FastAPI()
logger = logging.getLogger("uvicorn.error")

# Initialize DB at startup
init_db()

# -------------------------------------------------------------------------
# Friendly root & health endpoints for Render / browsers
# -------------------------------------------------------------------------
@app.get("/", include_in_schema=False)
def root():
    return {
        "status": "mcp-stock-analyzer",
        "message": "Service is LIVE",
        "endpoints": ["/mcp/manifest", "/mcp/rpc", "/mcp/analyze", "/llm/compose"],
        "docs": "/docs",
    }

@app.get("/healthz", include_in_schema=False)
def healthz():
    return {"status": "ok", "uptime": True}

# -------------------------------------------------------------------------
# Register MCP tools
# -------------------------------------------------------------------------
register_tool(
    mcp,
    "get_quote",
    get_quote,
    params_schema={
        "type": "object",
        "properties": {"symbol": {"type": "string"}},
        "required": ["symbol"],
    },
    desc="Get current quote",
)

register_tool(
    mcp,
    "get_history",
    get_history,
    params_schema={
        "type": "object",
        "properties": {
            "symbol": {"type": "string"},
            "period": {"type": "string"},
            "interval": {"type": "string"},
        },
        "required": ["symbol"],
    },
    desc="Get historical price data",
)

register_tool(
    mcp,
    "fundamentals",
    fundamentals,
    params_schema={
        "type": "object",
        "properties": {"symbol": {"type": "string"}},
        "required": ["symbol"],
    },
    desc="Get fundamentals",
)

# -------------------------------------------------------------------------
# MCP RPC ENDPOINT
# -------------------------------------------------------------------------
class RPC(BaseModel):
    id: str
    method: str
    params: dict = None
    envelope: dict = None

@app.post("/mcp/rpc")
def mcp_rpc(payload: RPC = Body(...), key=Depends(require_api_key)):
    # Rate limit per MCP key
    check_rate_limit(os.getenv("MCP_API_KEY", "dev-local-key"))

    body = payload.dict()
    req_id = body["id"]
    method = body["method"]
    params = body.get("params") or {}

    if method != "tool.call":
        raise HTTPException(status_code=400, detail="Unsupported method")

    tool = params.get("tool")
    args = params.get("args", {})

    if tool not in mcp.tools:
        return {"id": req_id, "error": "tool not found"}

    # Validate schema
    schema = mcp.tools[tool].get("params_schema")
    if schema:
        try:
            validate(instance=args, schema=schema)
        except ValidationError as e:
            return {"id": req_id, "error": f"invalid params: {e.message}"}

    try:
        result = mcp.call(tool, args)

        # Audit log
        audit_payload = {
            "req_id": req_id,
            "tool": tool,
            "args": args,
            "result": result,
            "envelope": body.get("envelope"),
            "ts": time.time(),
        }
        audit_hash = persist_audit(req_id, "tool_call", audit_payload)

        return {"id": req_id, "result": result, "audit_hash": audit_hash}

    except Exception as e:
        return {"id": req_id, "error": str(e)}

# -------------------------------------------------------------------------
# MCP MANIFEST
# -------------------------------------------------------------------------
@app.get("/mcp/manifest")
def manifest(key=Depends(require_api_key)):
    return {"tools": mcp.manifest(None)}

# -------------------------------------------------------------------------
# MCP AUDIT FETCH
# -------------------------------------------------------------------------
@app.get("/mcp/audit")
def get_audit(key=Depends(require_api_key)):
    from audit_model import SessionLocal, AuditRecord
    db = SessionLocal()
    recs = db.query(AuditRecord).order_by(AuditRecord.ts.desc()).limit(200).all()
    out = [
        {
            "req_id": r.req_id,
            "action": r.action,
            "audit_hash": r.audit_hash,
            "ts": r.ts,
        }
        for r in recs
    ]
    db.close()
    return {"count": len(out), "records": out}

# -------------------------------------------------------------------------
# MCP ANALYZE — Orchestrator-centric pipeline
# -------------------------------------------------------------------------
class AnalyzeRequest(BaseModel):
    id: str
    system_prompt: Optional[str] = None
    query: str
    symbols: Optional[List[str]] = []
    workflow: Optional[str] = "stock-analysis"
    params: Optional[Dict[str, Any]] = None

@app.post("/mcp/analyze")
def mcp_analyze(req: AnalyzeRequest = Body(...), key=Depends(require_api_key)):
    # Rate limit per key
    check_rate_limit(os.getenv("MCP_API_KEY", "dev-local-key"))

    body = req.dict()
    req_id = body["id"]
    system_prompt = body.get("system_prompt") or ""
    query = body.get("query") or ""
    symbols = [s.strip().upper() for s in (body.get("symbols") or [])]
    workflow = body.get("workflow") or "stock-analysis"

    steps = []
    tool_audit_refs = []

    try:
        steps.append({"step": "system_prompt", "detail": system_prompt})

        # ---- Run tools for each symbol ----
        for symbol in symbols:

            # QUOTE
            try:
                quote = mcp.call("get_quote", {"symbol": symbol})
                audit_payload = {
                    "req_id": req_id,
                    "tool": "get_quote",
                    "args": {"symbol": symbol},
                    "result": quote,
                    "ts": time.time(),
                }
                audit_hash = persist_audit(req_id, "tool_call", audit_payload)

                steps.append({"step": f"{symbol}:quote", "detail": quote, "audit_hash": audit_hash})
                tool_audit_refs.append({"tool": "get_quote", "symbol": symbol, "audit_hash": audit_hash})
            except Exception as e:
                steps.append({"step": f"{symbol}:quote_error", "detail": str(e)})

            # FUNDAMENTALS
            try:
                fund = mcp.call("fundamentals", {"symbol": symbol})
                audit_payload = {
                    "req_id": req_id,
                    "tool": "fundamentals",
                    "args": {"symbol": symbol},
                    "result": fund,
                    "ts": time.time(),
                }
                audit_hash = persist_audit(req_id, "tool_call", audit_payload)

                steps.append({"step": f"{symbol}:fundamentals", "detail": fund, "audit_hash": audit_hash})
                tool_audit_refs.append({"tool": "fundamentals", "symbol": symbol, "audit_hash": audit_hash})
            except Exception as e:
                steps.append({"step": f"{symbol}:fundamentals_error", "detail": str(e)})

            # HISTORY
            try:
                hist = mcp.call("get_history", {"symbol": symbol, "period": "1mo", "interval": "1d"})
                points = len(hist.get("data", []))

                audit_payload = {
                    "req_id": req_id,
                    "tool": "get_history",
                    "args": {"symbol": symbol},
                    "result_summary": {"points": points},
                    "ts": time.time(),
                }
                audit_hash = persist_audit(req_id, "tool_call", audit_payload)

                steps.append({"step": f"{symbol}:history", "detail": {"points": points}, "audit_hash": audit_hash})
                tool_audit_refs.append({"tool": "get_history", "symbol": symbol, "audit_hash": audit_hash})
            except Exception as e:
                steps.append({"step": f"{symbol}:history_error", "detail": str(e)})

        # ---- Build envelope ----
        slots = {
            "system_instructions": {"content": system_prompt, "source": "system", "ts": time.time()},
            "user_query": {"content": query, "source": "user", "ts": time.time()},
            "tool_outputs": [],
        }

        for s in steps:
            if any(s["step"].endswith(x) for x in [":quote", ":fundamentals", ":history"]):
                raw = s.get("detail")
                snippet = json.dumps(raw) if not isinstance(raw, str) else raw
                if len(snippet) > 2000:
                    snippet = snippet[:2000] + "..."
                slots["tool_outputs"].append({"step": s["step"], "snippet": snippet, "audit_hash": s.get("audit_hash")})

        envelope = {
            "envelope_id": f"env-{int(time.time() * 1000)}",
            "user_id": "ui",
            "session_id": f"sess-{int(time.time() * 1000)}",
            "slots": slots,
            "provenance": {"tool_audit_refs": tool_audit_refs},
            "created_at": time.time(),
        }

        # ---- Call LangGraph or Groq fallback ----
        lg_response = run_workflow(workflow, envelope, timeout=90)

        # ---- Audit the analyze action ----
        analyze_payload = {
            "req_id": req_id,
            "action": "analyze",
            "symbols": symbols,
            "query": query,
            "envelope_id": envelope["envelope_id"],
            "langgraph_result": lg_response,
            "ts": time.time(),
        }

        analyze_audit_hash = persist_audit(req_id, "analyze", analyze_payload)

        # Log final output
        logger.info(
            json.dumps(
                {
                    "event": "final_analysis",
                    "req_id": req_id,
                    "audit_hash": analyze_audit_hash,
                    "lg_source": lg_response.get("source"),
                }
            )
        )

        return {
            "id": req_id,
            "steps": steps,
            "envelope": envelope,
            "langgraph": lg_response,
            "audit_hash": analyze_audit_hash,
        }

    except Exception as e:
        err_payload = {
            "req_id": req_id,
            "action": "analyze_error",
            "error": str(e),
            "ts": time.time(),
        }
        err_hash = persist_audit(req_id, "analyze_error", err_payload)
        return {"id": req_id, "error": str(e), "audit_hash": err_hash}

# -------------------------------------------------------------------------
# DIRECT LLM COMPOSE ENDPOINT (Groq OSS-120B)
# -------------------------------------------------------------------------
@app.post("/llm/compose")
def llm_compose(req: dict = Body(...), key=Depends(require_api_key)):
    """
    POST body:
    {
      "messages": [...],
      "model": "openai/gpt-oss-120b",
      "temperature": 0.2,
      "max_tokens": 512
    }
    """
    check_rate_limit(os.getenv("MCP_API_KEY", "dev-local-key"))

    messages = req.get("messages") or []
    if not messages:
        raise HTTPException(status_code=400, detail="messages required")

    model = req.get("model")
    temperature = req.get("temperature", 0.2)
    max_tokens = req.get("max_tokens", 512)

    try:
        resp = groq_chat(messages, model=model, temperature=temperature, max_tokens=max_tokens)
        return {"ok": True, "result": resp}
    except Exception as e:
        return {"ok": False, "error": str(e)}
