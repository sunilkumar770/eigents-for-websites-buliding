"""
Real-time Agent Monitoring Example

This script demonstrates how to monitor agents in real-time using the Python SDK.
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestration import WorkflowOrchestrator, MessageBus, MessageType
from antigravity.llm.kimi_adapter import KimiAdapter


class RealTimeMonitor:
    """Monitor agent workflow in real-time"""
    
    def __init__(self):
        self.start_time = None
        self.stage_times = {}
        
    def on_workflow_started(self, message):
        """Called when workflow starts"""
        self.start_time = datetime.now()
        print("=" * 80)
        print("🚀 WORKFLOW STARTED")
        print("=" * 80)
        print(f"Project ID: {message.project_id}")
        print(f"Prompt: {message.payload.get('prompt', 'N/A')}")
        print(f"Started at: {self.start_time.strftime('%H:%M:%S')}")
        print()
    
    def on_task_started(self, message):
        """Called when a task/stage starts"""
        stage = message.payload['stage_name']
        self.stage_times[stage] = datetime.now()
        
        print(f"🔄 STARTING: {stage}")
        print(f"   Time: {datetime.now().strftime('%H:%M:%S')}")
        print()
    
    def on_task_completed(self, message):
        """Called when a task/stage completes"""
        stage = message.payload['stage_name']
        confidence = message.payload['confidence']
        
        # Calculate duration
        if stage in self.stage_times:
            duration = (datetime.now() - self.stage_times[stage]).total_seconds()
            duration_str = f"{duration:.1f}s"
        else:
            duration_str = "N/A"
        
        print(f"✅ COMPLETED: {stage}")
        print(f"   Confidence: {confidence}%")
        print(f"   Duration: {duration_str}")
        print()
    
    def on_task_failed(self, message):
        """Called when a task/stage fails"""
        stage = message.payload['stage_name']
        error = message.payload.get('error', 'Unknown error')
        retry_count = message.payload.get('retry_count', 0)
        
        print(f"❌ FAILED: {stage}")
        print(f"   Error: {error}")
        print(f"   Retry count: {retry_count}")
        print()
    
    def on_workflow_completed(self, message):
        """Called when workflow completes"""
        total_duration = (datetime.now() - self.start_time).total_seconds()
        
        print("=" * 80)
        print("🎉 WORKFLOW COMPLETED")
        print("=" * 80)
        print(f"Total duration: {total_duration:.1f}s ({total_duration/60:.1f} minutes)")
        print()
        
        # Print stage breakdown
        print("Stage Breakdown:")
        for stage, start_time in self.stage_times.items():
            print(f"  - {stage}")
    
    def on_workflow_failed(self, message):
        """Called when workflow fails"""
        print("=" * 80)
        print("⚠️  WORKFLOW FAILED")
        print("=" * 80)
        print(f"Stage: {message.payload.get('stage_name', 'Unknown')}")
        print(f"Error: {message.payload.get('error', 'Unknown error')}")
        print()


def main():
    """Run real-time monitoring example"""
    
    # Get API key
    api_key = os.getenv('NVIDIA_API_KEY', 'MOCK_KEY')
    
    if api_key == 'MOCK_KEY':
        print("⚠️  Using MOCK_KEY - set NVIDIA_API_KEY in .env for real usage\n")
    
    # Initialize
    adapter = KimiAdapter(api_key=api_key)
    orchestrator = WorkflowOrchestrator(llm_adapter=adapter)
    
    # Create monitor
    monitor = RealTimeMonitor()
    
    # Subscribe to all events
    bus = orchestrator.message_bus
    bus.subscribe(MessageType.WORKFLOW_STARTED, monitor.on_workflow_started)
    bus.subscribe(MessageType.TASK_STARTED, monitor.on_task_started)
    bus.subscribe(MessageType.TASK_COMPLETED, monitor.on_task_completed)
    bus.subscribe(MessageType.TASK_FAILED, monitor.on_task_failed)
    bus.subscribe(MessageType.WORKFLOW_COMPLETED, monitor.on_workflow_completed)
    bus.subscribe(MessageType.WORKFLOW_FAILED, monitor.on_workflow_failed)
    
    # Create project
    prompt = input("Enter your app idea: ").strip()
    if not prompt:
        prompt = "Build a simple blog platform with posts and comments"
    
    print(f"\n📝 Creating project: {prompt}\n")
    
    project_id = orchestrator.create_project(
        prompt=prompt,
        context={'target_audience': 'general users'}
    )
    
    # Run workflow (events will fire in real-time)
    orchestrator.run(max_iterations=50)
    
    # Get final status
    status = orchestrator.get_project_status(project_id)
    
    print("\n" + "=" * 80)
    print("📊 FINAL STATUS")
    print("=" * 80)
    print(f"Status: {status['status']}")
    print(f"Stages completed: {len([s for s in status['stages'] if s['status'] == 'completed'])}")
    
    if status['errors']:
        print(f"\nErrors ({len(status['errors'])}):")
        for error in status['errors']:
            print(f"  - {error}")
    
    print("\n" + "=" * 80)


if __name__ == '__main__':
    main()
