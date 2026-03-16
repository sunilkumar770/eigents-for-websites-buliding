"""
Multi-Agent System Demo

Demonstrates the complete workflow orchestrator coordinating all 8 agents.
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestration.workflow_orchestrator import WorkflowOrchestrator


def main():
    """Demo the multi-agent system with orchestrator"""
    
    # Auto-detect and build the best available LLM adapter:
    # - Kimi K2.5 (NVIDIA API) if NVIDIA_API_KEY is set
    # - Ollama (local)          if Ollama is running
    # - MultiLLMRouter          if both are available (recommended)
    from antigravity.llm.setup_llm import build_llm_adapter
    adapter = build_llm_adapter()
    
    # Initialize orchestrator
    orchestrator = WorkflowOrchestrator(llm_adapter=adapter)
    
    print("=" * 80)
    print("🚀 MULTI-AGENT WEB DEVELOPMENT SYSTEM")
    print("=" * 80)
    
    # Create project
    prompt = "Build a recipe sharing platform where users can post recipes, rate them, and leave comments"
    context = {
        'target_audience': 'home cooks and food enthusiasts',
        'key_features': [
            'recipe posting',
            'ratings and reviews',
            'user profiles',
            'search and filtering'
        ]
    }
    
    print(f"\n📝 Prompt: {prompt}\n")
    
    project_id = orchestrator.create_project(prompt=prompt, context=context)
    print(f"✅ Created project: {project_id}\n")
    
    # Process workflow
    print("🔄 Processing workflow...\n")
    orchestrator.run(max_iterations=50)
    
    # Get final status
    status = orchestrator.get_project_status(project_id)
    
    print("\n" + "=" * 80)
    print("📊 FINAL STATUS")
    print("=" * 80)
    print(f"\nProject ID: {project_id}")
    print(f"Status: {status['status']}")
    print(f"Current Stage: {status['current_stage']}")
    print(f"\nStages:")
    for stage in status['stages']:
        status_icon = "✅" if stage['status'] == 'completed' else "⚠️" if stage['status'] == 'failed' else "🔄"
        print(f"  {status_icon} {stage['name']}: {stage['status']} (confidence: {stage['confidence']}%)")
    
    if status['errors']:
        print(f"\n⚠️ Errors: {len(status['errors'])}")
        for error in status['errors']:
            print(f"  - {error}")
    
    print(f"\n{'🎉 WORKFLOW COMPLETED!' if status['status'] == 'completed' else '⚠️ WORKFLOW INCOMPLETE'}")
    print("=" * 80)


if __name__ == '__main__':
    main()
