"""
Test the fixed Product Interpreter Agent with various response formats
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.product_interpreter_agent import ProductInterpreterAgent
from antigravity.llm.kimi_adapter import KimiAdapter

print("=" * 80)
print("Testing Product Interpreter Agent - JSON Extraction")
print("=" * 80)

# Create agent
adapter = KimiAdapter(api_key="MOCK_KEY")
agent = ProductInterpreterAgent(llm_adapter=adapter)

# Test various response formats
test_cases = [
    ("Pure JSON", '{"product_name": "Test App", "description": "A test"}'),
    ("Markdown JSON block", '```json\n{"product_name": "Test App", "description": "A test"}\n```'),
    ("Markdown block no lang", '```\n{"product_name": "Test App", "description": "A test"}\n```'),
    ("With explanation", 'Here is the result:\n{"product_name": "Test App", "description": "A test"}'),
    ("With trailing text", '{"product_name": "Test App", "description": "A test"}\nHope this helps!'),
]

print("\n✅ Testing JSON extraction:")
for name, response in test_cases:
    try:
        result = agent._extract_json_from_response(response)
        print(f"  ✅ {name}: {result.get('product_name', 'N/A')}")
    except Exception as e:
        print(f"  ❌ {name}: {str(e)[:50]}")

print("\n" + "=" * 80)
print("✅ All JSON extraction tests completed!")
print("=" * 80)
