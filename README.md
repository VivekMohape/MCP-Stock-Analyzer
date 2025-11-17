# MCP-Stock-Analyzer

A lightweight, fully local **MCP-style stock analysis system** powered by:

- **Groq LLMs** (gpt-oss-120b via `GROQ_API_KEY`)
- **Local MCP orchestrator** (no LangGraph)
- **Tool-based pipeline** (quotes, history, fundamentals)
- **Step-by-step audit trace** stored in SQLite
- **Interactive Streamlit UI** for inspection and analysis

This project is designed as a clean and production-friendly MCP demonstration that can be deployed **entirely on Streamlit Cloud** without any external backend or Render server.

---

##  Overview

This repository implements a **MCP orchestrator** for stock analysis.  
Each run performs:

1. **Micro-tools**  
   - `quote_tool` – latest price snapshot  
   - `history_tool` – multi-period OHLC history  
   - `fundamentals_tool` – valuation metrics  

2. **LLM synthesis**  
   All collected data is passed to **Groq OSS-120 (gpt-oss-120b)** using the  
   `GROQ_API_KEY` you provide.

3. **Audit + trace logging**  
   Each MCP step (inputs, outputs, timestamps, duration) is logged in a local SQLite DB (`data/audit.db`).

4. **Streamlit UI**  
   View:
   - LLM analysis  
   - Step-by-step tool execution  
   - MCP trace  
   - Past runs (scrollable audit history)  
   - Automatic conclusion summary  

---

##  Architecture

###  MCP Components  
- **Tool Registry:** Defined in `tools_registry.py`  
- **Orchestrator:** Executes tools sequentially → builds context → calls LLM  
- **Audit Layer:** `audit_model.py` for SQLite-based step logging  
- **LLM Client:** `llm_client.py` (Groq-only)  
- **UI Layer:** `streamlit_app.py`  

###  LLM Backend  
Groq **OSS-120** model:  
