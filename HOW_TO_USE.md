# 🚀 How to Use the Multi-Agent System

## ⚡ Two Ways to Use:

### 1️⃣ STANDALONE (No API Server) - Easiest!

```bash
python run_standalone.py
```

**What it does:**
- Runs directly without API server
- Shows real-time progress
- Perfect for quick testing

**Pros:** Simple, one command
**Cons:** No WebSocket, no multiple projects

---

### 2️⃣ WITH API SERVER (Full Features)

**Step 1: Start API Server**
```bash
# Terminal 1
python api/api_server.py
```

**Step 2: Use CLI**
```bash
# Terminal 2
python api/cli.py create "Build a blog platform" --watch
```

**Pros:** Full features, WebSocket, multiple projects
**Cons:** Requires 2 terminals

---

## 🎯 Quick Start

### Option A: Standalone (Recommended for First Time)
```bash
python run_standalone.py
```

### Option B: With API Server
```bash
# Terminal 1
python api/api_server.py

# Wait for "Uvicorn running on http://0.0.0.0:8000"

# Terminal 2 (new terminal)
python api/cli.py create "Your app idea" --watch
```

### Option C: Just Run Demo
```bash
python demo.py
```

---

## 📊 What You'll See

**Standalone/Demo:**
```
🚀 WORKFLOW STARTED
Prompt: Build a blog platform
Time: 14:30:00

🔄 Starting: Product Interpretation
✅ Completed: Product Interpretation (Confidence: 95.5%, 30.2s)

🔄 Starting: Frontend Generation
✅ Completed: Frontend Generation (Confidence: 92.0%, 120.5s)

🔄 Starting: Backend Generation
✅ Completed: Backend Generation (Confidence: 93.5%, 115.2s)

... and so on ...

🎉 WORKFLOW COMPLETED in 12.5 minutes
```

**With API Server:**
```
Creating project...
✅ Project created: abc-123-def

🔄 Product Interpretation... ✅ (95.5%)
🔄 Frontend Generation... ✅ (92.0%)
🔄 Backend Generation... ✅ (93.5%)
🔄 Integration... ✅ (90.0%)
🔄 Testing... ✅ (88.5%)
🔄 Security Audit... ✅ (94.0%)
🔄 Production Readiness... ✅ (91.5%)

🎉 Workflow completed!
```

---

## 🔧 Troubleshooting

### "Connection refused" when using CLI
**Problem:** API server not running
**Solution:** Start API server first in another terminal
```bash
python api/api_server.py
```

### Want to avoid API server?
**Solution:** Use standalone mode
```bash
python run_standalone.py
```

### "Module not found"
**Solution:** Make sure you're in the right directory
```bash
cd c:\Users\sunil\Downloads\eigent
python run_standalone.py
```

---

## 💡 Examples

### Standalone Mode
```bash
python run_standalone.py
# Enter: Build a recipe sharing platform
```

### API Server Mode
```bash
# Terminal 1
python api/api_server.py

# Terminal 2
python api/cli.py create "Build an e-commerce platform" --watch
```

### Just Demo
```bash
python demo.py
```

---

## 📁 Generated Code

All projects saved in:
```
c:\Users\sunil\Downloads\eigent\generated_projects\<project-id>\
```

---

## 🎉 Start Now!

**Easiest way:**
```bash
python run_standalone.py
```

**Full features:**
```bash
# Terminal 1: python api/api_server.py
# Terminal 2: python api/cli.py create "Your idea" --watch
```
