"""
core/graph_builder.py
Wires the async nodes into a SimpleStateGraph for execution.
"""
from __future__ import annotations

from .agent_nodes import (
    supervisor_node, planner_cove_node, plan_validator_node,
    thinker_node, executor_code_node, executor_tests_node,
    executor_runtime_node, validator_node, debugger_node,
    reviewer_node, finalizer_node, memory_update_node
)
from .state_graph import SimpleStateGraph


def build_graph() -> SimpleStateGraph:
    """Build and compile the multi-agent execution graph."""
    sg = SimpleStateGraph()
    
    # 1. Register Nodes
    sg.add_node("supervisor", supervisor_node)
    sg.add_node("planner", planner_cove_node)
    sg.add_node("plan_validator", plan_validator_node)
    sg.add_node("thinker", thinker_node)
    sg.add_node("executor_code", executor_code_node)
    sg.add_node("executor_tests", executor_tests_node)
    sg.add_node("executor_runtime", executor_runtime_node)
    sg.add_node("validator", validator_node)
    sg.add_node("debugger", debugger_node)
    sg.add_node("reviewer", reviewer_node)
    sg.add_node("finalizer", finalizer_node)
    sg.add_node("memory_update", memory_update_node)
    
    # 2. Hardwired Edges
    sg.set_entry_point("supervisor")
    sg.add_edge("supervisor", "planner")
    sg.add_edge("planner", "plan_validator")
    
    # 3. Conditional: REPLAN loop
    sg.add_conditional_edges(
        "plan_validator",
        lambda s: "REPLAN" if s.status == "NEEDS_REPLAN" else "OK",
        {"REPLAN": "planner", "OK": "thinker"}
    )
    
    sg.add_edge("thinker", "executor_code")
    sg.add_edge("executor_code", "executor_tests")
    sg.add_edge("executor_tests", "executor_runtime")
    sg.add_edge("executor_runtime", "validator")
    
    # 4. Conditional: DEBUG loop
    def _check_verification(s):
        any_fail = any(
            not cu.verification or cu.verification.details.get("overall") != "True"
            for cu in s.code_units.values()
        )
        return "DEBUG" if any_fail else "REVIEW"
        
    sg.add_conditional_edges("validator", _check_verification, {"DEBUG": "debugger", "REVIEW": "reviewer"})
    
    # 5. Conditional: Review Loop
    def _check_review(s):
        if s.status == "NEEDS_REPLAN": return "REPLAN"
        if s.status == "DONE": return "FINISH"
        return "DEBUG" # default for NEEDS_REVISION or logic failures
        
    sg.add_conditional_edges(
        "reviewer", 
        _check_review, 
        {"REPLAN": "planner", "FINISH": "finalizer", "DEBUG": "debugger"}
    )
    
    # After debugger fix, re-run tests
    sg.add_edge("debugger", "executor_runtime")
    
    sg.add_edge("finalizer", "memory_update")
    # memory_update is leaf node (no next node)
    
    return sg
