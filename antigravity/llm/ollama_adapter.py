"""
Ollama Adapter (3‑model, lock-serialized)

Connects to a local Ollama server for LLM inference.

This version:
  - Uses three explicit models:
      OLLAMA_REASONER_MODEL   → reasoning agents
      OLLAMA_CODER_MODEL      → coding/debugging agents
      OLLAMA_GENERAL_MODEL    → everything else
  - Enforces a single active request at a time via a process-wide lock
    so heavy models never run concurrently on 16 GB RAM.

Env configuration (required):
  OLLAMA_REASONER_MODEL
  OLLAMA_CODER_MODEL
  OLLAMA_GENERAL_MODEL
  OLLAMA_BASE_URL (default: http://localhost:11434)
"""

import requests
import logging
import time
import os
import threading
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Global lock to serialize all Ollama calls across the process.
_OLLAMA_LOCK = threading.Lock()


class OllamaAdapter:
    """
    Adapter for local Ollama models with per-agent routing.

    Public API matches KimiAdapter:
        chat(messages, stream=False, agent_type=None, temperature=0.7, max_tokens=4096, **kwargs)
    """

    # Map antigravity agent_type → logical role → model slot
    AGENT_ROLE_MAP = {
        "product_interpreter":   "reasoner",
        "frontend_engineer":     "coder",
        "backend_engineer":      "coder",
        "integration":           "coder",
        "testing":               "coder",
        "debug":                 "coder",
        "security":              "reasoner",
        "production_readiness":  "general",
    }

    def __init__(
        self,
        model: str = "unused-default",
        base_url: str = "http://localhost:11434",
        timeout: int = 120,
        mock_mode: bool = False,
    ):
        """
        Initialize the Ollama adapter.

        Args:
            model:     Ignored for routing (kept for backward compatibility).
            base_url:  Ollama server URL.
            timeout:   HTTP request timeout in seconds.
            mock_mode: If True, returns mock responses without calling Ollama.
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.mock_mode = mock_mode
        self._chat_url = f"{self.base_url}/api/chat"

        # Required model tags per logical role
        self.reasoner_model = os.getenv("OLLAMA_REASONER_MODEL")
        self.coder_model = os.getenv("OLLAMA_CODER_MODEL")
        self.general_model = os.getenv("OLLAMA_GENERAL_MODEL")

        missing = [name for name, val in [
            ("OLLAMA_REASONER_MODEL", self.reasoner_model),
            ("OLLAMA_CODER_MODEL", self.coder_model),
            ("OLLAMA_GENERAL_MODEL", self.general_model),
        ] if not val]
        if missing and not mock_mode:
            raise RuntimeError(
                f"OllamaAdapter missing required env vars: {', '.join(missing)}. "
                "Configure all three model tags before running."
            )

        if mock_mode:
            logger.warning("OllamaAdapter running in MOCK mode — no real LLM calls.")
        else:
            logger.info(
                "OllamaAdapter initialized with 3‑model routing: "
                f"reasoner={self.reasoner_model}, "
                f"coder={self.coder_model}, "
                f"general={self.general_model}, "
                f"url={self.base_url}"
            )

    # ------------------------------------------------------------------ #
    # Routing helpers                                                    #
    # ------------------------------------------------------------------ #

    def _select_model_for_agent(self, agent_type: Optional[str]) -> str:
        """
        Map antigravity agent_type → logical role → concrete Ollama model tag.
        """
        if not agent_type:
            return self.general_model

        role = self.AGENT_ROLE_MAP.get(agent_type, "general")

        if role == "reasoner":
            return self.reasoner_model
        if role == "coder":
            return self.coder_model
        return self.general_model

    # ------------------------------------------------------------------ #
    # Public interface                                                   #
    # ------------------------------------------------------------------ #

    def chat(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        agent_type: str = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> Any:
        """
        Send a chat request to the local Ollama server.

        Args:
            messages:    List of {role, content} dicts (OpenAI format).
            stream:      Not used; kept for interface parity.
            agent_type:  Agent label for routing + logging.
            temperature: Sampling temperature.
            max_tokens:  Max tokens to generate (maps to num_predict).
        """
        tag = agent_type or "unknown"
        model = self._select_model_for_agent(agent_type)

        if self.mock_mode:
            logger.info(f"[OllamaAdapter-MOCK][{tag}] → {model} ({len(messages)} messages)")
            return f"[MOCK RESPONSE from {model} for agent {tag}]"

        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        logger.info(f"[OllamaAdapter][{tag}] → model={model} ({len(messages)} messages)")
        start = time.time()

        # Enforce single active Ollama request at a time.
        with _OLLAMA_LOCK:
            try:
                resp = requests.post(
                    self._chat_url,
                    json=payload,
                    timeout=self.timeout,
                    headers={"Content-Type": "application/json"},
                )
                resp.raise_for_status()
            except requests.exceptions.ConnectionError:
                raise RuntimeError(
                    f"Cannot connect to Ollama at {self.base_url}. "
                    "Is Ollama running? Start it with: ollama serve"
                )
            except requests.exceptions.Timeout:
                raise RuntimeError(
                    f"Ollama timed out after {self.timeout}s. "
                    "Try a smaller model or increase the timeout."
                )
            except requests.exceptions.HTTPError as exc:
                raise RuntimeError(f"Ollama HTTP error: {exc}\n{resp.text}")

            data = resp.json()

        content = data.get("message", {}).get("content", "")
        elapsed = time.time() - start
        logger.info(f"[OllamaAdapter][{tag}] ← {len(content)} chars from {model} in {elapsed:.2f}s")

        return content

    # ------------------------------------------------------------------ #
    # Health / discovery helpers                                         #
    # ------------------------------------------------------------------ #

    def is_available(self) -> bool:
        """
        Return True if Ollama is reachable and at least one configured model exists.
        """
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            resp.raise_for_status()
            models = [m["name"] for m in resp.json().get("models", [])]

            candidates = {
                self.reasoner_model,
                self.coder_model,
                self.general_model,
            }
            candidates = {c for c in candidates if c}

            for c in candidates:
                if any(c == m or m.startswith(c.split(":")[0]) for m in models):
                    return True
            return False
        except Exception:
            return False

    def list_local_models(self) -> List[str]:
        """Return list of locally available Ollama model names."""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            resp.raise_for_status()
            return [m["name"] for m in resp.json().get("models", [])]
        except Exception:
            return []
