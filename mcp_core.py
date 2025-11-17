import hashlib, json, time
from typing import Callable, Dict, Any

class MCP:
    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}
    def register(self, name: str, func: Callable, params_schema: dict = None, out_schema: dict = None, desc: str = "", sensitivity: str = "low"):
        self.tools[name] = {"func": func, "params_schema": params_schema, "out_schema": out_schema, "desc": desc, "sensitivity": sensitivity}
    def manifest(self, api_key=None):
        return [{"name": k, "desc": v["desc"], "params_schema": v["params_schema"], "sensitivity": v["sensitivity"]} for k, v in self.tools.items()]
    def call(self, name: str, params: dict):
        if name not in self.tools:
            raise KeyError("tool not found")
        return self.tools[name]["func"](**(params or {}))

mcp = MCP()
