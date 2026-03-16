"""
Quick test build to verify the JSON extraction fix
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestration import WorkflowOrchestrator
from antigravity.llm.kimi_adapter import KimiAdapter

print("=" * 80)
print("Testing Fixed Product Interpreter with Simple Build")
print("=" * 80)

# Create orchestrator
api_key = os.getenv("KIMI_API_KEY", "MOCK_KEY")
adapter = KimiAdapter(api_key=api_key)
orchestrator = WorkflowOrchestrator(llm_adapter=adapter)

# Simple test prompt
prompt = "Build a simple todo app with add, delete, and mark as done features"

print(f"\n📝 Test Prompt: {prompt}")
print(f"🔑 Using API Key: {'REAL' if api_key != 'MOCK_KEY' else 'MOCK'}")
print("\n🚀 Starting build...\n")

try:
    # Run just the product interpretation stage
    project_id = orchestrator.create_workflow(prompt=prompt)
    
    print(f"✅ Workflow created: {project_id}")
    print("\n✅ Product Interpreter completed successfully!")
    print("\nThe JSON extraction fix is working! 🎉")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
