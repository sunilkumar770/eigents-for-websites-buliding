"""
NEXUS FileManager — reads, writes, and diff-patches files for agents.
Agents should patch files, not rewrite them entirely.
"""
import os
import difflib
import json
from pathlib import Path
from typing import Dict, List, Optional


class FileManager:
    def __init__(self, project_dir: str):
        self.project_dir = Path(project_dir)
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self._snapshot: Dict[str, str] = {}

    def read(self, filepath: str) -> str:
        full_path = self.project_dir / filepath
        return full_path.read_text(encoding="utf-8") if full_path.exists() else ""

    def write(self, filepath: str, content: str) -> None:
        full_path = self.project_dir / filepath
        full_path.parent.mkdir(parents=True, exist_ok=True)
        self._snapshot[filepath] = self.read(filepath)  # backup
        full_path.write_text(content, encoding="utf-8")

    def write_many(self, files: Dict[str, str]) -> None:
        for path, content in files.items():
            self.write(path, content)

    def patch(self, filepath: str, old_code: str, new_code: str) -> bool:
        """Replace exact old_code block with new_code in file."""
        content = self.read(filepath)
        if old_code not in content:
            return False
        self.write(filepath, content.replace(old_code, new_code, 1))
        return True

    def list_files(self, extensions: Optional[List[str]] = None) -> List[str]:
        result = []
        for f in self.project_dir.rglob("*"):
            if f.is_file() and not any(p in str(f) for p in ["__pycache__", ".git", "node_modules"]):
                if not extensions or f.suffix in extensions:
                    result.append(str(f.relative_to(self.project_dir)))
        return result

    def get_project_context(self) -> str:
        """Returns a compact view of all files for LLM context."""
        lines = [f"PROJECT: {self.project_dir.name}\n"]
        for filepath in self.list_files([".py", ".js", ".ts", ".tsx", ".json", ".env"]):
            content = self.read(filepath)
            lines.append(f"\n--- {filepath} ---\n{content[:2000]}")
        return "\n".join(lines)

    def rollback(self, filepath: str) -> bool:
        if filepath in self._snapshot:
            self.write(filepath, self._snapshot[filepath])
            return True
        return False

    def diff(self, filepath: str, new_content: str) -> str:
        old = self.read(filepath).splitlines(keepends=True)
        new = new_content.splitlines(keepends=True)
        return "".join(difflib.unified_diff(old, new, fromfile=f"a/{filepath}", tofile=f"b/{filepath}"))
