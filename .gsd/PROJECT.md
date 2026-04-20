# Eigent Multi-Agent Framework v3 Upgrade

## Goal
Upgrade the existing eigent agent system to the Multi-Agent AI Framework v3 design:
- Async LangGraph-style `SimpleStateGraph` replacing the synchronous `NexusLoop`
- Pydantic `AgentState` schema (Plan, Thinking, CodeUnit, SandboxRun, VerificationResult)
- Multi-model async routing: Minimax (supervisor/planner), Kimi (thinker/reviewer), GLM (coder/tests), Nemotron (debugger), Gemma-local (memory)
- MCP-style tool stub (`call_tool_async`)
- E2B sandbox stub (`run_in_sandbox`)
- Tiered memory stub (`memory_store_async` / `memory_retrieve_async`)
- FastAPI REST server (`POST /run`, `GET /history`, `GET /health`)
- CoVe (Chain-of-Verification) planning in planner node
- Bug-free `reviewer_node` (fix the `user_msg` undefined + wrong dict access bugs in the reference code)

## Existing Structure (DO NOT DELETE)
- `agents/` – 8 specialised agent classes (keep, but update to call new async nodes)
- `core/llm_router.py` – LLMRouter (keep for Ollama fallback, but add async support)
- `core/memory.py` – AgentMemory (keep, extend for async)
- `core/loop.py` – NexusLoop (keep for backward-compat, but deprecate in favour of new graph)
- `core/executor.py`, `core/file_manager.py` – keep as-is
- `antigravity/`, `api/`, `orchestration/` – keep as-is

## Deliverables

### New Files to Create
1. `core/agent_state.py` – All Pydantic state models (AgentState, Plan, Thinking, CodeUnit, SandboxRun, VerificationResult, ReviewResult)
2. `core/model_caller.py` – `call_model_async()` async httpx-based multi-model caller with MODEL_CONFIG
3. `core/tool_stubs.py` – `call_tool_async`, `run_in_sandbox`, `memory_store_async`, `memory_retrieve_async`
4. `core/state_graph.py` – `SimpleStateGraph` + `NodeFunc` (lightweight LangGraph stand-in)
5. `core/agent_nodes.py` – All 10 async node functions: supervisor, planner_cove, plan_validator, thinker, executor_code, executor_tests, executor_runtime, validator, debugger, reviewer, finalizer, memory_update
6. `core/graph_builder.py` – `build_graph()` that wires all nodes + conditional edges
7. `agent_framework.py` – `run_task(task: str) -> AgentState` public entry + CLI `__main__`
8. `fastapi_server.py` – FastAPI wrapper (replace/update existing `api/` server if present)
9. `test_framework_v3.py` – Integration test suite (3 tests: build, debug, plan)

### Files to Update
10. `requirements.txt` – Add: `httpx>=0.25.0`, `pydantic>=2.0.0` (keep existing deps)
11. `.env.example` – Add MINIMAX_API_KEY, KIMI_API_KEY, GLM_API_KEY, NVIDIA_API_KEY entries

## Critical Bug Fixes in Reference Code (Apply These)
In `reviewer_node`:
- Bug 1: `user_msg` is referenced but never defined → fix by setting `user_msg = summary` before the `call_model_async` call
- Bug 2: `resp["choices"]["message"]["content"]` → fix to `resp["choices"][0]["message"]["content"]`
- Bug 3: `lines.upper()` on a list → fix to `lines[0].upper()`

## Success Criteria
- `python agent_framework.py "Build a hello world FastAPI app"` runs without import errors (will fail on API calls without keys, but must not crash on import/graph init)
- `python -c "from core.agent_state import AgentState; from core.state_graph import SimpleStateGraph; print('OK')"` prints OK
- `python -m pytest test_framework_v3.py -x --co -q` shows 3 collected tests
- `python fastapi_server.py --help` (or startup check) works without errors
- No existing files in `agents/`, `core/`, `antigravity/` are deleted
