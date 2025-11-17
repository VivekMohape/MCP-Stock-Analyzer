import os
from fastapi import HTTPException, Security
from fastapi.security.api_key import APIKeyHeader

API_KEY_HEADER = "X-API-KEY"
api_key_scheme = APIKeyHeader(name=API_KEY_HEADER, auto_error=False)

DEFAULT_KEY = os.getenv("MCP_API_KEY", "dev-local-key")
KEY_STORE = {
    DEFAULT_KEY: {"scopes": ["call:get_quote", "call:get_history", "call:fundamentals", "analyze:run"]}
}

def require_api_key(api_key: str = Security(api_key_scheme)):
    if not api_key or api_key not in KEY_STORE:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return KEY_STORE[api_key]
