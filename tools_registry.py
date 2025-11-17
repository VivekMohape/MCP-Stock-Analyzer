import time
import random

def quote_tool(ticker: str):
    time.sleep(0.2)
    return {
        "ticker": ticker.upper(),
        "price": round(100 + random.random() * 50, 2),
        "currency": "USD"
    }

def history_tool(ticker: str, period="1mo"):
    time.sleep(0.3)
    return [
        {"day": i, "price": 100 + i * 0.4 + (random.random() - 0.5) * 3}
        for i in range(20)
    ]

def fundamentals_tool(ticker: str):
    time.sleep(0.15)
    return {
        "market_cap": round(5e9 + random.random() * 3e9),
        "pe_ratio": round(10 + random.random() * 20, 1),
        "roe": round(random.random() * 20, 1)
    }

tools = {
    "quote_tool": quote_tool,
    "history_tool": history_tool,
    "fundamentals_tool": fundamentals_tool,
}
