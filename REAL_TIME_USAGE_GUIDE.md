# 🔥 Real-Time Agent Interaction Guide

## 🎯 Overview

You have **4 ways** to interact with agents in real-time:

1. **CLI with Live Progress** (Easiest)
2. **WebSocket Streaming** (Real-time updates)
3. **Server-Sent Events (SSE)** (HTTP streaming)
4. **Python SDK** (Direct integration)

---

## 1️⃣ CLI with Live Progress (Recommended)

### Start a Project with Real-time Updates

```bash
# Watch progress in real-time
python api/cli.py create "Build a blog platform" --watch

# You'll see:
# ✅ Product Interpretation (30s)
# 🔄 Frontend Generation (2-3 min)
# 🔄 Backend Generation (2-3 min)
# ✅ Integration (1 min)
# ... and so on
```

### Monitor Existing Project

```bash
# Stream logs for a project
python api/cli.py logs <project-id> --follow

# Check status anytime
python api/cli.py status <project-id>
```

### All CLI Commands

```bash
# Create project
python api/cli.py create "Your app idea" --watch

# List all projects
python api/cli.py list

# Get project status
python api/cli.py status <project-id>

# Stream logs
python api/cli.py logs <project-id> --follow

# Download generated code
python api/cli.py download <project-id> --output ./my-app

# Retry a failed stage
python api/cli.py retry <project-id> <stage-name>

# View system statistics
python api/cli.py stats
```

---

## 2️⃣ WebSocket Streaming (Real-time)

### Start API Server

```bash
python api/api_server.py
```

### Connect via WebSocket

**JavaScript Example:**
```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/projects/<project-id>');

// Receive real-time updates
ws.onmessage = (event) => {
    const update = JSON.parse(event.data);
    console.log('Event:', update.type);
    console.log('Data:', update.data);
    
    // Handle different event types
    switch(update.type) {
        case 'workflow_started':
            console.log('🚀 Workflow started!');
            break;
        case 'task_started':
            console.log(`🔄 ${update.data.stage_name} started`);
            break;
        case 'task_completed':
            console.log(`✅ ${update.data.stage_name} completed`);
            console.log(`Confidence: ${update.data.confidence}%`);
            break;
        case 'task_failed':
            console.log(`❌ ${update.data.stage_name} failed`);
            console.log(`Error: ${update.data.error}`);
            break;
        case 'workflow_completed':
            console.log('🎉 Workflow completed!');
            break;
    }
};

ws.onerror = (error) => {
    console.error('WebSocket error:', error);
};

ws.onclose = () => {
    console.log('WebSocket connection closed');
};
```

**Python Example:**
```python
import websocket
import json

def on_message(ws, message):
    update = json.loads(message)
    print(f"Event: {update['type']}")
    print(f"Data: {update['data']}")

def on_error(ws, error):
    print(f"Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("Connection closed")

def on_open(ws):
    print("Connected to WebSocket")

# Connect
ws = websocket.WebSocketApp(
    "ws://localhost:8000/ws/projects/<project-id>",
    on_message=on_message,
    on_error=on_error,
    on_close=on_close,
    on_open=on_open
)

ws.run_forever()
```

---

## 3️⃣ Server-Sent Events (SSE)

### Stream Progress via HTTP

**cURL Example:**
```bash
# Stream progress updates
curl -N http://localhost:8000/projects/<project-id>/progress
```

**Python Example:**
```python
import requests

# Stream progress
response = requests.get(
    'http://localhost:8000/projects/<project-id>/progress',
    stream=True
)

for line in response.iter_lines():
    if line:
        # Parse SSE format
        if line.startswith(b'data: '):
            data = line[6:].decode('utf-8')
            print(f"Update: {data}")
```

**JavaScript Example:**
```javascript
// Use EventSource for SSE
const eventSource = new EventSource(
    'http://localhost:8000/projects/<project-id>/progress'
);

eventSource.onmessage = (event) => {
    const update = JSON.parse(event.data);
    console.log('Progress update:', update);
};

eventSource.onerror = (error) => {
    console.error('SSE error:', error);
    eventSource.close();
};
```

---

## 4️⃣ Python SDK (Direct Integration)

### Real-time Monitoring with Callbacks

```python
from orchestration import WorkflowOrchestrator, MessageBus, MessageType
from antigravity.llm.kimi_adapter import KimiAdapter
import os

# Initialize
adapter = KimiAdapter(api_key=os.getenv('NVIDIA_API_KEY'))
orchestrator = WorkflowOrchestrator(llm_adapter=adapter)

# Subscribe to real-time events
bus = orchestrator.message_bus

# Define callbacks
def on_workflow_started(message):
    print(f"🚀 Workflow started: {message.project_id}")

def on_task_started(message):
    stage = message.payload['stage_name']
    print(f"🔄 Starting: {stage}")

def on_task_completed(message):
    stage = message.payload['stage_name']
    confidence = message.payload['confidence']
    print(f"✅ Completed: {stage} (confidence: {confidence}%)")

def on_task_failed(message):
    stage = message.payload['stage_name']
    error = message.payload['error']
    print(f"❌ Failed: {stage} - {error}")

def on_workflow_completed(message):
    print(f"🎉 Workflow completed!")

# Subscribe to events
bus.subscribe(MessageType.WORKFLOW_STARTED, on_workflow_started)
bus.subscribe(MessageType.TASK_STARTED, on_task_started)
bus.subscribe(MessageType.TASK_COMPLETED, on_task_completed)
bus.subscribe(MessageType.TASK_FAILED, on_task_failed)
bus.subscribe(MessageType.WORKFLOW_COMPLETED, on_workflow_completed)

# Create project
project_id = orchestrator.create_project(
    prompt="Build a recipe sharing platform",
    context={'target_audience': 'home cooks'}
)

print(f"Created project: {project_id}\n")

# Run workflow (events will fire in real-time)
orchestrator.run(max_iterations=50)

# Get final status
status = orchestrator.get_project_status(project_id)
print(f"\nFinal status: {status['status']}")
```

### Monitor Multiple Projects

```python
from orchestration import StateManager
import time

sm = StateManager()

# Get all active workflows
while True:
    workflows = sm.get_all_workflows()
    
    print("\n=== Active Projects ===")
    for workflow in workflows:
        if workflow.status.value == 'running':
            print(f"Project: {workflow.project_id}")
            print(f"  Stage: {workflow.current_stage}")
            print(f"  Prompt: {workflow.prompt[:50]}...")
    
    time.sleep(5)  # Update every 5 seconds
```

---

## 🎨 Build a Real-time Dashboard

### HTML + JavaScript Dashboard

```html
<!DOCTYPE html>
<html>
<head>
    <title>Multi-Agent Dashboard</title>
    <style>
        body { font-family: Arial; padding: 20px; }
        .project { border: 1px solid #ccc; padding: 15px; margin: 10px 0; }
        .stage { padding: 5px; margin: 5px 0; }
        .completed { background: #d4edda; }
        .running { background: #fff3cd; }
        .failed { background: #f8d7da; }
    </style>
</head>
<body>
    <h1>🚀 Multi-Agent System Dashboard</h1>
    <div id="projects"></div>

    <script>
        // Create new project
        async function createProject(prompt) {
            const response = await fetch('http://localhost:8000/projects', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({prompt, context: {}})
            });
            const data = await response.json();
            monitorProject(data.project_id);
        }

        // Monitor project via WebSocket
        function monitorProject(projectId) {
            const ws = new WebSocket(`ws://localhost:8000/ws/projects/${projectId}`);
            
            const projectDiv = document.createElement('div');
            projectDiv.className = 'project';
            projectDiv.id = projectId;
            projectDiv.innerHTML = `<h3>Project: ${projectId}</h3><div class="stages"></div>`;
            document.getElementById('projects').appendChild(projectDiv);
            
            ws.onmessage = (event) => {
                const update = JSON.parse(event.data);
                updateUI(projectId, update);
            };
        }

        // Update UI
        function updateUI(projectId, update) {
            const stagesDiv = document.querySelector(`#${projectId} .stages`);
            
            if (update.type === 'task_started') {
                const stageDiv = document.createElement('div');
                stageDiv.className = 'stage running';
                stageDiv.id = `${projectId}-${update.data.stage_name}`;
                stageDiv.textContent = `🔄 ${update.data.stage_name}`;
                stagesDiv.appendChild(stageDiv);
            }
            
            if (update.type === 'task_completed') {
                const stageDiv = document.getElementById(`${projectId}-${update.data.stage_name}`);
                stageDiv.className = 'stage completed';
                stageDiv.textContent = `✅ ${update.data.stage_name} (${update.data.confidence}%)`;
            }
            
            if (update.type === 'task_failed') {
                const stageDiv = document.getElementById(`${projectId}-${update.data.stage_name}`);
                stageDiv.className = 'stage failed';
                stageDiv.textContent = `❌ ${update.data.stage_name}`;
            }
        }

        // Example: Create a project
        // createProject("Build a blog platform");
    </script>
</body>
</html>
```

---

## 📊 Event Types You'll Receive

### Workflow Events
- `workflow_started` - Workflow begins
- `workflow_completed` - Workflow finishes successfully
- `workflow_failed` - Workflow fails permanently

### Task Events
- `task_started` - Agent starts working on a stage
- `task_completed` - Agent completes a stage
- `task_failed` - Agent fails a stage (may retry)

### Event Payload Examples

**workflow_started:**
```json
{
    "type": "workflow_started",
    "project_id": "abc-123",
    "timestamp": "2026-02-09T14:00:00Z",
    "data": {
        "prompt": "Build a blog platform"
    }
}
```

**task_completed:**
```json
{
    "type": "task_completed",
    "project_id": "abc-123",
    "timestamp": "2026-02-09T14:01:30Z",
    "data": {
        "stage_name": "product_interpretation",
        "confidence": 95.5,
        "outputs": {...}
    }
}
```

---

## 🚀 Quick Start Examples

### Example 1: CLI Real-time Monitoring
```bash
# Terminal 1: Start API server
python api/api_server.py

# Terminal 2: Create project with live updates
python api/cli.py create "Build a task manager" --watch
```

### Example 2: WebSocket Monitoring
```bash
# Terminal 1: Start API server
python api/api_server.py

# Terminal 2: Create project via API
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Build a blog"}'

# Terminal 3: Monitor via WebSocket (using wscat)
wscat -c ws://localhost:8000/ws/projects/<project-id>
```

### Example 3: Python SDK with Callbacks
```python
# See Python SDK example above
# Run: python your_script.py
```

---

## 💡 Best Practices

1. **Use CLI for Quick Testing** - Fastest way to see results
2. **Use WebSocket for Production** - Most efficient for real-time updates
3. **Use SSE for Simple Streaming** - Works with standard HTTP clients
4. **Use Python SDK for Integration** - Best for custom applications

---

## 🔧 Troubleshooting

**WebSocket not connecting:**
- Make sure API server is running: `python api/api_server.py`
- Check port 8000 is not blocked
- Verify project ID is correct

**No events received:**
- Check that workflow is actually running
- Verify you're subscribed to correct event types
- Check API server logs for errors

**Events delayed:**
- This is normal - agents take time to process
- Product interpretation: ~30 seconds
- Code generation: 2-3 minutes per agent
- Testing: 1-2 minutes

---

## 📞 Need Help?

- Check API docs: http://localhost:8000/docs
- View logs: `python api/cli.py logs <project-id> --follow`
- Check status: `python api/cli.py status <project-id>`

---

**Start monitoring in real-time now! 🚀**
