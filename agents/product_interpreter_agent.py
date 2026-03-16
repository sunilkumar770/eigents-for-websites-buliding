"""
Product Interpreter Agent

Converts vague user prompts into clear, structured product requirements.
"""

import json
import re
from typing import Dict, List, Any, Tuple, Optional
from agents.base_agent import BaseAgent, AgentType, AgentResult


class ProductInterpreterAgent(BaseAgent):
    
    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """
        Extract JSON from LLM response that may contain markdown, explanatory text, etc.
        
        Handles:
        - Pure JSON: {"key": "value"}
        - Markdown blocks: ```json\n{...}\n```
        - Mixed content: Here's the result:\n{...}
        - Code blocks without language: ```\n{...}\n```
        """
        response = response.strip()
        
        # Try 1: Direct JSON parse (fastest)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # Try 2: Extract from markdown code blocks
        # Pattern: ```json\n{...}\n``` or ```\n{...}\n```
        code_block_patterns = [
            r'```json\s*\n(.+?)\n```',  # ```json ... ```
            r'```\s*\n(.+?)\n```',      # ``` ... ```
            r'~~~json\s*\n(.+?)\n~~~',  # ~~~json ... ~~~
            r'~~~\s*\n(.+?)\n~~~',      # ~~~ ... ~~~
        ]
        
        for pattern in code_block_patterns:
            matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)
            if matches:
                for match in matches:
                    try:
                        return json.loads(match.strip())
                    except json.JSONDecodeError:
                        continue
        
        # Try 3: Find JSON object in text (look for {...})
        # Find content between outermost { and }
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, response, re.DOTALL)
        
        if matches:
            # Try the longest match first (likely to be the complete JSON)
            matches_sorted = sorted(matches, key=len, reverse=True)
            for match in matches_sorted:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue
        
        # Try 4: Look for array format [...]
        array_pattern = r'\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\]'
        matches = re.findall(array_pattern, response, re.DOTALL)
        
        if matches:
            matches_sorted = sorted(matches, key=len, reverse=True)
            for match in matches_sorted:
                try:
                    parsed = json.loads(match)
                    # If it's an array with one object, return that object
                    if isinstance(parsed, list) and len(parsed) == 1 and isinstance(parsed[0], dict):
                        return parsed[0]
                    return {"data": parsed}  # Wrap array in object
                except json.JSONDecodeError:
                    continue
        
        # If all else fails, raise an error with helpful message
        raise ValueError(
            f"Could not extract valid JSON from LLM response. "
            f"Response preview: {response[:200]}..."
        )
    """
    Agent responsible for interpreting user prompts and generating
    structured product requirements.
    
    Inputs:
        - prompt: User's product description (string)
        - context: Optional additional context (dict)
    
    Outputs:
        - product_name: Name of the product
        - description: Clear product description
        - features: List of features with priorities
        - pages: List of pages/screens
        - user_flows: User journey definitions
        - non_functional_requirements: Performance, security, etc.
        - tech_stack_recommendations: Suggested technologies
    """
    
    def __init__(self, llm_adapter: Any, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            agent_type=AgentType.PRODUCT_INTERPRETER,
            llm_adapter=llm_adapter,
            config=config
        )
    
    def validate_inputs(self, inputs: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate input data"""
        errors = []
        
        if 'prompt' not in inputs:
            errors.append("Missing required field: 'prompt'")
        elif not isinstance(inputs['prompt'], str):
            errors.append("Field 'prompt' must be a string")
        elif len(inputs['prompt'].strip()) < 10:
            errors.append("Prompt is too short (minimum 10 characters)")
        
        return len(errors) == 0, errors
    
    def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """
        Execute product interpretation
        
        Args:
            inputs: Dict with 'prompt' and optional 'context'
        
        Returns:
            AgentResult with structured requirements
        """
        self.logger.info("Starting product interpretation")
        
        prompt = inputs['prompt']
        context = inputs.get('context', {})
        
        # Build LLM prompt
        llm_prompt = self._build_interpretation_prompt(prompt, context)
        
        # Call LLM
        self.logger.info("Calling LLM to interpret requirements")
        llm_response = self._call_llm(
            prompt=llm_prompt,
            system_context="You are a Product Manager expert at converting vague ideas into structured requirements.",
            temperature=0.5,  # Lower temperature for more consistent output
            max_tokens=4096
        )
        
        # Parse response using robust JSON extraction
        try:
            requirements = self._extract_json_from_response(llm_response)
        except ValueError as e:
            self.logger.error(f"Failed to extract JSON from LLM response: {e}")
            requirements = None
        
        if not requirements:
            return AgentResult(
                success=False,
                confidence=0.0,
                outputs={},
                errors=["Failed to parse requirements from LLM response"]
            )
        
        # Validate and enrich requirements
        requirements = self._enrich_requirements(requirements, prompt)
        
        # Calculate confidence
        confidence = self._calculate_requirements_confidence(requirements)
        
        # Log decision
        self.log_decision(
            decision=f"Interpreted product: {requirements.get('product_name', 'Unknown')}",
            reasoning=f"Identified {len(requirements.get('features', []))} features, "
                     f"{len(requirements.get('pages', []))} pages, "
                     f"confidence: {confidence}%"
        )
        
        return AgentResult(
            success=True,
            confidence=confidence,
            outputs=requirements,
            metadata={
                'original_prompt': prompt,
                'context': context
            }
        )
    
    def _build_interpretation_prompt(self, prompt: str, context: Dict[str, Any]) -> str:
        """Build the LLM prompt for interpretation"""
        
        context_str = ""
        if context:
            context_str = f"\n\nAdditional Context:\n{json.dumps(context, indent=2)}"
        
        return f"""
You are a Product Manager. Convert the following user idea into structured product requirements.

User Idea:
{prompt}
{context_str}

Generate a comprehensive product specification in JSON format with the following structure:

{{
  "product_name": "string",
  "description": "string (2-3 sentences)",
  "features": [
    {{
      "name": "string",
      "priority": "high|medium|low",
      "description": "string",
      "acceptance_criteria": ["string"]
    }}
  ],
  "pages": [
    {{
      "name": "string",
      "route": "string (URL path)",
      "components": ["string"],
      "user_flows": ["string"]
    }}
  ],
  "user_flows": [
    {{
      "name": "string",
      "steps": ["string"],
      "success_criteria": "string"
    }}
  ],
  "non_functional_requirements": {{
    "performance": "string",
    "security": "string",
    "scalability": "string",
    "accessibility": "WCAG 2.1 AA"
  }},
  "tech_stack_recommendations": {{
    "frontend": "React|Next.js|Vue",
    "backend": "Node.js|Python|Go",
    "database": "PostgreSQL|MongoDB|MySQL",
    "auth": "JWT|OAuth2"
  }}
}}

IMPORTANT:
1. Be specific and detailed
2. Prioritize features realistically
3. Define clear acceptance criteria
4. Include all necessary pages
5. Map out complete user journeys
6. Consider security and performance from the start

Return ONLY the JSON, no additional text.
"""
    
    def _enrich_requirements(
        self,
        requirements: Dict[str, Any],
        original_prompt: str
    ) -> Dict[str, Any]:
        """
        Enrich and validate requirements
        
        Args:
            requirements: Parsed requirements from LLM
            original_prompt: Original user prompt
        
        Returns:
            Enriched requirements
        """
        # Ensure all required fields exist
        if 'product_name' not in requirements:
            # Extract from prompt or use default
            requirements['product_name'] = self._extract_product_name(original_prompt)
        
        if 'description' not in requirements:
            requirements['description'] = original_prompt[:200]
        
        # Ensure arrays exist
        for field in ['features', 'pages', 'user_flows']:
            if field not in requirements:
                requirements[field] = []
        
        # Ensure nested objects exist
        if 'non_functional_requirements' not in requirements:
            requirements['non_functional_requirements'] = {
                'performance': 'Standard web performance expectations',
                'security': 'Industry-standard security practices',
                'scalability': 'Support for moderate user growth',
                'accessibility': 'WCAG 2.1 AA'
            }
        
        if 'tech_stack_recommendations' not in requirements:
            requirements['tech_stack_recommendations'] = {
                'frontend': 'React',
                'backend': 'Node.js',
                'database': 'PostgreSQL',
                'auth': 'JWT'
            }
        
        # Add metadata
        requirements['_metadata'] = {
            'generated_at': self.state['last_execution'],
            'agent': self.agent_type.value
        }
        
        return requirements
    
    def _extract_product_name(self, prompt: str) -> str:
        """Extract a product name from the prompt"""
        # Simple heuristic: take first few words
        words = prompt.split()[:3]
        return ' '.join(words).title()
    
    def _calculate_requirements_confidence(self, requirements: Dict[str, Any]) -> float:
        """
        Calculate confidence in the requirements
        
        Criteria:
        - Has product name and description
        - Has at least 3 features
        - Features have priorities and acceptance criteria
        - Has at least 2 pages
        - Has at least 1 user flow
        - Has non-functional requirements
        - Has tech stack recommendations
        """
        criteria = {
            'has_product_name': bool(requirements.get('product_name')),
            'has_description': bool(requirements.get('description')),
            'has_features': len(requirements.get('features', [])) >= 3,
            'features_have_priorities': all(
                'priority' in f for f in requirements.get('features', [])
            ),
            'features_have_acceptance_criteria': all(
                'acceptance_criteria' in f and len(f['acceptance_criteria']) > 0
                for f in requirements.get('features', [])
            ),
            'has_pages': len(requirements.get('pages', [])) >= 2,
            'has_user_flows': len(requirements.get('user_flows', [])) >= 1,
            'has_nfr': bool(requirements.get('non_functional_requirements')),
            'has_tech_stack': bool(requirements.get('tech_stack_recommendations'))
        }
        
        # Weighted criteria
        weights = {
            'has_product_name': 1.0,
            'has_description': 1.0,
            'has_features': 2.0,
            'features_have_priorities': 1.5,
            'features_have_acceptance_criteria': 1.5,
            'has_pages': 1.0,
            'has_user_flows': 1.0,
            'has_nfr': 1.0,
            'has_tech_stack': 1.0
        }
        
        confidence = self._calculate_confidence(criteria, weights)
        
        # Log what's missing
        missing = [k for k, v in criteria.items() if not v]
        if missing:
            self.logger.warning(f"Requirements missing criteria: {missing}")
        
        return confidence


if __name__ == '__main__':
    # Test the agent
    from antigravity.llm.kimi_adapter import KimiAdapter
    
    adapter = KimiAdapter(api_key="MOCK_KEY")
    agent = ProductInterpreterAgent(llm_adapter=adapter)
    
    # Test input
    test_input = {
        'prompt': 'Build a task management app where users can create, assign, and track tasks with due dates',
        'context': {
            'target_audience': 'small teams',
            'key_features': ['task creation', 'assignments', 'due dates']
        }
    }
    
    result = agent.execute_with_retry(test_input)
    
    print(f"\nSuccess: {result.success}")
    print(f"Confidence: {result.confidence}%")
    print(f"\nRequirements:")
    print(json.dumps(result.outputs, indent=2))
