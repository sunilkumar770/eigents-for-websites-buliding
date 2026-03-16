# 🤖 Eigent — AI-Powered Multi-Agent Code Generator

> Generate full-stack applications with a team of specialized AI agents — locally or in the cloud.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

---

## ✨ What is Eigent?

**Eigent** is a multi-agent AI system that automatically generates complete, production-ready full-stack applications from a simple text description. It orchestrates a team of specialized AI agents — each focused on a specific part of the development lifecycle.

| Agent | Responsibility |
|---|---|
| 🔍 **Product Interpreter** | Translates your idea into structured requirements |
| 🎨 **Frontend Engineer** | Builds the UI components and pages |
| ⚙️ **Backend Engineer** | Designs API endpoints and database schema |
| 🔗 **Integration Engineer** | Wires frontend + backend together |
| 🐛 **Debug Agent** | Identifies and fixes code issues |
| 🛡️ **Security Agent** | Audits for vulnerabilities |
| ✅ **Testing Agent** | Writes automated tests |
| 🚀 **Production Readiness Agent** | Prepares deployment configs |

---

## 🚀 Quick Start

### 1. Prerequisites

- **Python 3.9+**
- **[Ollama](https://ollama.com/download)** (for free local inference) — *or* an NVIDIA API key for Kimi K2.5

### 2. Install

```bash
git clone https://github.com/YOUR_USERNAME/eigent.git
cd eigent
pip install -r requirements.txt
```

### 3. Configure

```bash
cp .env.example .env
# Edit .env with your preferred LLM backend (see below)
```

### 4. Start Ollama (recommended, free)

```bash
# Pull a model
ollama pull deepseek-r1:1.5b

# Start the Ollama server
ollama serve
```

### 5. Run!

```bash
# Start the API server
python api/api_server.py

# In a new terminal — create your first project
python api/cli.py create "Build a recipe sharing app with user authentication"

# Watch the agents work
python api/cli.py status <project-id>
```

---

## ⚙️ LLM Configuration

Eigent supports two LLM backends — configure via your `.env` file:

### Option A: Ollama (Free, Local, Recommended)

```env
OLLAMA_MODEL=deepseek-r1:1.5b
OLLAMA_BASE_URL=http://localhost:11434
```

Works with any Ollama-compatible model like `deepseek-r1`, `llama3`, `gemma3`, `mistral`, `phi3`, etc.

### Option B: Kimi K2.5 via NVIDIA API (Cloud)

```env
NVIDIA_API_KEY=your_key_here
```

Sign up at [build.nvidia.com](https://build.nvidia.com) for a free API key.

### Option C: Hybrid (Best of Both)

Set **both** variables and Eigent will automatically route complex tasks to Kimi and fast tasks to Ollama using the `MultiLLMRouter`.

---

## 🏗️ Project Structure

```
eigent/
├── api/                    # FastAPI server + CLI
│   ├── api_server.py       # REST API  (port 8000)
│   └── cli.py              # Command-line interface
├── agents/                 # Individual AI agents
├── orchestration/          # Workflow engine & state management
├── antigravity/
│   └── llm/                # LLM adapters (Ollama, Kimi, Router)
├── generated_projects/     # Output directory (gitignored)
├── eigent_mcp.py           # MCP server for Antigravity integration
├── .env.example            # Environment variable template
└── requirements.txt
```

---

## 🔌 MCP Server (Antigravity Integration)

Eigent can be used as an MCP server in **Antigravity** for hybrid AI orchestration:

```json
{
  "eigent-hybrid": {
    "command": "python",
    "args": ["path/to/eigent/eigent_mcp.py"],
    "env": {
      "OLLAMA_MODEL": "deepseek-r1:1.5b",
      "OLLAMA_BASE_URL": "http://localhost:11434"
    }
  }
}
```

---

## 📦 Requirements

```
fastapi
uvicorn
requests
python-dotenv
fastmcp
```

Install: `pip install -r requirements.txt`

---

## 📄 License

MIT © 2025 Eigent Contributors
