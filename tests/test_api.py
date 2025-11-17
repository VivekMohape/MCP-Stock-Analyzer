from fastapi.testclient import TestClient
import sys
sys.path.insert(0, "")
from api import app
client = TestClient(app)

def test_manifest_and_rpc():
    headers = {"X-API-KEY": "dev-local-key"}
    r = client.get("/mcp/manifest", headers=headers)
    assert r.status_code == 200
    payload = {"id": "t1", "method": "tool.call", "params": {"tool": "get_quote", "args": {"symbol": "AAPL"}}}
    r2 = client.post("/mcp/rpc", json=payload, headers=headers)
    assert r2.status_code == 200
    assert "result" in r2.json() or "error" in r2.json()
