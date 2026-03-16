"""
Bridge Script

Allows Antigravity (via Terminal) to trigger Eigent logic.
Usage: python bridge.py "optimize database queries"
"""
import sys
import os

# Add root directory to sys.path
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from antigravity.llm.llm_router import route_task

def run_eigent_parallel():
    if len(sys.argv) < 2:
        print("Usage: python bridge.py \"Your task description\"")
        sys.exit(1)
        
    task = sys.argv[1]
    # Optionally accept agent_type as second arg
    agent_type = sys.argv[2] if len(sys.argv) > 2 else "product_interpreter"
    
    print(f"🚀 Antigravity handing off to Eigent [{agent_type}]: {task}")
    
    try:
        result = route_task(task, agent_type=agent_type)
        print("\n--- Eigent Result ---")
        print(result)
        return result
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run_eigent_parallel()
