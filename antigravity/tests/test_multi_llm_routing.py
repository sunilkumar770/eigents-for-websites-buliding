import sys
import os

# Add root directory to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import logging
from antigravity.llm.setup_llm import build_llm_adapter
from agents.base_agent import AgentType

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_router_logic():
    print("\n--- Testing Multi-LLM Router Logic ---")
    
    # Build adapter
    adapter = build_llm_adapter()
    
    print(f"\nResulting Adapter Type: {type(adapter).__name__}")
    
    # Check routing if it's a router
    from antigravity.llm.llm_router import MultiLLMRouter
    if isinstance(adapter, MultiLLMRouter):
        print("\nRouting Table:")
        for agent, target in adapter.routing.items():
            print(f"  {agent:25s} -> {target}")
            
        # Test a mock call (routing only, doesn't call API yet)
        print("\nTesting Routing Resolution:")
        for agent_type in [
            "product_interpreter", 
            "debug", 
            "testing", 
            "backend_engineer"
        ]:
            resolved = adapter._resolve_adapter(agent_type)
            print(f"  {agent_type:25s} -> {resolved}")
    else:
        print("\nNote: Router not active (only one LLM backend detected or both missing).")

if __name__ == "__main__":
    test_router_logic()
