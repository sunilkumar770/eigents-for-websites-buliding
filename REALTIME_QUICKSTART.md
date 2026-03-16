# 🚀 Real-time Agent Interaction - Quick Reference

## 📍 Location
All examples are in: `c:\Users\sunil\Downloads\eigent\`

---

## ⚡ Quick Start (Choose One)

### 1. CLI with Live Progress (Easiest)
```bash
# Double-click or run:
start_realtime.bat

# Or directly:
python api/cli.py create "Build a blog platform" --watch
```
**What you'll see:** Real-time progress updates in terminal

---

### 2. Python Real-time Monitor
```bash
python examples/realtime_monitor.py
```
**What you'll see:** Formatted real-time updates with timestamps and durations

---

### 3. WebSocket Dashboard (Browser)
```bash
# Terminal 1: Start API server
python api/api_server.py

# Terminal 2: Open dashboard
start examples/websocket_client.html
```
**What you'll see:** Beautiful web dashboard with live updates

---

### 4. API Server + Manual Interaction
```bash
# Start server
python api/api_server.py

# Visit interactive docs
http://localhost:8000/docs
```
**What you'll see:** Interactive API documentation with real-time endpoints

---

## 📊 Available Examples

### 1. `realtime_monitor.py`
- **Purpose:** Monitor agents with Python callbacks
- **Features:** Timestamps, durations, formatted output
- **Run:** `python examples/realtime_monitor.py`

### 2. `websocket_client.html`
- **Purpose:** Web-based real-time dashboard
- **Features:** Visual progress, multiple projects, WebSocket streaming
- **Run:** Open in browser after starting API server

---

## 🎯 Real-time Interaction Methods

### Method 1: CLI Commands
```bash
# Create with live updates
python api/cli.py create "Your idea" --watch

# Stream logs
python api/cli.py logs <project-id> --follow

# Check status
python api/cli.py status <project-id>
```

### Method 2: WebSocket (JavaScript)
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/projects/<id>');
ws.onmessage = (event) => {
    const update = JSON.parse(event.data);
    console.log(update.type, update.data);
};
```

### Method 3: Server-Sent Events (HTTP)
```bash
curl -N http://localhost:8000/projects/<id>/progress
```

### Method 4: Python SDK
```python
from orchestration import WorkflowOrchestrator, MessageType

orchestrator = WorkflowOrchestrator(llm_adapter=adapter)
orchestrator.message_bus.subscribe(
    MessageType.TASK_COMPLETED,
    lambda msg: print(f"✅ {msg.payload['stage_name']}")
)
```

---

## 📡 Real-time Events

You'll receive these events:
- `workflow_started` - Project begins
- `task_started` - Agent starts a stage
- `task_completed` - Agent completes a stage (with confidence score)
- `task_failed` - Agent fails (will retry)
- `workflow_completed` - Project done!
- `workflow_failed` - Project failed

---

## 💡 Try These Examples

### Example 1: Watch a Blog Platform Being Built
```bash
python api/cli.py create "Build a blog platform with markdown editor and comments" --watch
```

### Example 2: Monitor Multiple Projects
```bash
# Terminal 1: Start API server
python api/api_server.py

# Terminal 2: Open dashboard
start examples/websocket_client.html

# Create multiple projects from the dashboard!
```

### Example 3: Custom Python Monitor
```bash
python examples/realtime_monitor.py
# Enter your app idea when prompted
```

---

## 🔧 Troubleshooting

**"Connection refused"**
- Start API server first: `python api/api_server.py`

**"No updates received"**
- Make sure project is actually running
- Check project status: `python api/cli.py status <id>`

**"WebSocket closed"**
- This is normal when workflow completes
- Reconnect for new projects

---

## 📚 Full Documentation

- **REAL_TIME_USAGE_GUIDE.md** - Complete guide with all methods
- **SUCCESS.md** - System overview and usage
- **GETTING_STARTED.md** - Installation and setup

---

**Start monitoring now! 🚀**

```bash
# Easiest way:
start_realtime.bat

# Or:
python api/cli.py create "Your app idea" --watch
```
