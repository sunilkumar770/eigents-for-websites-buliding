"""
Step-by-Step Agent Build
Runs each agent one at a time so you can see each step clearly.
"""
import sys
import os
import json
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.product_interpreter_agent import ProductInterpreterAgent
from agents.frontend_engineer_agent import FrontendEngineerAgent
from agents.backend_engineer_agent import BackendEngineerAgent
from agents.integration_agent import IntegrationAgent
from agents.testing_agent import TestingAgent
from agents.debug_agent import DebugAgent
from agents.security_agent import SecurityAgent
from agents.production_readiness_agent import ProductionReadinessAgent
from antigravity.llm.kimi_adapter import KimiAdapter


def print_header(text):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_result(result, agent_name):
    """Print agent result nicely"""
    if result.success:
        print(f"\n✅ {agent_name} COMPLETED")
        print(f"   Confidence: {result.confidence:.1f}%")
        if result.outputs:
            # Show key outputs
            for key in list(result.outputs.keys())[:5]:
                val = result.outputs[key]
                if isinstance(val, str):
                    print(f"   {key}: {val[:60]}...")
                elif isinstance(val, list):
                    print(f"   {key}: [{len(val)} items]")
                elif isinstance(val, dict):
                    print(f"   {key}: {{...}}")
    else:
        print(f"\n❌ {agent_name} FAILED")
        for err in result.errors[:3]:
            print(f"   Error: {err}")


def main():
    print_header("🚀 STEP-BY-STEP AGENT BUILD")
    print("\nBuilding: Rental Marketplace Platform")
    print("Mode: Mock responses for demonstration\n")
    
    # Use mock adapter
    adapter = KimiAdapter(api_key="MOCK_KEY")
    
    # Initial prompt
    prompt = """Build a rental marketplace where stores can list items for rent 
    and customers can browse, book, and pay for rentals with Google Maps integration."""
    
    context = {
        'tech_stack': {'frontend': 'Next.js', 'backend': 'Node.js', 'database': 'PostgreSQL'}
    }
    
    # Track results
    results = {}
    
    # ========== AGENT 1: Product Interpreter ==========
    print_header("AGENT 1/8: Product Interpreter")
    print("📝 Converting requirements to structured specs...")
    
    agent1 = ProductInterpreterAgent(llm_adapter=adapter)
    result1 = agent1.execute_with_retry({'prompt': prompt, 'context': context})
    print_result(result1, "Product Interpreter")
    results['requirements'] = result1.outputs if result1.success else {}
    
    input("\n⏸️  Press ENTER to continue to next agent...")
    
    # ========== AGENT 2: Frontend Engineer ==========
    print_header("AGENT 2/8: Frontend Engineer")
    print("🎨 Generating Next.js frontend components...")
    
    agent2 = FrontendEngineerAgent(llm_adapter=adapter)
    result2 = agent2.execute_with_retry({
        'requirements': results.get('requirements', {}),
        'tech_stack': {'frontend': 'Next.js'}
    })
    print_result(result2, "Frontend Engineer")
    results['frontend'] = result2.outputs if result2.success else {}
    
    input("\n⏸️  Press ENTER to continue to next agent...")
    
    # ========== AGENT 3: Backend Engineer ==========
    print_header("AGENT 3/8: Backend Engineer")
    print("⚙️  Generating Node.js backend API...")
    
    agent3 = BackendEngineerAgent(llm_adapter=adapter)
    result3 = agent3.execute_with_retry({
        'requirements': results.get('requirements', {}),
        'tech_stack': {'backend': 'Node.js', 'database': 'PostgreSQL'}
    })
    print_result(result3, "Backend Engineer")
    results['backend'] = result3.outputs if result3.success else {}
    
    input("\n⏸️  Press ENTER to continue to next agent...")
    
    # ========== AGENT 4: Integration Agent ==========
    print_header("AGENT 4/8: Integration Agent")
    print("🔗 Connecting frontend and backend...")
    
    agent4 = IntegrationAgent(llm_adapter=adapter)
    result4 = agent4.execute_with_retry({
        'frontend': results.get('frontend', {}),
        'backend': results.get('backend', {}),
        'requirements': results.get('requirements', {})
    })
    print_result(result4, "Integration Agent")
    results['integration'] = result4.outputs if result4.success else {}
    
    input("\n⏸️  Press ENTER to continue to next agent...")
    
    # ========== AGENT 5: Testing Agent ==========
    print_header("AGENT 5/8: Testing Agent")
    print("🧪 Generating test suites...")
    
    agent5 = TestingAgent(llm_adapter=adapter)
    result5 = agent5.execute_with_retry({
        'frontend': results.get('frontend', {}),
        'backend': results.get('backend', {}),
        'integration': results.get('integration', {})
    })
    print_result(result5, "Testing Agent")
    results['testing'] = result5.outputs if result5.success else {}
    
    input("\n⏸️  Press ENTER to continue to next agent...")
    
    # ========== AGENT 6: Debug Agent ==========
    print_header("AGENT 6/8: Debug Agent")
    print("🔍 Reviewing code quality...")
    
    agent6 = DebugAgent(llm_adapter=adapter)
    result6 = agent6.execute_with_retry({
        'frontend': results.get('frontend', {}),
        'backend': results.get('backend', {}),
        'test_results': results.get('testing', {})
    })
    print_result(result6, "Debug Agent")
    results['debug'] = result6.outputs if result6.success else {}
    
    input("\n⏸️  Press ENTER to continue to next agent...")
    
    # ========== AGENT 7: Security Agent ==========
    print_header("AGENT 7/8: Security Agent")
    print("🔒 Performing security audit...")
    
    agent7 = SecurityAgent(llm_adapter=adapter)
    result7 = agent7.execute_with_retry({
        'frontend': results.get('frontend', {}),
        'backend': results.get('backend', {}),
        'requirements': results.get('requirements', {})
    })
    print_result(result7, "Security Agent")
    results['security'] = result7.outputs if result7.success else {}
    
    input("\n⏸️  Press ENTER to continue to next agent...")
    
    # ========== AGENT 8: Production Readiness ==========
    print_header("AGENT 8/8: Production Readiness")
    print("🚀 Final validation for deployment...")
    
    agent8 = ProductionReadinessAgent(llm_adapter=adapter)
    result8 = agent8.execute_with_retry({
        'frontend': results.get('frontend', {}),
        'backend': results.get('backend', {}),
        'security': results.get('security', {}),
        'testing': results.get('testing', {})
    })
    print_result(result8, "Production Readiness")
    
    # ========== FINAL SUMMARY ==========
    print_header("🎉 ALL 8 AGENTS COMPLETED!")
    
    successful = sum(1 for r in [result1, result2, result3, result4, result5, result6, result7, result8] if r.success)
    print(f"\n✅ Successful agents: {successful}/8")
    
    print("\n📊 Agent Results Summary:")
    print(f"   1. Product Interpreter: {'✅' if result1.success else '❌'} ({result1.confidence:.0f}%)")
    print(f"   2. Frontend Engineer:   {'✅' if result2.success else '❌'} ({result2.confidence:.0f}%)")
    print(f"   3. Backend Engineer:    {'✅' if result3.success else '❌'} ({result3.confidence:.0f}%)")
    print(f"   4. Integration Agent:   {'✅' if result4.success else '❌'} ({result4.confidence:.0f}%)")
    print(f"   5. Testing Agent:       {'✅' if result5.success else '❌'} ({result5.confidence:.0f}%)")
    print(f"   6. Debug Agent:         {'✅' if result6.success else '❌'} ({result6.confidence:.0f}%)")
    print(f"   7. Security Agent:      {'✅' if result7.success else '❌'} ({result7.confidence:.0f}%)")
    print(f"   8. Production Ready:    {'✅' if result8.success else '❌'} ({result8.confidence:.0f}%)")
    
    print("\n" + "=" * 70)
    print("  🎊 RENTAL MARKETPLACE BUILD COMPLETE!")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
