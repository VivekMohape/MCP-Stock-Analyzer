from fastapi import FastAPI
from pydantic import BaseModel
from local_orchestrator import run_analysis

app = FastAPI()

class Req(BaseModel):
    ticker: str
    params: dict = {}

@app.post("/analyze")
def analyze(req: Req):
    return run_analysis(req.ticker, req.params)
