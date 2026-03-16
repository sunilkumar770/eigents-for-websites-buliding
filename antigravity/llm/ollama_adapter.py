"""
Ollama Adapter

Connects to a local Ollama server for LLM inference.
Compatible models: deepseek-r1, gemma3, llama3, mistral, phi3, etc.
Provides the same `chat()` interface as KimiAdapter so it can be used
as a drop-in replacement within the multi-agent workflow.
"""

import requests
import json
import logging
import time
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class OllamaAdapter:
    """
    Adapter for local Ollama models.

    Uses the Ollama REST API (http://localhost:11434/api/chat).
    Provides the same chat() interface as KimiAdapter so agents can
    use either backend transparently.

    Supported Ollama models (must be pulled first):
      - deepseek-r1:1.5b
      - deepseek-r1:7b
      - gemma3:2b / gemma3:12b
      - llama3.1 / llama3.2
      - mistral / mistral-nemo
      - phi3 / phi3.5
      - qwen2.5-coder
    """

    def __init__(
        self,
        model: str = "deepseek-r1:1.5b",
        base_url: str = "http://localhost:11434",
        timeout: int = 120,
        mock_mode: bool = False,
    ):
        """
        Initialize the Ollama adapter.

        Args:
            model:     Ollama model tag (must already be pulled).
            base_url:  Ollama server URL. Default: http://localhost:11434
            timeout:   HTTP request timeout in seconds.
            mock_mode: If True, returns mock responses without calling Ollama.
                       Useful for development/testing without a running Ollama server.
        """
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.mock_mode = mock_mode
        self._chat_url = f"{self.base_url}/api/chat"
        if mock_mode:
            logger.warning("OllamaAdapter running in MOCK mode — no real LLM calls.")
        else:
            logger.info(f"OllamaAdapter initialised: model={model}, url={self.base_url}")

    # ------------------------------------------------------------------
    # Public interface (matches KimiAdapter)
    # ------------------------------------------------------------------

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
            stream:      Not yet used; kept for interface parity.
            agent_type:  Optional label for logging.
            temperature: Sampling temperature.
            max_tokens:  Max tokens to generate (maps to num_predict).

        Returns:
            Response content string (or raises RuntimeError on failure).
        """
        tag = agent_type or "unknown"
        start = time.time()

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        logger.info(f"[OllamaAdapter][{tag}] → {self.model} ({len(messages)} messages)")

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

        # Ollama returns: {"message": {"role": "assistant", "content": "..."}, ...}
        content = data.get("message", {}).get("content", "")

        elapsed = time.time() - start
        logger.info(f"[OllamaAdapter][{tag}] ← {len(content)} chars in {elapsed:.2f}s")

        return content

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def is_available(self) -> bool:
        """Return True if Ollama is reachable and the model exists."""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            resp.raise_for_status()
            models = [m["name"] for m in resp.json().get("models", [])]
            # Accept partial match (e.g. "deepseek-r1:1.5b" contains "deepseek-r1")
            return any(self.model in m or m.startswith(self.model.split(":")[0]) for m in models)
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
