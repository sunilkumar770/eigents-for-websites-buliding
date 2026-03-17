"""
NEXUS Loop — Plan → Code → Execute → Debug → Fix → Verify
This is the autonomous engine. Runs until tests pass or max_retries hit.
"""
import logging
from typing import Optional
from .executor import CodeExecutor
from .file_manager import FileManager
from .memory import AgentMemory

logger = logging.getLogger("nexus.loop")


class NexusLoop:
    """
    Orchestrates the full autonomous agent loop:
    1. Planner decomposes task
    2. Coder generates files
    3. Executor runs code
    4. Debugger reads errors
    5. Fixer patches files
    6. Validator confirms fix
    Repeats until success or max_retries exhausted.
    """

    def __init__(self, llm_client, project_dir: str, session_id: str, max_retries: int = 6):
        self.llm = llm_client
        self.fm = FileManager(project_dir)
        self.executor = CodeExecutor()
        self.memory = AgentMemory(session_id)
        self.max_retries = max_retries
        self.project_dir = project_dir

    def run(self, task: str) -> dict:
        logger.info(f"🚀 NEXUS starting task: {task[:80]}")
        self.memory.set_context("task", task)

        # Step 1: Plan
        plan = self._plan(task)
        self.memory.add_event("plan", plan)
        logger.info(f"📋 Plan generated: {len(plan.get('subtasks', []))} subtasks")

        # Step 2: Generate Code
        files = self._generate_code(task, plan)
        self.fm.write_many(files)
        self.memory.add_event("code_generated", list(files.keys()))
        logger.info(f"📝 Generated {len(files)} files")

        # Step 3: Install deps
        dep_result = self.executor.install_deps(self.project_dir)
        logger.info(f"📦 Deps: {'OK' if dep_result.success else dep_result.stderr[:100]}")

        # Step 4: Execute → Debug → Fix loop
        for attempt in range(self.max_retries):
            result = self.executor.run_tests(self.project_dir)
            self.memory.add_event("execution", result.to_agent_context()[:500])

            if result.success:
                logger.info(f"✅ All tests passed on attempt {attempt + 1}")
                self.memory.set_context("status", "success")
                return {"status": "success", "attempts": attempt + 1, "files": self.fm.list_files()}

            logger.warning(f"⚠️  Attempt {attempt + 1}/{self.max_retries} failed: {result.error_type}")
            self.memory.add_event("error", result.stderr[:500])

            # Check memory for known fix
            cached_fix = self.memory.recall_similar_fix(result.stderr)
            if cached_fix:
                logger.info("🧠 Applying cached fix from memory")
                fix = {"strategy": "apply_cached", "patch": cached_fix}
            else:
                fix = self._debug_and_fix(result, attempt)

            if not fix:
                logger.error("🛑 Debug agent could not generate fix")
                break

            self._apply_fix(fix, result)

        self.memory.set_context("status", "failed")
        return {"status": "failed", "attempts": self.max_retries, "last_error": result.stderr[:500]}

    def fix_existing(self, filepath: str, error_description: str) -> dict:
        """Targeted fix: given a file and error description, fix it autonomously."""
        content = self.fm.read(filepath)
        context = f"FILE: {filepath}\n\nCONTENT:\n{content}\n\nERROR:\n{error_description}"
        fix = self._ask_llm("fixer", context)
        if fix.get("patched_content"):
            self.fm.write(filepath, fix["patched_content"])
            result = self.executor.run_file(filepath, self.project_dir)
            return {"status": "success" if result.success else "failed", "result": result.to_agent_context()}
        return {"status": "no_fix_generated"}

    # ── LLM calls ────────────────────────────────────────────────

    def _plan(self, task: str) -> dict:
        prompt = f"""You are a senior software architect. Decompose this task into concrete subtasks.
TASK: {task}
Return JSON: {{"subtasks": ["...", "..."], "tech_stack": {{}}, "entry_point": "main.py"}}"""
        return self._ask_llm("planner", prompt)

    def _generate_code(self, task: str, plan: dict) -> dict:
        prompt = f"""You are an expert full-stack developer. Generate complete, production-ready code.
TASK: {task}
PLAN: {plan}
Return JSON: {{"files": {{"path/to/file.py": "...full content..."}}}}"""
        resp = self._ask_llm("coder", prompt)
        return resp.get("files", {})

    def _debug_and_fix(self, result, attempt: int) -> Optional[dict]:
        project_context = self.fm.get_project_context()
        recent_errors = "\n".join(self.memory.get_recent_errors())
        prompt = f"""You are an expert debugger. Analyze the error and generate a precise fix.

EXECUTION RESULT:
{result.to_agent_context()}

PROJECT FILES:
{project_context[:6000]}

PREVIOUS ERRORS THIS SESSION:
{recent_errors}

ATTEMPT: {attempt + 1}

Return JSON with ONE of these strategies:
1. Patch: {{"strategy": "patch", "filepath": "...", "old_code": "...", "new_code": "..."}}
2. Rewrite file: {{"strategy": "rewrite", "filepath": "...", "content": "..."}}
3. Shell fix: {{"strategy": "shell", "command": "pip install missing-package"}}"""
        return self._ask_llm("debugger", prompt)

    def _apply_fix(self, fix: dict, result):
        strategy = fix.get("strategy")
        if strategy == "patch":
            success = self.fm.patch(fix["filepath"], fix["old_code"], fix["new_code"])
            if not success:
                # Fallback: rewrite if patch fails
                self.fm.write(fix["filepath"], fix.get("new_code", ""))
            self.memory.remember_fix(result.stderr[:300], fix.get("new_code", ""), fix["filepath"])
        elif strategy == "rewrite":
            self.fm.write(fix["filepath"], fix["content"])
        elif strategy == "shell":
            self.executor.run_shell(fix["command"], self.project_dir)
        elif strategy == "apply_cached":
            logger.info("Applying cached fix strategy")

    def _ask_llm(self, role: str, prompt: str) -> dict:
        import json, re
        try:
            response = self.llm.generate(prompt, role=role)
            # Extract JSON from markdown code blocks if present
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            # Try direct JSON parse
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except Exception as e:
            logger.error(f"LLM parse error in {role}: {e}")
        return {}
