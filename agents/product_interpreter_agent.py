"""
Product Interpreter Agent (Async v3)

Converts vague user prompts into clear, structured product requirements.
Updated for the v3 Async/Graph architecture.
"""

import json
import re
from typing import Dict, List, Any, Tuple, Optional
from agents.base_agent import BaseAgent, AgentType, AgentResult


class ProductInterpreterAgent(BaseAgent):
    """
    Agent responsible for interpreting user prompts and generating 
    structured product requirements.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, llm_adapter: Any = None):
        super().__init__(
            agent_type=AgentType.PRODUCT_INTERPRETER,
            config=config,
            llm_adapter=llm_adapter
        )

    async def validate_inputs(self, inputs: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate input data"""
        errors = []
        if 'prompt' not in inputs:
            errors.append("Missing required field: 'prompt'")
        elif not isinstance(inputs['prompt'], str) or len(inputs['prompt'].strip()) < 10:
            errors.append("Prompt must be a string of at least 10 characters")
        return len(errors) == 0, errors

    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """Execute product interpretation asynchronously"""
        self.logger.info("Starting product interpretation (Async)")
        
        prompt = inputs['prompt']
        context = inputs.get('context', {})
        
        # Build LLM prompt
        llm_prompt = self._build_interpretation_prompt(prompt, context)
        
        # Use our updated async _call_llm
        llm_response = await self._call_llm(
            prompt=llm_prompt,
            system_context="You are a Product Manager expert at converting vague ideas into structured requirements.",
            temperature=0.5
        )
        
        # Parse response using our robust JSON extraction
        try:
            requirements = self._extract_json_from_response(llm_response)
        except ValueError as e:
            self.logger.error(f"Failed to extract JSON: {e}")
            return AgentResult(success=False, confidence=0.0, outputs={}, errors=[str(e)])
        
        # Enrich and calculate confidence
        requirements = self._enrich_requirements(requirements, prompt)
        confidence = self._calculate_requirements_confidence(requirements)
        
        self.log_decision(
            decision=f"Interpreted product: {requirements.get('product_name', 'Unknown')}",
            reasoning=f"Identified {len(requirements.get('features', []))} features, confidence: {confidence}%"
        )
        
        return AgentResult(
            success=True,
            confidence=confidence,
            outputs=requirements,
            metadata={'original_prompt': prompt}
        )

    def _build_interpretation_prompt(self, prompt: str, context: Dict[str, Any]) -> str:
        context_str = json.dumps(context, indent=2) if context else "None"
        return f"""
Convert the following user idea into structured product requirements.

User Idea: {prompt}
Context: {context_str}

Generate a JSON object:
{{
  "product_name": "string",
  "description": "string",
  "features": [
    {{ "name": "string", "priority": "high|medium|low", "description": "string", "acceptance_criteria": ["string"] }}
  ],
  "pages": [
    {{ "name": "string", "route": "string", "components": ["string"] }}
  ],
  "tech_stack_recommendations": {{ "frontend": "string", "backend": "string", "database": "string" }}
}}

Return ONLY JSON.
"""

    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """Robust extraction from markdown or text"""
        # Try finding JSON block
        import re
        match = re.search(r"\{.*\}", response, re.DOTALL)
        if match:
            try: return json.loads(match.group(0))
            except: pass
        
        # Try raw
        try: return json.loads(response.strip())
        except: pass
        
        raise ValueError("Could not extract valid JSON from response")

    def _enrich_requirements(self, requirements: Dict[str, Any], original_prompt: str) -> Dict[str, Any]:
        if 'product_name' not in requirements:
            requirements['product_name'] = original_prompt.split()[:3][0].title()
        for field in ['features', 'pages']:
            if field not in requirements: requirements[field] = []
        return requirements

    def _calculate_requirements_confidence(self, requirements: Dict[str, Any]) -> float:
        criteria = {
            'has_product_name': bool(requirements.get('product_name')),
            'has_features': len(requirements.get('features', [])) >= 2,
            'has_pages': len(requirements.get('pages', [])) >= 1
        }
        return self._calculate_confidence(criteria)


if __name__ == '__main__':
    # Test stub
    import asyncio
    async def main():
        agent = ProductInterpreterAgent()
        res = await agent.execute_with_retry({'prompt': 'Build a simple todo app with authentication'})
        print(f"Result: {res.success}, Confidence: {res.confidence}%")
    asyncio.run(main())
