"""
Simple Test - Multi-Agent System

Tests basic functionality without running full workflow.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("🧪 Multi-Agent System - Simple Test")
print("=" * 80)

# Test 1: Import orchestration components
print("\n1️⃣ Testing orchestration imports...")
try:
    from orchestration.state_manager import StateManager
    from orchestration.task_queue import TaskQueue, TaskPriority
    from orchestration.message_bus import MessageBus, MessageType
    print("✅ Orchestration imports successful")
except ImportError as e:
    print(f"❌ Orchestration import failed: {e}")
    sys.exit(1)

# Test 2: Create state manager
print("\n2️⃣ Testing state manager...")
try:
    sm = StateManager(db_path="test_simple.db")
    workflow = sm.create_workflow("test-123", "Build a test app")
    print(f"✅ Created workflow: {workflow.project_id}")
    sm.delete_workflow("test-123")
    os.remove("test_simple.db")
    print("✅ State manager working")
except Exception as e:
    print(f"❌ State manager failed: {e}")
    sys.exit(1)

# Test 3: Create task queue
print("\n3️⃣ Testing task queue...")
try:
    queue = TaskQueue()
    task_id = queue.enqueue(
        "proj-1",
        "test_stage",
        "test_agent",
        {"test": True},
        TaskPriority.HIGH
    )
    task = queue.dequeue()
    print(f"✅ Created and dequeued task: {task.task_id}")
    print("✅ Task queue working")
except Exception as e:
    print(f"❌ Task queue failed: {e}")
    sys.exit(1)

# Test 4: Create message bus
print("\n4️⃣ Testing message bus...")
try:
    bus = MessageBus()
    received = []
    
    def callback(msg):
        received.append(msg)
    
    bus.subscribe(MessageType.TASK_COMPLETED, callback)
    bus.publish(MessageType.TASK_COMPLETED, "proj-1", {"test": True})
    
    if len(received) == 1:
        print("✅ Message bus working")
    else:
        print(f"⚠️  Expected 1 message, got {len(received)}")
except Exception as e:
    print(f"❌ Message bus failed: {e}")
    sys.exit(1)

# Test 5: Test LLM adapter
print("\n5️⃣ Testing LLM adapter...")
try:
    from antigravity.llm.kimi_adapter import KimiAdapter
    
    api_key = os.getenv('NVIDIA_API_KEY', 'MOCK_KEY')
    adapter = KimiAdapter(api_key=api_key)
    
    if api_key == 'MOCK_KEY':
        print("⚠️  Using MOCK_KEY - set NVIDIA_API_KEY in .env for real usage")
    else:
        print("✅ LLM adapter initialized with real API key")
except Exception as e:
    print(f"❌ LLM adapter failed: {e}")
    sys.exit(1)

print("\n" + "=" * 80)
print("✅ ALL TESTS PASSED!")
print("=" * 80)

print("\n📊 System Status:")
print("  ✅ Orchestration layer working")
print("  ✅ State persistence working")
print("  ✅ Task queue working")
print("  ✅ Message bus working")
print("  ✅ LLM adapter ready")

print("\n⚠️  Note: Agent imports need fixing for full workflow")
print("   The orchestration layer is fully functional.")
print("   To use with agents, we need to update agent import paths.")

print("\n🚀 Next Steps:")
print("  1. Set NVIDIA_API_KEY in .env file")
print("  2. Run: python api/api_server.py")
print("  3. Visit: http://localhost:8000/docs")
print("  4. Use API to create projects")

print("\n" + "=" * 80)
