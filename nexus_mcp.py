"""
NEXUS MCP Server — expose all NEXUS capabilities as MCP tools for Antigravity.
Drop this in your Antigravity MCP config to get the full agent system.
"""
import json
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from fastmcp import FastMCP
from core.executor import CodeExecutor
from core.file_manager import FileManager
from core.memory import AgentMemory
from core.loop import NexusLoop
from core.llm_router import LLMRouter

mcp = FastMCP("nexus-agent")
llm = LLMRouter()
executor = CodeExecutor()


@mcp.tool()
def build_project(task: str, project_name: str = "nexus_project") -> str:
    """
    Build an entire project from a text description.
    Autonomously generates code, runs it, debugs, and fixes until tests pass.
    
    Args:
        task: Natural language description of what to build
        project_name: Name for the output directory
    """
    project_dir = str(Path("generated_projects") / project_name)
    loop = NexusLoop(llm, project_dir, session_id=project_name)
    result = loop.run(task)
    return json.dumps(result, indent=2)


@mcp.tool()
def fix_code(filepath: str, error_description: str, project_dir: str = ".") -> str:
    """
    Fix a specific file given an error description.
    Reads the file, understands the error, and patches it autonomously.
    
    Args:
        filepath: Relative path to the broken file
        error_description: The error message or description of what's wrong
        project_dir: Root directory of the project
    """
    loop = NexusLoop(llm, project_dir, session_id="fix_session")
    result = loop.fix_existing(filepath, error_description)
    return json.dumps(result, indent=2)


@mcp.tool()
def run_and_debug(project_dir: str) -> str:
    """
    Run a project's tests, capture errors, and return structured debug info.
    
    Args:
        project_dir: Path to the project directory
    """
    result = executor.run_tests(project_dir)
    return result.to_agent_context()


@mcp.tool()
def execute_code_snippet(code: str, language: str = "python") -> str:
    """
    Execute a code snippet and return output + any errors.
    
    Args:
        code: The code to execute
        language: python, javascript, or bash
    """
    if language == "python":
        result = executor.run_python(code)
    elif language in ["javascript", "node"]:
        import tempfile, os
        with tempfile.NamedTemporaryFile(suffix=".js", delete=False, mode="w") as f:
            f.write(code)
            tmp = f.name
        result = executor.run_file(tmp)
        os.unlink(tmp)
    elif language == "bash":
        result = executor.run_shell(code)
    else:
        return f"Unsupported language: {language}"
    return result.to_agent_context()


@mcp.tool()
def read_project_files(project_dir: str) -> str:
    """
    Read all source files in a project and return their contents.
    Useful for giving agents full project context before fixing.
    
    Args:
        project_dir: Path to the project directory
    """
    fm = FileManager(project_dir)
    return fm.get_project_context()


@mcp.tool()
def write_file(filepath: str, content: str, project_dir: str = ".") -> str:
    """
    Write content to a file in the project.
    
    Args:
        filepath: Relative path to write
        content: File content
        project_dir: Root project directory
    """
    fm = FileManager(project_dir)
    fm.write(filepath, content)
    return f"✅ Written: {filepath}"


@mcp.tool()
def patch_file(filepath: str, old_code: str, new_code: str, project_dir: str = ".") -> str:
    """
    Precisely patch a file by replacing old_code with new_code.
    Safer than full rewrites — only changes what's needed.
    
    Args:
        filepath: File to patch
        old_code: Exact code block to find and replace
        new_code: Replacement code
        project_dir: Root project directory
    """
    fm = FileManager(project_dir)
    success = fm.patch(filepath, old_code, new_code)
    if success:
        return f"✅ Patched {filepath} successfully"
    return f"❌ Could not find old_code in {filepath}. Use write_file instead."


@mcp.tool()
def get_agent_memory(session_id: str) -> str:
    """
    Retrieve memory and context from a previous agent session.
    
    Args:
        session_id: The session ID to recall
    """
    mem = AgentMemory(session_id)
    return mem.summarize()


@mcp.tool()
def install_dependencies(project_dir: str) -> str:
    """
    Auto-detect and install project dependencies (pip or npm).
    
    Args:
        project_dir: Path to the project with requirements.txt or package.json
    """
    result = executor.install_deps(project_dir)
    return result.to_agent_context()


if __name__ == "__main__":
    mcp.run()
