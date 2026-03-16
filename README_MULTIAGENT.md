# Multi-Agent Web Development System

> **Transform a simple idea into a production-ready web application with zero human intervention**

## 🌟 Overview

An autonomous multi-agent system that coordinates 8 specialized AI agents to build complete full-stack web applications from natural language prompts. The system handles everything from requirements gathering to production deployment validation.

## ✨ Features

- **🤖 8 Specialized Agents**: Product Interpreter, Frontend Engineer, Backend Engineer, Integration, Testing, Debug, Security, Production Readiness
- **🔄 Autonomous Workflow**: Complete automation from idea to production-ready code
- **📊 Real-time Monitoring**: WebSocket and Server-Sent Events for live progress updates
- **🔁 Automatic Retry**: Intelligent retry logic with exponential backoff
- **🎯 Quality Gates**: Confidence-based validation between stages
- **⚡ Parallel Execution**: Frontend and Backend generated simultaneously
- **🛡️ Security First**: OWASP Top 10 vulnerability scanning
- **📦 Production Ready**: Deployment checklists and infrastructure-as-code templates

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements_orchestrator.txt

# Set your API key
export NVIDIA_API_KEY="your-api-key-here"
```

### Option 1: CLI (Recommended)

```bash
# Create a project
python cli.py create "Build a recipe sharing platform with ratings and comments" --watch

# Check status
python cli.py status <project-id>

# Download generated code
python cli.py download <project-id> --output ./my-app
```

### Option 2: API Server

```bash
# Start the server
python api_server.py

# In another terminal, create a project
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Build a task management app",
    "context": {"target_audience": "small teams"}
  }'
```

### Option 3: Python SDK

```python
from workflow_orchestrator import WorkflowOrchestrator
from antigravity.llm.kimi_adapter import KimiAdapter

adapter = KimiAdapter(api_key="YOUR_KEY")
orchestrator = WorkflowOrchestrator(llm_adapter=adapter)

project_id = orchestrator.create_project(
    prompt="Build a blog platform",
    context={'target_audience': 'developers'}
)

orchestrator.run(max_iterations=50)
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface                          │
│              (CLI / REST API / WebSocket)                   │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│              Workflow Orchestrator                          │
│  (State Machine, Quality Gates, Parallel Execution)        │
└─────┬──────────────┬──────────────┬────────────────────────┘
      │              │              │
┌─────▼─────┐  ┌────▼─────┐  ┌─────▼──────┐
│   State   │  │   Task   │  │  Message   │
│  Manager  │  │   Queue  │  │    Bus     │
└───────────┘  └──────────┘  └────────────┘
      │              │              │
┌─────▼──────────────▼──────────────▼────────────────────────┐
│                    8 Specialized Agents                     │
│  Product │ Frontend │ Backend │ Integration │ Testing      │
│  Debug │ Security │ Production Readiness                   │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Workflow Stages

1. **Product Interpretation** → Converts prompt to structured requirements
2. **Frontend Generation** → Creates React/Next.js/Vue application
3. **Backend Generation** → Builds Node.js/Python/Go API server
4. **Integration** → Connects frontend ↔ backend with API clients
5. **Testing** → Generates and runs unit/integration/E2E tests
6. **Debug** → Automatically fixes errors (if tests fail)
7. **Security Audit** → OWASP Top 10 vulnerability scanning
8. **Production Readiness** → Validates deployment readiness

## 🎯 What You Get

From a simple prompt like:
```
"Build a recipe sharing platform with ratings and comments"
```

You get:
- ✅ Complete React/Next.js frontend with components
- ✅ Node.js/Python backend with REST API
- ✅ Database schema and migrations
- ✅ Authentication and authorization
- ✅ Comprehensive test suites
- ✅ Security audit report
- ✅ Production deployment checklist
- ✅ Docker and Kubernetes configs

## 📚 API Documentation

### REST Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/projects` | Create new project |
| GET | `/projects/{id}` | Get project status |
| GET | `/projects` | List all projects |
| GET | `/projects/{id}/progress` | Stream progress (SSE) |
| GET | `/projects/{id}/artifacts` | Download generated code |
| POST | `/projects/{id}/retry` | Retry failed stage |
| DELETE | `/projects/{id}` | Delete project |
| GET | `/health` | Health check |
| GET | `/stats` | System statistics |

### WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/projects/{id}');
ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log('Progress:', update);
};
```

## 🧪 Testing

```bash
# Run integration tests
pytest test_orchestrator.py -v

# Test coverage
pytest test_orchestrator.py --cov=. --cov-report=html
```

## 📊 System Statistics

- **Total Components**: 24 files
- **Lines of Code**: ~8,000+
- **Agents**: 8 specialized agents
- **API Endpoints**: 10+ REST + WebSocket
- **Test Coverage**: Core orchestration layer

## 🔧 Configuration

Edit `orchestrator_config.py` to customize:
- Confidence thresholds for quality gates
- Maximum retry attempts
- Database connection (SQLite/PostgreSQL)
- Parallel execution settings
- Logging levels

## 🚢 Deployment

### Local Development
```bash
python api_server.py
```

### Production (Docker)
```bash
docker build -t multi-agent-system .
docker run -p 8000:8000 -e NVIDIA_API_KEY=your-key multi-agent-system
```

### Production (Kubernetes)
```bash
kubectl apply -f k8s/deployment.yaml
```

## 🤝 Contributing

This is a demonstration project showcasing autonomous multi-agent systems for web development.

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- Built with FastAPI, SQLAlchemy, and Click
- Powered by Kimi K2.5 LLM via NVIDIA API
- Inspired by autonomous agent architectures

---

**Made with ❤️ by the Antigravity Team**
