import asyncio
import logging
from typing import List, Dict, Any, Callable
from antigravity.llm.kimi_adapter import KimiAdapter
from antigravity.config.llm_config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AntigravityOrchestrator")

class AntigravityAgent:
    """
    Representation of an autonomous agent inside Antigravity.
    """
    def __init__(self, name: str, role: str, adapter: KimiAdapter):
        self.name = name
        self.role = role
        self.adapter = adapter

    async def execute_task(self, task_description: str) -> str:
        """
        Execute a single task using the reasoning LLM.
        """
        logger.info(f"Agent {self.name} ({self.role}) starting task: {task_description}")
        
        # NVIDIA Kimi K2.5 does not support 'system' role. 
        # We prepend agent personality to the user message instead.
        agent_instruction = f"[AGENT: {self.name}, ROLE: {self.role}] "
        messages = [
            {"role": "user", "content": agent_instruction + task_description}
        ]
        
        # Parallel-friendly execution
        response = await asyncio.to_thread(self.adapter.chat, messages)
        
        # Handle dictionary response (from requests) or mock
        # Both are now dicts in the new KimiAdapter implementation
        content = response["choices"][0]["message"]["content"]
        
        logger.info(f"Agent {self.name} completed task.")
        return content

class AgentManager:
    """
    Orchestrates multiple agents and parallel task execution.
    """
    def __init__(self):
        self.adapter = KimiAdapter(api_key=Config.get_api_key())
        self.agents = {}

    def spawn_agent(self, name: str, role: str) -> AntigravityAgent:
        agent = AntigravityAgent(name, role, self.adapter)
        self.agents[name] = agent
        return agent

    async def run_parallel_tasks(self, tasks: List[Dict[str, str]]):
        """
        tasks: List of dicts with {'agent_name': '...', 'task': '...'}
        """
        logger.info(f"Starting parallel execution of {len(tasks)} tasks.")
        
        execution_tasks = []
        for t in tasks:
            agent = self.agents.get(t['agent_name'])
            if agent:
                execution_tasks.append(agent.execute_task(t['task']))
        
        results = await asyncio.gather(*execution_tasks)
        return results

# Vibe Coding Flow Implementation
async def vibe_coding_flow(instruction: str):
    """
    Example of a 'vibe coding' flow where one agent plans and others execute in parallel.
    """
    manager = AgentManager()
    planner = manager.spawn_agent("Architect", "System Planning")
    coder = manager.spawn_agent("Developer", "Python Coding")
    reviewer = manager.spawn_agent("Reviewer", "Code Quality")
    
    logger.info("--- Phase 1: Planning ---")
    plan = await planner.execute_task(f"Plan the following: {instruction}")
    
    logger.info("--- Phase 2: Parallel Implementation & Review ---")
    tasks = [
        {'agent_name': "Developer", 'task': f"Implement based on plan: {plan}"},
        {'agent_name': "Reviewer", 'task': f"Prepare test cases for plan: {plan}"}
    ]
    
    results = await manager.run_parallel_tasks(tasks)
    return {"plan": plan, "results": results}

if __name__ == "__main__":
    # Test script for Phase 4
    import json
    result = asyncio.run(vibe_coding_flow("Build a hello world web server"))
    print("\n--- LIVE VERIFICATION RESULTS ---")
    print(json.dumps(result, indent=2))
