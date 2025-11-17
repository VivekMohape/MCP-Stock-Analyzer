from typing import Dict, Any
TOOLS: Dict[str, Dict[str, Any]] = {}

def register_tool(mcp, name: str, func, params_schema=None, out_schema=None, desc: str = "", sensitivity: str = "low"):
    TOOLS[name] = {"func": func, "params_schema": params_schema, "out_schema": out_schema, "desc": desc, "sensitivity": sensitivity}
    mcp.register(name, func, params_schema, out_schema, desc, sensitivity)
