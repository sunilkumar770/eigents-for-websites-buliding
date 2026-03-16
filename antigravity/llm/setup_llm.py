"""
LLM Setup Helper

Central place to build the multi-LLM adapter used by the orchestrator.
Import this from api_server.py, demo.py, or any entry point.

Usage:
    from antigravity.llm.setup_llm import build_llm_adapter
    adapter = build_llm_adapter()
    orchestrator = WorkflowOrchestrator(llm_adapter=adapter)
"""

import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def build_llm_adapter(
    kimi_api_key: Optional[str] = None,
    ollama_model: Optional[str] = None,
    ollama_url: Optional[str] = None,
    routing: Optional[Dict[str, str]] = None,
):
    """
    Build and return the best available LLM adapter.

    Priority / auto-detection:
      1. If NVIDIA_API_KEY is set  → KimiAdapter available
      2. If Ollama is reachable    → OllamaAdapter available
      3. If BOTH → MultiLLMRouter (each agent goes to the right backend)
      4. If only Kimi              → KimiAdapter for all agents
      5. If only Ollama            → OllamaAdapter for all agents
      6. Neither                  → Mock mode (dev fallback)

    Environment variables:
      NVIDIA_API_KEY         — Kimi K2.5 via NVIDIA API (optional)
      OLLAMA_MODEL           — local Ollama model tag (default: deepseek-r1:1.5b)
      OLLAMA_BASE_URL        — Ollama server (default: http://localhost:11434)
      EIGENT_ROUTE_<AGENT>   — per-agent routing override (e.g. EIGENT_ROUTE_DEBUG=kimi)

    Args:
        kimi_api_key:  Override for NVIDIA_API_KEY.
        ollama_model:  Override for OLLAMA_MODEL.
        ollama_url:    Override for OLLAMA_BASE_URL.
        routing:       Custom routing dict to pass to MultiLLMRouter.
    """
    # --- Load env ---
    from dotenv import load_dotenv
    load_dotenv()

    api_key  = kimi_api_key or os.getenv("NVIDIA_API_KEY", "").strip()
    model    = ollama_model or os.getenv("OLLAMA_MODEL", "deepseek-r1:1.5b").strip()
    base_url = ollama_url   or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip()

    # --- Probe Kimi ---
    kimi_available = bool(api_key and api_key not in ("", "MOCK_KEY", "your_api_key_here"))

    # --- Probe Ollama ---
    ollama_adapter = None
    try:
        from antigravity.llm.ollama_adapter import OllamaAdapter
        candidate = OllamaAdapter(model=model, base_url=base_url)
        if candidate.is_available():
            ollama_adapter = candidate
            logger.info(f"✓ Ollama available: model={model} @ {base_url}")
        else:
            local_models = candidate.list_local_models()
            if local_models:
                logger.warning(
                    f"Ollama is running but model '{model}' not found locally. "
                    f"Available: {local_models}. Pull with: ollama pull {model}"
                )
            else:
                logger.info("Ollama not reachable — will skip local inference.")
    except Exception as exc:
        logger.debug(f"Ollama probe failed: {exc}")

    # --- Build Kimi adapter ---
    kimi_adapter = None
    if kimi_available:
        from antigravity.llm.kimi_adapter import KimiAdapter
        kimi_adapter = KimiAdapter(api_key=api_key)
        logger.info("✓ Kimi K2.5 adapter ready (NVIDIA API)")
    else:
        logger.info("✗ NVIDIA_API_KEY not set — Kimi K2.5 unavailable")

    # --- Choose adapter strategy ---
    if kimi_adapter and ollama_adapter:
        from antigravity.llm.llm_router import MultiLLMRouter
        adapter = MultiLLMRouter(
            adapters={"kimi": kimi_adapter, "ollama": ollama_adapter},
            routing=routing,
            default_adapter="kimi",
        )
        logger.info("🔀 Using MultiLLMRouter  (Kimi + Ollama)")

    elif kimi_adapter:
        adapter = kimi_adapter
        logger.info("🤖 Using Kimi K2.5 for all agents")

    elif ollama_adapter:
        adapter = ollama_adapter
        logger.info("🦙 Using Ollama for all agents")

    else:
        # Fallback: Mock mode using OllamaAdapter
        from antigravity.llm.ollama_adapter import OllamaAdapter
        adapter = OllamaAdapter(model=model, base_url=base_url, mock_mode=True)
        logger.warning(
            "⚠️  No live LLM available — running in MOCK mode.\n"
            "    → Set NVIDIA_API_KEY in .env for Kimi K2.5\n"
            "    → Or run `ollama serve` for local inference"
        )

    return adapter
