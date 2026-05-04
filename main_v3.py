"""
main_v3.py

Terminal entry point for the modernized Eigent Framework v3.
Usage: python main_v3.py "Build a recipe sharing platform"
"""

import sys
import asyncio
import logging
from orchestration.orchestrator_v3 import OrchestratorV3

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

async def main():
    if len(sys.argv) < 2:
        print("Usage: python main_v3.py \"your product idea\"")
        return

    prompt = sys.argv[1]
    setup_logging()
    
    print("\n" + "="*50)
    print("🚀 Eigent v3: Multi-Agent Generation Started")
    print(f"Prompt: {prompt}")
    print("="*50 + "\n")

    orch = OrchestratorV3()
    project_id = orch.create_project(prompt)
    
    print(f"Project ID: {project_id}\n")
    
    # Run the graph
    await orch.arun(project_id)
    
    # Check final status
    status = orch.get_project_status(project_id)
    print("\n" + "="*50)
    print(f"✅ Project Final Status: {status['status'].upper()}")
    print("="*50)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopping orchestrator...")
