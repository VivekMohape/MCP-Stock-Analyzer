# MCP‑Stock‑Analyzer

A multi‑agent stock analysis system built on the **Model Context Protocol (MCP)**. It combines OpenAI’s OSS‑20B LLM, LangGraph workflows, and yfinance‑powered market data to deliver fast, auditable technical and fundamental insights via a FastAPI backend and Streamlit UI.

## Overview
This repository implements an orchestrator‑centric MCP demo for stock analysis:

- **Data sources:** yfinance tools (quotes, history, fundamentals)  
- **MCP components:** tool registry + SQLite audit persistence  
- **API endpoints:** JSON‑RPC `/mcp/rpc` and orchestrator `/mcp/analyze`  
- **Workflow support:** LangGraph integration  
- **LLM backend:** OpenAI OSS‑20B (configured with `GROQ_API_KEY`)  
- **UI:** Streamlit interface

## Features
- Real‑time market data retrieval  
- Technical and fundamental analysis pipelines  
- Auditable interactions stored in SQLite  
- Scalable FastAPI backend  
- Interactive Streamlit dashboard for users

## Getting Started
1. Clone the repository.  
2. Install dependencies: `pip install -r requirements.txt`.  
3. Set `GROQ_API_KEY` in your environment.  
4. Run the FastAPI server: `uvicorn app.main:app --reload`.  
5. Launch the Streamlit UI: `streamlit run ui/app.py`.

## Contribution
Feel free to open issues or submit pull requests. All contributions are welcome!  
