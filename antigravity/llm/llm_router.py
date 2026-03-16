"""
Multi-LLM Router

Routes each agent's LLM calls to the most appropriate backend.

Default routing:
  ┌──────────────────────┬──────────────────────────────────────────┐
  │ Agent                │ Backend                                  │
  ├──────────────────────┼──────────────────────────────────────────┤
  │ ProductInterpreter   │ Kimi K2.5 (complex reasoning)            │
  │ FrontendEngineer     │ Kimi K2.5 (UI/UX design + code)         │
  │ BackendEngineer      │ Kimi K2.5 (complex backend logic)        │
  │ Integration          │ Kimi K2.5 (API contract reasoning)       │
  │ Testing              │ Ollama (fast, local, test generation)     │
  │ Debug                │ Ollama (fast iteration for fixes)         │
  │ Security             │ Kimi K2.5 (security expertise needed)    │
  │ ProductionReadiness  │ Ollama (checklist-style tasks)           │
  └──────────────────────┴──────────────────────────────────────────┘

Override via environment variables or the `routing` dict in constructor.
"""

import logging
import os
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class MultiLLMRouter:
    """
    A transparent LLM adapter that dispatches each agent's request
    to a specific underlying adapter.

    Implements the same chat() interface so it can be passed anywhere
    a KimiAdapter or OllamaAdapter is expected.

    Usage:
        router = MultiLLMRouter(
            adapters={
                "kimi":   KimiAdapter(api_key=...),
                "ollama": OllamaAdapter(model="deepseek-r1:1.5b"),
            }
        )
        orchestrator = WorkflowOrchestrator(llm_adapter=router)
    """

    # Default: which adapter each agent_type should use
    DEFAULT_ROUTING: Dict[str, str] = {
        "product_interpreter":   "kimi",
        "frontend_engineer":     "kimi",
        "backend_engineer":      "kimi",
        "integration":           "kimi",
        "testing":               "ollama",
        "debug":                 "ollama",
        "security":              "kimi",
        "production_readiness":  "ollama",
    }

    def __init__(
        self,
        adapters: Dict[str, Any],
        routing: Optional[Dict[str, str]] = None,
        default_adapter: str = "kimi",
    ):
        """
        Args:
            adapters:        Mapping of name → adapter instance.
                             E.g. {"kimi": KimiAdapter(...), "ollama": OllamaAdapter(...)}
            routing:         Agent-type → adapter-name overrides.
                             Merges with DEFAULT_ROUTING.
            default_adapter: Fallback adapter name if agent_type is unknown.
        """
        if not adapters:
            raise ValueError("MultiLLMRouter requires at least one adapter.")

        self.adapters = adapters
        self.default_adapter = default_adapter

        # Build effective routing (env > constructor > default)
        self.routing = dict(self.DEFAULT_ROUTING)
        if routing:
            self.routing.update(routing)
        self._apply_env_overrides()

        self._log_config()

    # ------------------------------------------------------------------
    # Public interface (matches KimiAdapter / OllamaAdapter)
    # ------------------------------------------------------------------

    def chat(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        agent_type: str = None,
        **kwargs,
    ) -> Any:
        """
        Route the request to the correct adapter based on agent_type.

        Args:
            messages:   Chat messages.
            stream:     Passed through to the underlying adapter.
            agent_type: Agent type string used for routing.
        """
        adapter_name = self._resolve_adapter(agent_type)
        adapter = self.adapters[adapter_name]

        logger.debug(
            f"[Router] agent={agent_type or 'unknown'} → adapter={adapter_name} "
            f"({type(adapter).__name__})"
        )

        return adapter.chat(messages, stream=stream, agent_type=agent_type, **kwargs)

    # ------------------------------------------------------------------
    # Routing helpers
    # ------------------------------------------------------------------

    def _resolve_adapter(self, agent_type: Optional[str]) -> str:
        """Return the adapter name for the given agent_type."""
        if agent_type:
            name = self.routing.get(agent_type, self.default_adapter)
        else:
            name = self.default_adapter

        if name not in self.adapters:
            logger.warning(
                f"[Router] Adapter '{name}' not found, falling back to '{self.default_adapter}'"
            )
            name = self.default_adapter

        return name

    def _apply_env_overrides(self):
        """
        Allow per-agent routing overrides via environment variables.

        Format:  EIGENT_ROUTE_<AGENT_TYPE>=<adapter_name>
        Example: EIGENT_ROUTE_DEBUG=kimi
        """
        for agent_type in list(self.routing.keys()):
            env_key = f"EIGENT_ROUTE_{agent_type.upper()}"
            env_val = os.getenv(env_key)
            if env_val:
                self.routing[agent_type] = env_val.strip().lower()
                logger.info(f"[Router] Env override: {agent_type} → {env_val}")

    def _log_config(self):
        """Print the effective routing table on startup."""
        logger.info("=== MultiLLMRouter active ===")
        for agent, adapter in self.routing.items():
            available_adapters = list(self.adapters.keys())
            status = "✓" if adapter in available_adapters else "✗ MISSING"
            logger.info(f"  {agent:25s} → {adapter} {status}")
        logger.info(f"  Registered adapters: {list(self.adapters.keys())}")

    # ------------------------------------------------------------------
    # Convenience / info
    # ------------------------------------------------------------------

    def get_routing_table(self) -> Dict[str, str]:
        """Return current routing table."""
        return dict(self.routing)

    def override_agent_routing(self, agent_type: str, adapter_name: str):
        """
        Dynamically change which adapter an agent uses.

        Useful for A/B testing or runtime fallbacks.
        """
        if adapter_name not in self.adapters:
            raise ValueError(
                f"Adapter '{adapter_name}' not registered. "
                f"Available: {list(self.adapters.keys())}"
            )
        self.routing[agent_type] = adapter_name
        logger.info(f"[Router] Overriding {agent_type} → {adapter_name}")

    def add_adapter(self, name: str, adapter: Any):
        """Register a new adapter at runtime."""
        self.adapters[name] = adapter
        logger.info(f"[Router] Added adapter: {name} ({type(adapter).__name__})")


# ------------------------------------------------------------------
# Global Helper for External Integration (MCP / Bridge)
# ------------------------------------------------------------------

_router_instance: Optional[MultiLLMRouter] = None


def route_task(prompt: str, agent_type: str = "product_interpreter") -> str:
    """
    Convenience function to route a task to the best available LLM.
    Used by MCP and CLI bridge.
    
    Args:
        prompt: Task description or prompt.
        agent_type: The agent context for routing (defaults to product_interpreter/Kimi).
    
    Returns:
        LLM response string.
    """
    global _router_instance
    if _router_instance is None:
        from antigravity.llm.setup_llm import build_llm_adapter
        adapter = build_llm_adapter()
        
        # If build_llm_adapter returned a router, use it.
        # If it returned a single adapter, wrap it so the interface is consistent.
        if isinstance(adapter, MultiLLMRouter):
            _router_instance = adapter
        else:
            # Fallback wrapper
            _router_instance = MultiLLMRouter(
                adapters={"fallback": adapter},
                default_adapter="fallback"
            )
    
    messages = [{"role": "user", "content": prompt}]
    return _router_instance.chat(messages, agent_type=agent_type)
