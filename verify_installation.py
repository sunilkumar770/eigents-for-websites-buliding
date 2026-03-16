"""
Verification Script

Tests the complete multi-agent system installation.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all imports"""
    print("Testing imports...")
    
    try:
        # Test agents
        from agents import BaseAgent, AgentType
        from agents import ProductInterpreterAgent
        from agents import FrontendEngineerAgent
        from agents import BackendEngineerAgent
        from agents import IntegrationAgent
        from agents import TestingAgent
        from agents import DebugAgent
        from agents import SecurityAgent
        from agents import ProductionReadinessAgent
        print("✅ All agent imports successful")
        
        # Test orchestration
        from orchestration import StateManager
        from orchestration import TaskQueue, TaskPriority
        from orchestration import MessageBus, MessageType
        from orchestration import WorkflowOrchestrator
        print("✅ All orchestration imports successful")
        
        # Test LLM adapter
        from antigravity.llm.kimi_adapter import KimiAdapter
        print("✅ LLM adapter import successful")
        
        return True
    
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


def test_state_manager():
    """Test state manager"""
    print("\nTesting state manager...")
    
    try:
        from orchestration import StateManager
        
        sm = StateManager(db_path="test_verify.db")
        workflow = sm.create_workflow("test-verify", "Test prompt")
        
        assert workflow.project_id == "test-verify"
        assert workflow.prompt == "Test prompt"
        
        sm.delete_workflow("test-verify")
        os.remove("test_verify.db")
        
        print("✅ State manager test passed")
        return True
    
    except Exception as e:
        print(f"❌ State manager test failed: {e}")
        return False


def test_task_queue():
    """Test task queue"""
    print("\nTesting task queue...")
    
    try:
        from orchestration import TaskQueue, TaskPriority
        
        queue = TaskQueue()
        task_id = queue.enqueue(
            "proj-1",
            "test",
            "agent",
            {},
            TaskPriority.HIGH
        )
        
        task = queue.dequeue()
        assert task is not None
        assert task.task_id == task_id
        
        print("✅ Task queue test passed")
        return True
    
    except Exception as e:
        print(f"❌ Task queue test failed: {e}")
        return False


def test_message_bus():
    """Test message bus"""
    print("\nTesting message bus...")
    
    try:
        from orchestration import MessageBus, MessageType
        
        bus = MessageBus()
        received = []
        
        def callback(msg):
            received.append(msg)
        
        bus.subscribe(MessageType.TASK_COMPLETED, callback)
        bus.publish(MessageType.TASK_COMPLETED, "proj-1", {"test": True})
        
        assert len(received) == 1
        
        print("✅ Message bus test passed")
        return True
    
    except Exception as e:
        print(f"❌ Message bus test failed: {e}")
        return False


def test_orchestrator():
    """Test orchestrator"""
    print("\nTesting orchestrator...")
    
    try:
        from orchestration import WorkflowOrchestrator
        from antigravity.llm.kimi_adapter import KimiAdapter
        
        # Use mock adapter
        adapter = KimiAdapter(api_key="MOCK_KEY")
        orchestrator = WorkflowOrchestrator(llm_adapter=adapter)
        
        # Create project
        project_id = orchestrator.create_project(
            prompt="Test app",
            context={}
        )
        
        assert project_id is not None
        
        # Get status
        status = orchestrator.get_project_status(project_id)
        assert status['project_id'] == project_id
        
        # Cleanup
        orchestrator.state_manager.delete_workflow(project_id)
        os.remove("workflow_state.db")
        
        print("✅ Orchestrator test passed")
        return True
    
    except Exception as e:
        print(f"❌ Orchestrator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 80)
    print("🧪 Multi-Agent System Verification")
    print("=" * 80)
    
    tests = [
        ("Imports", test_imports),
        ("State Manager", test_state_manager),
        ("Task Queue", test_task_queue),
        ("Message Bus", test_message_bus),
        ("Orchestrator", test_orchestrator),
    ]
    
    results = []
    for name, test_func in tests:
        result = test_func()
        results.append((name, result))
    
    print("\n" + "=" * 80)
    print("📊 Test Results")
    print("=" * 80)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! System is ready to use.")
        print("\nNext steps:")
        print("  1. Set NVIDIA_API_KEY in .env file")
        print("  2. Run: python demo.py")
        print("  3. Or: python api/cli.py create \"Your app idea\" --watch")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
    
    print("=" * 80)


if __name__ == '__main__':
    main()
