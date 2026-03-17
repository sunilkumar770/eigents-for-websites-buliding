"""
NEXUS Executor — runs code, captures output, feeds errors back to agents
The core tool that makes the agent loop autonomous.
"""
import subprocess
import os
import sys
import tempfile
import shutil
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class ExecutionResult:
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    error_type: Optional[str] = None
    error_line: Optional[int] = None
    error_file: Optional[str] = None

    def to_agent_context(self) -> str:
        """Format for feeding into LLM agent prompt."""
        if self.success:
            return f"✅ EXECUTION SUCCESS\nOutput:\n{self.stdout}"
        return (
            f"❌ EXECUTION FAILED (exit code {self.exit_code})\n"
            f"Error Type: {self.error_type or 'Unknown'}\n"
            f"File: {self.error_file or 'N/A'} | Line: {self.error_line or 'N/A'}\n"
            f"STDERR:\n{self.stderr}\n"
            f"STDOUT:\n{self.stdout}"
        )


class CodeExecutor:
    """
    Safe subprocess executor for Python, Node.js, and shell commands.
    Supports timeout, isolated temp dirs, and structured error parsing.
    """

    TIMEOUT = 30  # seconds

    def run_python(self, code: str, workdir: Optional[str] = None) -> ExecutionResult:
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
            f.write(code)
            tmp_path = f.name
        try:
            return self._run_cmd(
                [sys.executable, tmp_path],
                workdir=workdir or os.path.dirname(tmp_path)
            )
        finally:
            os.unlink(tmp_path)

    def run_file(self, filepath: str, workdir: Optional[str] = None) -> ExecutionResult:
        ext = Path(filepath).suffix
        if ext == ".py":
            cmd = [sys.executable, filepath]
        elif ext in [".js", ".ts"]:
            cmd = ["node", filepath]
        elif ext == ".sh":
            cmd = ["bash", filepath]
        else:
            return ExecutionResult(False, "", f"Unsupported file type: {ext}", 1)
        return self._run_cmd(cmd, workdir=workdir or os.path.dirname(filepath))

    def run_tests(self, project_dir: str) -> ExecutionResult:
        """Auto-detects and runs pytest or npm test."""
        if (Path(project_dir) / "package.json").exists():
            return self._run_cmd(["npm", "test", "--", "--passWithNoTests"], workdir=project_dir)
        return self._run_cmd([sys.executable, "-m", "pytest", "-v", "--tb=short"], workdir=project_dir)

    def run_shell(self, command: str, workdir: Optional[str] = None) -> ExecutionResult:
        return self._run_cmd(command, shell=True, workdir=workdir)

    def install_deps(self, project_dir: str) -> ExecutionResult:
        req = Path(project_dir) / "requirements.txt"
        pkg = Path(project_dir) / "package.json"
        if req.exists():
            return self._run_cmd([sys.executable, "-m", "pip", "install", "-r", str(req)], workdir=project_dir)
        if pkg.exists():
            return self._run_cmd(["npm", "install"], workdir=project_dir)
        return ExecutionResult(True, "No dependency file found", "", 0)

    def _run_cmd(self, cmd, shell=False, workdir=None) -> ExecutionResult:
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.TIMEOUT,
                cwd=workdir,
                shell=shell,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
            )
            parsed = self._parse_error(result.stderr)
            return ExecutionResult(
                success=result.returncode == 0,
                stdout=result.stdout[:8000],
                stderr=result.stderr[:8000],
                exit_code=result.returncode,
                **parsed
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(False, "", f"Timeout after {self.TIMEOUT}s", 124, "TimeoutError")
        except FileNotFoundError as e:
            return ExecutionResult(False, "", str(e), 127, "CommandNotFound")
        except Exception as e:
            return ExecutionResult(False, "", str(e), 1, type(e).__name__)

    def _parse_error(self, stderr: str) -> dict:
        """Extract error type, file, and line number from traceback."""
        result = {"error_type": None, "error_line": None, "error_file": None}
        if not stderr:
            return result
        lines = stderr.strip().splitlines()
        for line in reversed(lines):
            line = line.strip()
            if line and not line.startswith(" "):
                result["error_type"] = line.split(":")[0]
                break
        for line in lines:
            if 'File "' in line and ", line " in line:
                try:
                    result["error_file"] = line.split('File "')[1].split('"')[0]
                    result["error_line"] = int(line.split(", line ")[1].split(",")[0])
                except (IndexError, ValueError):
                    pass
        return result
