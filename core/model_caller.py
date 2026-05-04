"""
core/model_caller.py
Async multi-model caller for Framework v3.

Supported models:
  minimax  – Minimax M2 (supervisor / planner)
  kimi     – Kimi K2.6 via Moonshot (thinker / reviewer)
  glm      – GLM-4-Plus via ZhipuAI (coder / tests)
  nemotron – Nemotron-Ultra via NVIDIA (debugger)
  gemma    – Gemma3 via local Ollama (memory / misc)
"""
from __future__ import annotations

import os
from typing import Dict, List

import httpx

# ── Model registry ────────────────────────────────────────────────────────────
MODEL_CONFIG: Dict[str, dict] = {
    "minimax": {
        "endpoint": "https://api.minimax.chat/v1/text/chatcompletion_v2",
        "key_env": "MINIMAX_API_KEY",
        "model_id": "MiniMax-Text-01",
        "schema": "openai",
    },
    "kimi": {
        "endpoint": "https://api.moonshot.cn/v1/chat/completions",
        "key_env": "KIMI_API_KEY",
        "model_id": "moonshot-v1-128k",
        "schema": "openai",
    },
    "glm": {
        "endpoint": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "key_env": "GLM_API_KEY",
        "model_id": "glm-4-plus",
        "schema": "openai",
    },
    "nemotron": {
        "endpoint": "https://integrate.api.nvidia.com/v1/chat/completions",
        "key_env": "NVIDIA_API_KEY",
        "model_id": "nvidia/llama-3.1-nemotron-ultra-253b-v1",
        "schema": "openai",
    },
    "gemma": {
        "endpoint": "http://localhost:11434/api/generate",
        "key_env": "",
        "model_id": "gemma3:latest",
        "schema": "ollama",
    },
    "glm-nim": {
        "endpoint": "https://integrate.api.nvidia.com/v1/chat/completions",
        "key_env": "NVIDIA_API_KEY",
        "model_id": "z-ai/glm-5.1",
        "schema": "openai",
        "extra_body": {"chat_template_kwargs": {"enable_thinking": True, "clear_thinking": False}},
    },
    "minimax-nim": {
        "endpoint": "https://integrate.api.nvidia.com/v1/chat/completions",
        "key_env": "NVIDIA_API_KEY",
        "model_id": "minimaxai/minimax-m2.7",
        "schema": "openai",
    },
    "kimi-nim": {
        "endpoint": "https://integrate.api.nvidia.com/v1/chat/completions",
        "key_env": "NVIDIA_API_KEY",
        "model_id": "moonshotai/kimi-k2.6",
        "schema": "openai",
        "extra_body": {"chat_template_kwargs": {"thinking": True}},
    },
}

# Fallback: if a cloud model is unavailable, route through Ollama
_OLLAMA_FALLBACK_MODEL = os.getenv("OLLAMA_GENERAL_MODEL", "gemma3:latest")
_OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


async def call_model_async(
    model_name: str,
    messages: List[dict],
    temperature: float = 0.1,
    max_tokens: int = 4096,
) -> dict:
    """
    Call a registered model asynchronously.

    Returns a normalised dict always containing:
      choices[0].message.content  – the text response
    """
    cfg = MODEL_CONFIG.get(model_name)
    if cfg is None:
        raise ValueError(f"Unknown model '{model_name}'. Valid: {list(MODEL_CONFIG)}")

    api_key = os.getenv(cfg["key_env"], "") if cfg.get("key_env") else ""

    async with httpx.AsyncClient(timeout=300.0) as client:
        if cfg["schema"] == "openai":
            payload = {
                "model": cfg["model_id"],
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            # Merge extra body parameters (e.g. for NVIDIA NIM thinking)
            if "extra_body" in cfg:
                payload.update(cfg["extra_body"])
                
            resp = await client.post(
                cfg["endpoint"],
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            
            # Handle reasoning_content if present (thinking models)
            if "choices" in data and len(data["choices"]) > 0:
                delta = data["choices"][0].get("message", {})
                reasoning = delta.get("reasoning_content")
                if reasoning:
                    import logging
                    logging.getLogger("eigent.model_caller").info(f"[{model_name}] Thinking: {reasoning}")
            
            return data

        elif cfg["schema"] == "ollama":
            # Flatten messages → single prompt for Ollama /api/generate
            prompt = "\n".join(
                f"[{m['role'].upper()}] {m['content']}" for m in messages
            )
            payload = {
                "model": cfg["model_id"],
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": max_tokens, "temperature": temperature},
            }
            resp = await client.post(cfg["endpoint"], json=payload)
            resp.raise_for_status()
            data = resp.json()
            # Normalise to OpenAI-style so callers are uniform
            return {
                "choices": [
                    {"message": {"content": data.get("response", "")}}
                ]
            }

        else:
            raise ValueError(f"Unsupported schema '{cfg['schema']}'")


async def call_model_with_fallback(
    model_name: str,
    messages: List[dict],
    temperature: float = 0.1,
    max_tokens: int = 4096,
) -> dict:
    """
    Try the requested cloud model; on any HTTP/network error fall back to Gemma (Ollama).
    """
    try:
        return await call_model_async(model_name, messages, temperature, max_tokens)
    except Exception as exc:
        import logging
        logging.getLogger("eigent.model_caller").warning(
            f"Model '{model_name}' failed ({exc}), falling back to Ollama"
        )
        # Use gemma config but allow OLLAMA_GENERAL_MODEL override
        fallback_cfg = {**MODEL_CONFIG["gemma"], "model_id": _OLLAMA_FALLBACK_MODEL}
        prompt = "\n".join(
            f"[{m['role'].upper()}] {m['content']}" for m in messages
        )
        async with httpx.AsyncClient(timeout=300.0) as client:
            resp = await client.post(
                f"{_OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": _OLLAMA_FALLBACK_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_predict": max_tokens, "temperature": temperature},
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return {"choices": [{"message": {"content": data.get("response", "")}}]}
