"""
Standalone Real-time Demo - No API Server Required

This script runs the multi-agent system directly without needing the API server.
Perfect for quick testing and seeing the system in action.
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestration import WorkflowOrchestrator, MessageType
from antigravity.llm.kimi_adapter import KimiAdapter


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def print_stage(icon, stage, details=""):
    """Print stage update"""
    print(f"{icon} {stage}")
    if details:
        print(f"   {details}")


class SimpleMonitor:
    """Simple real-time monitor"""
    
    def __init__(self):
        self.start_time = None
        self.stage_times = {}
    
    def on_workflow_started(self, msg):
        self.start_time = datetime.now()
        print_header("🚀 WORKFLOW STARTED")
        print(f"Prompt: {msg.payload.get('prompt', 'N/A')}")
        print(f"Time: {self.start_time.strftime('%H:%M:%S')}\n")
    
    def on_task_started(self, msg):
        stage = msg.payload['stage_name']
        self.stage_times[stage] = datetime.now()
        print_stage("🔄", f"Starting: {stage.replace('_', ' ').title()}")
    
    def on_task_completed(self, msg):
        stage = msg.payload['stage_name']
        confidence = msg.payload['confidence']
        
        duration = ""
        if stage in self.stage_times:
            secs = (datetime.now() - self.stage_times[stage]).total_seconds()
            duration = f"({secs:.1f}s)"
        
        print_stage("✅", f"Completed: {stage.replace('_', ' ').title()}", 
                   f"Confidence: {confidence}% {duration}")
    
    def on_task_failed(self, msg):
        stage = msg.payload['stage_name']
        error = msg.payload.get('error', 'Unknown')
        print_stage("❌", f"Failed: {stage.replace('_', ' ').title()}", f"Error: {error}")
    
    def on_workflow_completed(self, msg):
        total = (datetime.now() - self.start_time).total_seconds()
        print_header(f"🎉 WORKFLOW COMPLETED in {total/60:.1f} minutes")


def main():
    """Run standalone demo"""
    
    print_header("Multi-Agent System - Standalone Demo")
    print("\nThis demo runs WITHOUT the API server.")
    print("You'll see real-time updates as agents work.\n")
    
    # Get API key
    api_key = os.getenv('NVIDIA_API_KEY', 'MOCK_KEY')
    
    if api_key == 'MOCK_KEY':
        print("⚠️  Using MOCK_KEY (simulated responses)")
        print("   Set NVIDIA_API_KEY in .env for real LLM usage\n")
    
    # Get user input
    print("What would you like to build?")
    print("Examples:")
    print("  - Build a blog platform with markdown editor")
    print("  - Build a task management app with Kanban boards")
    print("  - Build a recipe sharing platform\n")
    
    prompt = input("Your idea: ").strip()
    if not prompt:
        prompt = "Build a simple blog platform"
        print(f"Using default: {prompt}\n")
    
    # Initialize
    adapter = KimiAdapter(api_key=api_key)
    orchestrator = WorkflowOrchestrator(llm_adapter=adapter)
    
    # Set up monitoring
    monitor = SimpleMonitor()
    bus = orchestrator.message_bus
    bus.subscribe(MessageType.WORKFLOW_STARTED, monitor.on_workflow_started)
    bus.subscribe(MessageType.TASK_STARTED, monitor.on_task_started)
    bus.subscribe(MessageType.TASK_COMPLETED, monitor.on_task_completed)
    bus.subscribe(MessageType.TASK_FAILED, monitor.on_task_failed)
    bus.subscribe(MessageType.WORKFLOW_COMPLETED, monitor.on_workflow_completed)
    
    # Create and run
    project_id = orchestrator.create_project(prompt=prompt, context={})
    print(f"\n📋 Project ID: {project_id}\n")
    
    # Run workflow
    orchestrator.run(max_iterations=50)
    
    # Show results
    status = orchestrator.get_project_status(project_id)
    
    print_header("📊 FINAL STATUS")
    print(f"Status: {status['status']}")
    print(f"Stages completed: {len([s for s in status['stages'] if s['status'] == 'completed'])}/8")
    
    if status['errors']:
        print(f"\n⚠️  Errors: {len(status['errors'])}")
        for error in status['errors'][:3]:  # Show first 3
            print(f"  - {error}")
    
    print("\n" + "=" * 80)
    print("\n✅ Demo complete!")
    print(f"\nGenerated code would be in: generated_projects/{project_id}/")
    print("\nTo use the API server and CLI:")
    print("  1. Terminal 1: python api/api_server.py")
    print("  2. Terminal 2: python api/cli.py create \"Your idea\" --watch")
    print("\n" + "=" * 80 + "\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
