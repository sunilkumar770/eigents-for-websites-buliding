"""
NEXUS LLM Router — 3‑model Ollama setup, no global OLLAMA_MODEL override.

Roles:
  - planner / validator       → OLLAMA_REASONER_MODEL   (e.g. DeepSeek R1 Qwen 14B)
  - coder / fixer / debugger  → OLLAMA_CODER_MODEL      (e.g. Qwen-Coder 14B)
  - default / misc            → OLLAMA_GENERAL_MODEL    (e.g. Gemma 3 12B)

Env configuration (required):
  OLLAMA_REASONER_MODEL   (no default; must be set)
  OLLAMA_CODER_MODEL      (no default; must be set)
  OLLAMA_GENERAL_MODEL    (no default; must be set)
  OLLAMA_BASE_URL         (default: http://localhost:11434)
  NVIDIA_API_KEY          (optional cloud reasoning)
  OPENAI_API_KEY          (optional cloud reasoning)
"""

import os
import requests
from typing import Optional


class LLMRouter:
    """
    Unified LLM interface for the NEXUS loop.

    Strategy:
      - planner / validator → cloud (if available) else Ollama reasoner model
      - coder / debugger / fixer → Ollama coder model
      - everything else → Ollama general model

    There is NO single-model override anymore; you must configure all 3 env vars.
    """

    def __init__(self):
        # Base URLs / keys
        self.ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
        self.nvidia_key = os.getenv("NVIDIA_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")

        # Required per-role model tags
        self.reasoner_model = os.getenv("OLLAMA_REASONER_MODEL")
        self.coder_model = os.getenv("OLLAMA_CODER_MODEL")
        self.general_model = os.getenv("OLLAMA_GENERAL_MODEL")

        # Validate config early
        missing = [name for name, val in [
            ("OLLAMA_REASONER_MODEL", self.reasoner_model),
            ("OLLAMA_CODER_MODEL", self.coder_model),
            ("OLLAMA_GENERAL_MODEL", self.general_model),
        ] if not val]
        if missing:
            raise RuntimeError(
                f"NEXUS LLMRouter missing required env vars: {', '.join(missing)}. "
                "Configure all three model tags before running."
            )

        # Reasoning roles that may use cloud if available
        self.reasoning_roles = ["planner", "validator"]

    # ------------------------------------------------------------------ #
    # Public API                                                         #
    # ------------------------------------------------------------------ #

    def generate(self, prompt: str, role: str = "default", max_tokens: int = 4096) -> str:
        """
        Main entry point used by NEXUS loop.

        Args:
            prompt:     Text prompt.
            role:       Logical role: planner, coder, debugger, fixer, validator, default.
            max_tokens: Max tokens to generate.
        """
        role = (role or "default").lower()

        # Use cloud for reasoning roles if configured
        if role in self.reasoning_roles:
            if self.nvidia_key:
                return self._nvidia(prompt, max_tokens)
            if self.openai_key:
                return self._openai(prompt, max_tokens)

        # Otherwise, route to Ollama 3‑model setup
        return self._ollama(prompt, role, max_tokens)

    # ------------------------------------------------------------------ #
    # Ollama backend (3-model routing)                                   #
    # ------------------------------------------------------------------ #

    def _select_ollama_model(self, role: str) -> str:
        if role in ("planner", "validator"):
            return self.reasoner_model
        if role in ("coder", "debugger", "fixer"):
            return self.coder_model
        return self.general_model

    def _ollama(self, prompt: str, role: str, max_tokens: int) -> str:
        model = self._select_ollama_model(role)

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": 0.2,
            },
        }

        resp = requests.post(f"{self.ollama_url}/api/generate", json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "")

    # ------------------------------------------------------------------ #
    # Optional cloud backends                                            #
    # ------------------------------------------------------------------ #

    def _nvidia(self, prompt: str, max_tokens: int) -> str:
        """Kimi K2.5 via NVIDIA API."""
        import requests as _r

        headers = {
            "Authorization": f"Bearer {self.nvidia_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "moonshotai/kimi-k2.6",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.2,
        }

        r = _r.post("https://integrate.api.nvidia.com/v1/chat/completions", headers=headers, json=payload, timeout=120)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

    def _openai(self, prompt: str, max_tokens: int) -> str:
        import requests as _r

        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.2,
        }

        r = _r.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=120)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
