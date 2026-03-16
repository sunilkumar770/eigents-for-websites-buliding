# Multi-Agent System - Quick Start Guide

## Installation

1. **Install Dependencies**:
```bash
pip install -r requirements_orchestrator.txt
```

2. **Set API Key**:
```bash
export NVIDIA_API_KEY="your-api-key-here"
```

## Running the System

### Option 1: API Server

Start the API server:
```bash
python api_server.py
```

The server will start on `http://localhost:8000`

### Option 2: CLI Tool

Use the command-line interface:

**Create a project**:
```bash
python cli.py create "Build a recipe sharing platform"
```

**Watch progress**:
```bash
python cli.py create "Build a task manager" --watch
```

**Check status**:
```bash
python cli.py status <project-id>
```

**Download artifacts**:
```bash
python cli.py download <project-id> --output ./my-app
```

**List projects**:
```bash
python cli.py list
```

### Option 3: Python Demo

Run the demo script:
```bash
python demo.py
```

## API Endpoints

### Create Project
```bash
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Build a recipe sharing platform",
    "context": {
      "target_audience": "home cooks"
    }
  }'
```

### Get Project Status
```bash
curl http://localhost:8000/projects/<project-id>
```

### Stream Progress (Server-Sent Events)
```bash
curl -N http://localhost:8000/projects/<project-id>/progress
```

### Download Artifacts
```bash
curl http://localhost:8000/projects/<project-id>/artifacts
```

### WebSocket Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/projects/<project-id>');

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log('Update:', update);
};
```

## System Statistics

```bash
curl http://localhost:8000/stats
```

## Health Check

```bash
curl http://localhost:8000/health
```

## Example Workflow

1. **Create a project**:
```bash
PROJECT_ID=$(python cli.py create "Build a blog platform" | grep "Project ID" | cut -d: -f2 | tr -d ' ')
```

2. **Watch progress**:
```bash
python cli.py logs $PROJECT_ID --follow
```

3. **Download when complete**:
```bash
python cli.py download $PROJECT_ID --output ./my-blog
```

## Troubleshooting

- **Database locked**: Only one process can write to SQLite at a time. Use the API server for concurrent access.
- **LLM timeout**: Increase timeout in `kimi_adapter.py` or check API key.
- **Port already in use**: Change port in `api_server.py` (default: 8000)
