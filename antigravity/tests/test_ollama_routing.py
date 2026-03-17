"""
Verification script for 3-model Ollama routing.
Prints which model each agent type will be assigned.
"""
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from antigravity.llm.ollama_adapter import OllamaAdapter

def test_routing():
    print("=== Testing 3-Model Ollama Routing ===\n")
    
    # Mock env vars for test if not set
    os.environ["OLLAMA_REASONER_MODEL"] = os.getenv("OLLAMA_REASONER_MODEL", "deepseek-r1:14b")
    os.environ["OLLAMA_CODER_MODEL"] = os.getenv("OLLAMA_CODER_MODEL", "qwen2.5-coder:14b")
    os.environ["OLLAMA_GENERAL_MODEL"] = os.getenv("OLLAMA_GENERAL_MODEL", "gemma3:12b")

    adapter = OllamaAdapter(mock_mode=True)
    
    agents = [
        "product_interpreter",
        "frontend_engineer",
        "backend_engineer",
        "integration",
        "testing",
        "debug",
        "security",
        "production_readiness",
        "unknown_agent"
    ]
    
    print(f"Configured Models:")
    print(f"  Reasoner: {adapter.reasoner_model}")
    print(f"  Coder:    {adapter.coder_model}")
    print(f"  General:  {adapter.general_model}\n")
    
    print(f"{'Agent Type':<25} | {'Assigned Model'}")
    print(f"{'-'*25}-|-{'-'*30}")
    
    for agent in agents:
        model = adapter._select_model_for_agent(agent)
        print(f"{agent:<25} | {model}")

if __name__ == "__main__":
    test_routing()
