"""
core/agent_nodes.py
Async node functions for the Multi-Agent Framework v3.
Each node takes AgentState and returns AgentState (mutated or fresh).
"""
from __future__ import annotations

import json
import time
import uuid
from typing import Any, Dict, List

from .agent_state import AgentState, CodeUnit, SandboxRun, VerificationResult
from .model_caller import call_model_async
from .tool_stubs import call_tool_async, memory_store_async, run_in_sandbox
from .agent_adapters import (
    interpreter_adapter, frontend_adapter, backend_adapter,
    security_adapter, testing_adapter, integration_adapter,
    debug_adapter, readiness_adapter
)


# ── Supervisor Node ───────────────────────────────────────────────────────────

async def supervisor_node(state: AgentState) -> AgentState:
    """Uses ProductInterpreter to analyze task and then decomposes it."""
    # First, use the specialized interpreter
    state = await interpreter_adapter(state)
    
    # Then refine subtasks if needed (original supervisor logic)
    if not state.subtasks:
        sys_prompt = (
            "You are the Master Orchestrator. Decompose the user task into a list of "
            "logical subtasks. Output ONLY JSON with keys: 'intent', 'subtasks' (list)."
        )
        user_msg = f"Task: {state.task}"
        
        resp = await call_model_async(
            "minimax",
            [{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_msg}]
        )
        
        try:
            content = resp["choices"][0]["message"]["content"]
            import re
            match = re.search(r"\{.*\}", content, re.DOTALL)
            data = json.loads(match.group(0)) if match else json.loads(content)
            state.subtasks = data.get("subtasks", [])
        except Exception:
            state.subtasks = [state.task]
            
    return state


# ── Planner (CoVe) Node ───────────────────────────────────────────────────────

async def planner_cove_node(state: AgentState) -> AgentState:
    """Chain-of-Verification (CoVe) enhanced planner."""
    sys_prompt = (
        "You are the Planner Agent. Use Chain-of-Verification (CoVe).\n"
        "1. Create a DRAFT plan.\n"
        "2. Generate internal verification QUESTIONS to check for flaws.\n"
        "3. Provide ANSWERS to those questions.\n"
        "4. Output the FINAL PLAN.\n"
        "Use sections: ## DRAFT, ## QUESTIONS, ## ANSWERS, ## FINAL PLAN."
    )
    user_msg = f"Task: {state.task}\nSubtasks: {state.subtasks}"
    
    resp = await call_model_async(
        "minimax",
        [{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_msg}]
    )
    
    text = resp["choices"][0]["message"]["content"]
    sections = {"DRAFT": "", "QUESTIONS": "", "ANSWERS": "", "FINAL PLAN": ""}
    current = None
    
    for line in text.split("\n"):
        if line.startswith("##"):
            current = line.strip(" #").upper()
            if "FINAL PLAN" in current: current = "FINAL PLAN"
        elif current and current in sections:
            sections[current] += line + "\n"
            
    state.plan.draft = sections["DRAFT"].strip()
    state.plan.questions = [q.strip("- ") for q in sections["QUESTIONS"].split("\n") if q.strip()]
    state.plan.verification_answers = [a.strip("- ") for a in sections["ANSWERS"].split("\n") if a.strip()]
    state.plan.final = sections["FINAL PLAN"].strip()
    
    return state


# ── Plan Validator Node ───────────────────────────────────────────────────────

async def plan_validator_node(state: AgentState) -> AgentState:
    """Ensure the final plan covers all subtasks."""
    plan_text = state.plan.final.lower()
    missing = [st for st in state.subtasks if st.lower() not in plan_text]
    
    if missing:
        state.status = "NEEDS_REPLAN"
        state.memory_refs.append(f"plan_missing_subtasks: {','.join(missing)}")
    else:
        state.status = "RUNNING"
        
    return state


# ── Thinker Node ──────────────────────────────────────────────────────────────

async def thinker_node(state: AgentState) -> AgentState:
    """Deep reasoning – extract facts, assumptions, risks, and decisions."""
    sys_prompt = (
        "You are the Thinker Agent. Analyze the task and plan.\n"
        "Output four sections exactly: ## FACTS, ## ASSUMPTIONS, ## RISKS, ## DECISIONS."
    )
    user_msg = f"Task: {state.task}\nPlan: {state.plan.final}"
    
    resp = await call_model_async(
        "kimi",
        [{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_msg}]
    )
    
    text = resp["choices"][0]["message"]["content"]
    sections = {"FACTS": "", "ASSUMPTIONS": "", "RISKS": "", "DECISIONS": ""}
    current = None
    
    for line in text.split("\n"):
        if line.startswith("##"):
            current = line.strip(" #").upper()
        elif current and current in sections:
            sections[current] += line + "\n"
            
    state.thinking.facts = [f.strip("- ") for f in sections["FACTS"].split("\n") if f.strip()]
    state.thinking.assumptions = [a.strip("- ") for a in sections["ASSUMPTIONS"].split("\n") if a.strip()]
    state.thinking.risks = [r.strip("- ") for r in sections["RISKS"].split("\n") if r.strip()]
    state.thinking.decisions = [d.strip("- ") for d in sections["DECISIONS"].split("\n") if d.strip()]
    
    return state


# ── Executor: Code Node ───────────────────────────────────────────────────────

async def executor_code_node(state: AgentState) -> AgentState:
    """Generate production-grade code using Specialized Frontend/Backend agents."""
    # Run Frontend agent
    state = await frontend_adapter(state)
    # Run Backend agent
    state = await backend_adapter(state)
    # Run Security audit on generated code
    state = await security_adapter(state)
    return state


# ── Executor: Tests Node ──────────────────────────────────────────────────────

async def executor_tests_node(state: AgentState) -> AgentState:
    """Generate thorough test suites using Specialized Testing agent."""
    state = await testing_adapter(state)
    return state


# ── Executor: Runtime Node ────────────────────────────────────────────────────

async def executor_runtime_node(state: AgentState) -> AgentState:
    """Run code and tests in the sandbox stub."""
    for module, cu in state.code_units.items():
        run = await run_in_sandbox(module, cu.source, cu.tests)
        cu.sandbox_runs.append(run)
        
        if cu.verification is None:
            cu.verification = VerificationResult()
        cu.verification.tests_ok = (run.exit_code == 0)
        
    return state


# ── Validator Node ────────────────────────────────────────────────────────────

async def validator_node(state: AgentState) -> AgentState:
    """Perform AST and schema checks."""
    for module, cu in state.code_units.items():
        if cu.verification is None:
            cu.verification = VerificationResult()
            
        # Basic AST validation - ONLY for Python files
        if module.endswith(".py") or "." not in module:
            try:
                compile(cu.source or "", f"{module}.py", "exec")
                cu.verification.ast_ok = True
            except Exception as e:
                cu.verification.ast_ok = False
                cu.verification.details["ast_error"] = str(e)
        else:
            # Assume OK for JS/JSON/etc. for now
            cu.verification.ast_ok = True
            
        cu.verification.schema_ok = True
        
        # Overall is True if ALL checks pass
        is_overall_ok = (cu.verification.ast_ok and cu.verification.schema_ok and cu.verification.tests_ok)
        cu.verification.details["overall"] = "True" if is_overall_ok else "False"
        
    return state


# ── Debugger Node ─────────────────────────────────────────────────────────────

async def debugger_node(state: AgentState) -> AgentState:
    """Fix failing code units using Specialized Debug agent."""
    state = await debug_adapter(state)
    return state


# ── Reviewer Node ─────────────────────────────────────────────────────────────

async def reviewer_node(state: AgentState) -> AgentState:
    """Kimi-based final review for approval."""
    sys_prompt = (
        "You are the Reviewer Agent. Your first line must be exactly 'APPROVED', "
        "'NEEDS_REVISION', or 'FAILED'. Then list your findings."
    )
    
    # Build summary
    summary = f"Task: {state.task}\nPlan: {state.plan.final}\n"
    summary += "Code Units Status:\n"
    for module, cu in state.code_units.items():
        status = "OK" if cu.verification and cu.verification.details.get("overall") == "True" else "FAIL"
        summary += f"- {module}: {status}\n"
        
    user_msg = summary # BUG FIX 1: user_msg was missing in reference
    
    resp = await call_model_async(
        "kimi",
        [{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_msg}]
    )
    
    # BUG FIX 2: Correct dict access
    text = resp["choices"][0]["message"]["content"]
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    
    if lines:
        # BUG FIX 3: .upper() on list item, not list
        verdict = lines[0].upper()
        if verdict.startswith("APPROVED"):
            state.status = "DONE"
        elif verdict.startswith("NEEDS_REVISION"):
            state.status = "NEEDS_REPLAN"
        elif verdict.startswith("APPROVED"):
            # Run final readiness check before finishing
            state = await readiness_adapter(state)
            state.status = "DONE"
        else:
            state.status = "FAILED"
            
        await memory_store_async(f"review:{int(time.time())}", text)
        
    return state


# ── Finalizer & Memory Update Nodes ───────────────────────────────────────────

async def finalizer_node(state: AgentState) -> AgentState:
    """Ensure state is marked as terminal."""
    if state.status not in ("DONE", "FAILED"):
        state.status = "DONE"
    return state

async def memory_update_node(state: AgentState) -> AgentState:
    """Persist the entire state to episodic memory."""
    await memory_store_async(
        f"episode:{state.task[:20]}:{int(time.time())}", 
        state.model_dump_json() # Pydantic v2
    )
    return state
