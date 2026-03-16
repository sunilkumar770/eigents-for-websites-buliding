"""
NEXUS Memory — gives agents persistent context across runs.
Stores session history, errors seen, fixes applied.
"""
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


class AgentMemory:
    def __init__(self, session_id: str, memory_dir: str = ".nexus_memory"):
        self.session_id = session_id
        self.memory_path = Path(memory_dir) / f"{session_id}.json"
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        self._data = self._load()

    def _load(self) -> Dict:
        if self.memory_path.exists():
            return json.loads(self.memory_path.read_text())
        return {"session_id": self.session_id, "events": [], "fixes": [], "errors_seen": [], "context": {}}

    def _save(self):
        self.memory_path.write_text(json.dumps(self._data, indent=2))

    def add_event(self, event_type: str, data: Any):
        self._data["events"].append({
            "type": event_type,
            "data": data,
            "timestamp": time.time()
        })
        self._save()

    def remember_fix(self, error: str, fix: str, filepath: str):
        self._data["fixes"].append({"error": error[:500], "fix": fix[:1000], "file": filepath})
        self._save()

    def recall_similar_fix(self, error: str) -> Optional[str]:
        """Find a previously applied fix for similar error."""
        for fix in self._data["fixes"]:
            if any(word in fix["error"] for word in error.split()[:5]):
                return fix["fix"]
        return None

    def set_context(self, key: str, value: Any):
        self._data["context"][key] = value
        self._save()

    def get_context(self, key: str, default=None) -> Any:
        return self._data["context"].get(key, default)

    def get_recent_errors(self, n: int = 5) -> List[str]:
        errors = [e["data"] for e in self._data["events"] if e["type"] == "error"]
        return errors[-n:]

    def summarize(self) -> str:
        ctx = self._data["context"]
        fixes = len(self._data["fixes"])
        events = len(self._data["events"])
        return f"Session: {self.session_id} | Events: {events} | Fixes applied: {fixes} | Context keys: {list(ctx.keys())}"
