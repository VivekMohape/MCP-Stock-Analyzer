import yfinance as yf
from functools import lru_cache
from typing import Dict, Any

@lru_cache(maxsize=256)
def _ticker_data(symbol: str, period: str = "1d", interval: str = "1m"):
    t = yf.Ticker(symbol)
    hist = t.history(period=period, interval=interval, auto_adjust=False)
    info = t.info or {}
    return hist, info

def get_quote(symbol: str) -> Dict[str, Any]:
    hist, info = _ticker_data(symbol, period="5d", interval="1m")
    last = None
    try:
        last = float(hist["Close"].dropna().iloc[-1])
    except Exception:
        last = info.get("previousClose") or info.get("open")
    return {"symbol": symbol.upper(), "price": last, "currency": info.get("currency"), "shortName": info.get("shortName")}

def get_history(symbol: str, period: str = "1mo", interval: str = "1d") -> Dict[str, Any]:
    hist, info = _ticker_data(symbol, period=period, interval=interval)
    df = hist.reset_index()
    data = df[["Date", "Open", "High", "Low", "Close", "Volume"]].to_dict(orient="records")
    return {"symbol": symbol.upper(), "data": data}

def fundamentals(symbol: str) -> Dict[str, Any]:
    _, info = _ticker_data(symbol, period="1d", interval="1d")
    keys = ["marketCap", "trailingPE", "forwardPE", "beta", "debtToEquity", "dividendYield"]
    return {k: info.get(k) for k in keys}
