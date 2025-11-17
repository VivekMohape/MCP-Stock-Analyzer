# MCP-Stock-Analyzer  
### **Custom MCP • Groq OSS-120 • Streamlit**

A fully local **Custom MCP (Model Context Protocol)** stock analysis workflow powered by:

- **Groq OSS-120B** (via `GROQ_API_KEY`)
- **Local MCP-style orchestrator**
- **Tool-based execution pipeline**
- **Full provenance logging (SQLite)**
- **Interactive Streamlit UI**

Everything runs *directly inside Streamlit Cloud* — no external backend, no LangGraph, no Render deployment.

---

#  Live Demo

 **https://mcp-stock-analyzer.streamlit.app/**

---

#  What This Project Demonstrates

This repository is a compact, production-ready demonstration of a **Custom MCP System**, where:

- Tools fetch market data  
- An orchestrator coordinates all steps  
- Context is assembled and sent to the LLM  
- A structured audit trace is logged  
- A UI visualizes the entire MCP pipeline  

No external services — everything happens inside the Streamlit app.

---

#  Custom MCP Architecture

This is a pure, minimal implementation of MCP:

### ✔ Tools  
Defined in `tools_registry.py`  
- `quote_tool()`  
- `history_tool()`  
- `fundamentals_tool()`

### ✔ Orchestrator  
Defined in `local_orchestrator.py`

Executes the MCP pipeline:

1. Call tools sequentially  
2. Collect results  
3. Compose prompt  
4. Call Groq OSS-120 model  
5. Log each step  

### ✔ Provenance / Audit  
`audit_model.py` logs every MCP step:

- Run ID  
- Step index  
- Tool name  
- Input JSON  
- Output JSON  
- Duration  
- Timestamp  

### ✔ LLM Client  
`llm_client.py`  
- Groq-only  
- Supports probe/debug  
- Uses model: `openai/gpt-oss-120b`

### ✔ UI / Inspector  
`streamlit_app.py`  
Interactive dashboard that shows:

- Final LLM output  
- MCP step-by-step trace  
- Debug information  
- Conclusion summary  
- Past runs (scrollable panel)  

---

#  How This App Implements “Custom MCP”

MCP (Model Context Protocol) = a structured method for LLMs to execute workflows using tools.

This project uses MCP concepts:

| MCP Concept | Implementation |
|------------|----------------|
| **Tools** | Independent micro-functions (`tools_registry.py`) |
| **Controller** | Deterministic orchestrator (`local_orchestrator.py`) |
| **Context Assembly** | Aggregated prompt containing tool outputs |
| **Provenance** | SQLite logs for every tool + LLM call |
| **LLM Resolver** | Groq OSS-120B through `llm_client.py` |
| **Inspector UI** | Streamlit dashboard showing complete trace |
| **Replayability** | `list_runs()` and `get_trace()` |

This is an **MCP system**, but implemented **locally**, using:

- No LangGraph  
- No OpenAI MCP server  
- No JSON-RPC MCP runtime  

Just the **protocol pattern**, clean and customizable.

---

# 🏗 Architecture Diagram (Mermaid)

```mermaid
flowchart TD
    A[Ticker Input] --> B(MCP Orchestrator)
    B --> C1[quote_tool]
    B --> C2[history_tool]
    B --> C3[fundamentals_tool]

    C1 --> D[Context Assembly]
    C2 --> D
    C3 --> D

    D --> E(Groq LLM: gpt-oss-120b)
    E --> F[LLM Output]

    B --> G[Audit Logger (SQLite)]

    F --> H[UI: Final Output]
    G --> I[UI: MCP Trace Viewer]
    G --> J[UI: Past Runs Panel]
````

---

# ✨ Features

* Custom MCP execution pipeline
* Groq OSS-120B integration
* Multi-step tool workflow
* Step-by-step audit trace (inputs + outputs)
* History window selection: 1m, 3m, 6m, 1y, 5y
* Scrollable Past Runs sidebar
* Automatic conclusion extraction
* Debug panel for key detection + LLM probe
* Fully deployable on Streamlit Cloud

---

# 📦 Getting Started (Local)

### 1. Clone the repo

```bash
git clone https://github.com/<your-user>/MCP-Stock-Analyzer.git
cd MCP-Stock-Analyzer
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set your Groq API key

```bash
export GROQ_API_KEY="your_key_here"
```

### 4. Run the Streamlit UI

```bash
streamlit run streamlit_app.py
```

---

# 🌐 Deploy on Streamlit Cloud

1. Push this repository to **GitHub**
2. Go to [https://share.streamlit.io](https://share.streamlit.io) → **New App**
3. Select:

   * Repo: your GitHub repo
   * Branch: `main`
   * File: `streamlit_app.py`
4. Add your secret (under “App → Settings → Secrets”):

   ```
   GROQ_API_KEY = "your_key_here"
   ```
5. Click **Deploy**

---

# 🔧 Replacing Mock Tools with Real Market Data

You can switch from mock data to **yfinance** or an actual market API.

Example:

```python
import yfinance as yf

def quote_tool(ticker):
    return yf.Ticker(ticker).fast_info
```

Add:

* OHLC data
* Financial statements
* Analyst ratings
* News sentiment

---

# 📚 How to Extend the MCP Workflow

You can add any step:

* News scraper
* Sentiment analyzer
* Risk scoring
* Intraday signals
* Options flow
* Multi-model LLM reasoning
* Human-in-the-loop confirmation

Each becomes another MCP “step” in the orchestrator + audit log.

---

# 🤝 Contribution

PRs welcome!
Open an issue for:

* additional MCP patterns
* better tooling integration
* Groq rate-limit handling
* persistent DB storage
* enhanced charting

