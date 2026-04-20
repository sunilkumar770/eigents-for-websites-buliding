"""
agent_framework.py
CLI entry point for the Multi-Agent AI Framework v3.
Run: python agent_framework.py "your task here"
"""
from __future__ import annotations

import asyncio
import sys

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from core.agent_state import AgentState
from core.graph_builder import build_graph


async def run_task(task: str) -> AgentState:
    """Execute a task through the async multi-agent graph."""
    graph = build_graph()
    initial_state = AgentState(task=task)
    
    # Run the graph
    final_state = await graph.ainvoke(initial_state)
    return final_state


def print_report(state: AgentState):
    """Print a clean CLI report of the execution results."""
    print("\n" + "="*80)
    print(f" TASK: {state.task}")
    print(f" STATUS: {state.status}")
    print("="*80)
    
    if state.subtasks:
        print("\n[ SUBTASKS ]")
        for i, st in enumerate(state.subtasks, 1):
            print(f"  {i}. {st}")
            
    if state.code_units:
        print("\n[ GENERATED MODULES ]")
        for module, cu in state.code_units.items():
            verify = "✅" if cu.verification and cu.verification.details.get("overall") == "True" else "❌"
            print(f"  {verify} {module}")
            
    if state.status == "DONE":
        print("\n✅ Task completed successfully.\n")
    else:
        print(f"\n❌ Task ended with status: {state.status}\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        user_task = " ".join(sys.argv[1:])
    else:
        user_task = input("Enter your task: ").strip()
        
    if not user_task:
        print("No task provided. Exiting.")
        sys.exit(1)
        
    try:
        final_state = asyncio.run(run_task(user_task))
        print_report(final_state)
    except KeyboardInterrupt:
        print("\nAborted by user.")
    except Exception as e:
        print(f"\nError running framework: {e}")
        import traceback
        traceback.print_exc()
