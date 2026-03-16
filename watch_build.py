"""
Real-time Build Monitor - Shows live agent actions
"""
import time
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestration import StateManager

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    print("=" * 80)
    print("  🚀 RENTAL MARKETPLACE - LIVE BUILD MONITOR")
    print("=" * 80)
    print()

def monitor_build():
    """Monitor the build in real-time"""
    sm = StateManager()
    last_stage = None
    
    while True:
        clear_screen()
        print_header()
        
        # Get all workflows using list_workflows method
        workflows = sm.list_workflows(limit=10)
        
        if not workflows:
            print("⏳ Waiting for build to start...")
            time.sleep(2)
            continue
        
        # Get the latest workflow
        workflow = workflows[-1]
        
        print(f"📋 Project ID: {workflow.project_id}")
        print(f"📝 Prompt: {workflow.prompt[:70]}...")
        print(f"⏱️  Status: {workflow.status.value.upper()}")
        print(f"🔄 Current Stage: {workflow.current_stage or 'Initializing'}")
        print()
        print("=" * 80)
        print("  AGENT PROGRESS")
        print("=" * 80)
        print()
        
        # Show stage progress
        stages = [
            ("product_interpretation", "Product Interpreter"),
            ("frontend_generation", "Frontend Engineer"),
            ("backend_generation", "Backend Engineer"),
            ("integration", "Integration Agent"),
            ("testing", "Testing Agent"),
            ("debug", "Debug Agent"),
            ("security_audit", "Security Agent"),
            ("production_readiness", "Production Readiness")
        ]
        
        # Get all stages for this project
        all_stages = sm.get_stages(workflow.project_id)
        stage_dict = {s.stage_name: s for s in all_stages}
        
        for stage_key, stage_name in stages:
            # Check if stage exists in results
            if stage_key in stage_dict:
                stage_state = stage_dict[stage_key]
                if stage_state.status.value == 'completed':
                    icon = "✅"
                    status = f"COMPLETED (Confidence: {stage_state.confidence:.1f}%)"
                elif stage_state.status.value == 'running':
                    icon = "🔄"
                    status = "IN PROGRESS..."
                elif stage_state.status.value == 'failed':
                    icon = "❌"
                    status = f"FAILED - {stage_state.error_message[:40] if stage_state.error_message else 'Unknown error'}"
                else:
                    icon = "⏳"
                    status = "PENDING"
            else:
                icon = "⏳"
                status = "PENDING"
            
            print(f"{icon} {stage_name:25} {status}")
        
        print()
        print("=" * 80)
        
        # Check if workflow is complete
        if workflow.status.value in ['completed', 'failed']:
            print()
            if workflow.status.value == 'completed':
                print("🎉 BUILD COMPLETED!")
                print(f"\n📁 Generated code: generated_projects/{workflow.project_id}/")
            else:
                print("❌ BUILD FAILED!")
            print()
            print("Press Ctrl+C to exit...")
            break
        
        # Show current action
        if workflow.current_stage != last_stage:
            last_stage = workflow.current_stage
        
        print(f"\n⏳ Refreshing in 3 seconds... (Press Ctrl+C to exit)")
        
        try:
            time.sleep(3)
        except KeyboardInterrupt:
            print("\n\n👋 Monitoring stopped.")
            break

if __name__ == '__main__':
    try:
        monitor_build()
    except KeyboardInterrupt:
        print("\n\n👋 Monitoring stopped.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
