import asyncio
import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Add project root to path
sys.path.append('c:\\Users\\sunil\\Downloads\\eigent')

from core.agent_state import AgentState, CodeUnit, VerificationResult
from core.execution.graph_compiler import compile_v3_graph
from orchestration.orchestrator_v3 import OrchestratorV3
from api.api_server import app
from eigent_mcp import mcp

class TestEigentV3(unittest.IsolatedAsyncioTestCase):
    
    def setUp(self):
        # Mock environment
        os.environ["NVIDIA_API_KEY"] = "mock_key"
        self.orch = OrchestratorV3()
        self.api_client = TestClient(app)

    async def test_graph_flow_mock(self):
        """Test that the state graph can process a simple task flow."""
        graph = compile_v3_graph()
        # Mock ALL external calls globally within this test
        with patch('core.agent_nodes.call_model_async') as mock_call, \
             patch('core.agent_nodes.call_tool_async') as mock_tool, \
             patch('core.agent_nodes.run_in_sandbox') as mock_sandbox:
            
            mock_call.return_value = {
                "choices": [{"message": {"content": '{"subtasks": ["task1"]}'}}]
            }
            mock_tool.return_value = "Tool results"
            mock_sandbox.return_value = MagicMock(stdout="", stderr="", exit_code=0)

            # Specifically mock nodes to pass loops
            async def mock_val_node(s):
                for cu in s.code_units.values():
                    cu.verification = VerificationResult(ast_ok=True, schema_ok=True, tests_ok=True, details={"overall": "True"})
                return s
            
            async def mock_rev_node(s):
                s.status = "DONE"
                return s

            with patch('core.agent_nodes.interpreter_adapter', side_effect=lambda s: (setattr(s, 'code_units', {"main": CodeUnit(module="main", spec="test", source="print(1)")}), s)[1]), \
                 patch('core.agent_nodes.planner_cove_node', side_effect=lambda s: s), \
                 patch('core.agent_nodes.plan_validator_node', side_effect=lambda s: s), \
                 patch('core.agent_nodes.thinker_node', side_effect=lambda s: s), \
                 patch('core.agent_nodes.executor_code_node', side_effect=lambda s: s), \
                 patch('core.agent_nodes.executor_tests_node', side_effect=lambda s: s), \
                 patch('core.agent_nodes.executor_runtime_node', side_effect=lambda s: s), \
                 patch('core.agent_nodes.validator_node', side_effect=mock_val_node), \
                 patch('core.agent_nodes.reviewer_node', side_effect=mock_rev_node), \
                 patch('core.agent_nodes.finalizer_node', side_effect=lambda s: s), \
                 patch('core.agent_nodes.memory_update_node', side_effect=lambda s: s):

                state = AgentState(task="Build a test page")
                result = await graph.ainvoke(state)
                
                self.assertEqual(result.status, "DONE")
                print("✓ Graph Flow Test Passed")

    async def test_orchestrator_project_creation(self):
        """Test OrchestratorV3 project lifecycle."""
        project_id = self.orch.create_project("Test Prompt")
        self.assertIsNotNone(project_id)
        
        status = self.orch.get_project_status(project_id)
        self.assertEqual(status['prompt'], "Test Prompt")
        print("✓ Orchestrator Lifecycle Test Passed")

    def test_api_health(self):
        """Test API Health endpoint."""
        response = self.api_client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")
        print("✓ API Health Check Passed")

    async def test_mcp_generate_tool(self):
        """Test MCP generate_project tool definition."""
        with patch('orchestration.orchestrator_v3.OrchestratorV3.arun', return_value=asyncio.Future()):
            # await list_tools
            tools = await mcp.list_tools()
            self.assertTrue(any(t.name == "generate_project" for t in tools))
            print("✓ MCP Tool Definitions Verified")

if __name__ == '__main__':
    unittest.main()
