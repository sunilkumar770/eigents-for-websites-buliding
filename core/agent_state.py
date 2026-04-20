"""
core/agent_state.py
Pydantic v2 state models for the Multi-Agent Framework v3.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class SandboxRun(BaseModel):
    module: str
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    duration_ms: int = 0


class VerificationResult(BaseModel):
    ast_ok: bool = False
    schema_ok: bool = False
    tests_ok: bool = False
    details: Dict[str, str] = Field(default_factory=dict)


class ReviewResult(BaseModel):
    verdict: Literal["APPROVED", "NEEDS_REVISION", "FAILED"]
    findings: List[str] = Field(default_factory=list)


class CodeUnit(BaseModel):
    module: str
    spec: str
    source: str = ""
    tests: str = ""
    patched_source: str = ""
    sandbox_runs: List[SandboxRun] = Field(default_factory=list)
    verification: Optional[VerificationResult] = None
    review: Optional[ReviewResult] = None


class Thinking(BaseModel):
    facts: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    decisions: List[str] = Field(default_factory=list)


class Plan(BaseModel):
    draft: str = ""
    questions: List[str] = Field(default_factory=list)
    verification_answers: List[str] = Field(default_factory=list)
    final: str = ""


class AgentState(BaseModel):
    task: str
    subtasks: List[str] = Field(default_factory=list)
    plan: Plan = Field(default_factory=Plan)
    thinking: Thinking = Field(default_factory=Thinking)
    code_units: Dict[str, CodeUnit] = Field(default_factory=dict)
    full_requirements: Dict[str, Any] = Field(default_factory=dict)
    memory_refs: List[str] = Field(default_factory=list)
    status: Literal[
        "PENDING", "RUNNING", "NEEDS_REPLAN", "FAILED", "DONE"
    ] = "PENDING"

    class Config:
        # Allow mutation so nodes can update fields
        arbitrary_types_allowed = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for persistence."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AgentState:
        """Create state from dictionary."""
        return cls(**data)
