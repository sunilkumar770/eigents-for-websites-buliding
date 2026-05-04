
from typing import Optional, Dict, Any
from core.model_caller import call_model_async

class CommunicableTrait:
    async def _call_llm(
        self,
        prompt: str,
        model_name: str,
        system_context: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 4096
    ) -> str:
        messages = []
        if system_context:
            messages.append({"role": "system", "content": system_context})
        messages.append({"role": "user", "content": prompt})
        
        resp = await call_model_async(
            model_name,
            messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return resp["choices"][0]["message"]["content"]
