"""
NEXUS LLM Router — routes to Ollama (free local) or cloud APIs.
Extend with any provider. Keeps your existing LLM setup compatible.
"""
import os
import requests
import json
from typing import Optional


class LLMRouter:
    """
    Unified LLM interface. Routes by role:
    - planner/debugger → stronger model (cloud or 7B+)
    - coder/fixer → code-specialized model (deepseek-coder)
    - fast tasks → small local model
    """

    ROLE_MODEL_MAP = {
        "planner": "deepseek-r1:7b",
        "coder": "deepseek-coder:6.7b",
        "debugger": "deepseek-coder:6.7b",
        "fixer": "deepseek-coder:6.7b",
        "validator": "deepseek-r1:1.5b",
        "default": "deepseek-r1:1.5b",
    }

    def __init__(self):
        self.ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.nvidia_key = os.getenv("NVIDIA_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.use_cloud_for = ["planner", "debugger"]  # roles that benefit from stronger models

    def generate(self, prompt: str, role: str = "default", max_tokens: int = 4096) -> str:
        if self.nvidia_key and role in self.use_cloud_for:
            return self._nvidia(prompt, max_tokens)
        if self.openai_key and role in self.use_cloud_for:
            return self._openai(prompt, max_tokens)
        return self._ollama(prompt, role, max_tokens)

    def _ollama(self, prompt: str, role: str, max_tokens: int) -> str:
        model = self.ROLE_MODEL_MAP.get(role, self.ROLE_MODEL_MAP["default"])
        override = os.getenv("OLLAMA_MODEL")
        if override:
            model = override
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": max_tokens, "temperature": 0.2}
        }
        r = requests.post(f"{self.ollama_url}/api/generate", json=payload, timeout=120)
        r.raise_for_status()
        return r.json().get("response", "")

    def _nvidia(self, prompt: str, max_tokens: int) -> str:
        headers = {"Authorization": f"Bearer {self.nvidia_key}", "Content-Type": "application/json"}
        payload = {
            "model": "mistralai/mixtral-8x22b-instruct-v0.1",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.2,
        }
        r = requests.post("https://integrate.api.nvidia.com/v1/chat/completions", headers=headers, json=payload, timeout=120)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

    def _openai(self, prompt: str, max_tokens: int) -> str:
        headers = {"Authorization": f"Bearer {self.openai_key}", "Content-Type": "application/json"}
        payload = {
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.2,
        }
        r = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=120)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
