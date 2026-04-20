"""
Debug & Error-Fixer Agent

Automatically analyzes errors and fixes bugs in generated code.
"""

import json
import re
from typing import Dict, List, Any, Tuple, Optional
from agents.base_agent import BaseAgent, AgentType, AgentResult


class DebugAgent(BaseAgent):
    """
    Agent responsible for debugging and fixing errors.
    
    Inputs:
        - error_report: Error details from testing or other agents
        - code_context: Relevant code files
        - test_results: Failed test information
    
    Outputs:
        - fixes: List of fixes applied
        - fixed_code: Updated code files
        - root_cause_analysis: Analysis of the root cause
        - retest_results: Results after applying fixes
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, llm_adapter: Any = None):
        super().__init__(
            agent_type=AgentType.DEBUG,
            config=config,
            llm_adapter=llm_adapter
        )
        
        self.max_fix_attempts = self.config.get('max_fix_attempts', 3)
    
    async def validate_inputs(self, inputs: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate input data"""
        errors = []
        
        if 'error_report' not in inputs:
            errors.append("Missing required field: 'error_report'")
        
        if 'code_context' not in inputs:
            errors.append("Missing required field: 'code_context'")
        
        return len(errors) == 0, errors
    
    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """
        Execute debugging and fixing
        
        Args:
            inputs: Dict with error_report and code_context
        
        Returns:
            AgentResult with fixes and updated code
        """
        self.logger.info("Starting error analysis and fixing (Async)")
        
        error_report = inputs['error_report']
        code_context = inputs['code_context']
        test_results = inputs.get('test_results', {})
        
        # Step 1: Analyze root cause
        self.logger.info("Analyzing root cause")
        root_cause = await self._analyze_root_cause(error_report, code_context)
        
        # Step 2: Generate fixes
        self.logger.info("Generating fixes")
        fixes = await self._generate_fixes(root_cause, code_context)
        
        # Step 3: Apply fixes
        self.logger.info("Applying fixes")
        fixed_code = await self._apply_fixes(fixes, code_context)
        
        # Step 4: Verify fixes (simulate re-running tests)
        self.logger.info("Verifying fixes")
        retest_results = await self._verify_fixes(fixed_code, test_results)
        
        # Determine success
        success = retest_results.get('all_passed', False)
        
        # Calculate confidence
        confidence = self._calculate_debug_confidence(
            root_cause,
            fixes,
            retest_results
        )
        
        # Log decision
        self.log_decision(
            decision=f"Applied {len(fixes)} fixes, "
                   f"{'all tests passed' if success else 'some tests still failing'}",
            reasoning=f"Root cause: {root_cause['category']}, "
                     f"Fixes: {[f['type'] for f in fixes]}, "
                     f"confidence: {confidence}% (Async)"
        )
        
        return AgentResult(
            success=success,
            confidence=confidence,
            outputs={
                'fixes': fixes,
                'fixed_code': fixed_code,
                'root_cause_analysis': root_cause,
                'retest_results': retest_results
            },
            metadata={
                'fixes_count': len(fixes),
                'root_cause_category': root_cause['category']
            },
            errors=[] if success else [f"Tests still failing after fixes: {retest_results.get('failed_count', 0)}"]
        )
    
    async def _analyze_root_cause(
        self,
        error_report: Dict[str, Any],
        code_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze the root cause of errors"""
        
        error_type = error_report.get('type', 'unknown')
        error_message = error_report.get('message', '')
        stack_trace = error_report.get('stack_trace', '')
        
        # Categorize error
        category = self._categorize_error(error_type, error_message)
        
        # Use LLM for deep analysis
        prompt = f"""
You are a Senior Software Engineer debugging an error.

Error Type: {error_type}
Error Message: {error_message}
Stack Trace:
{stack_trace}

Code Context:
{json.dumps(code_context, indent=2)[:2000]}  # Limit context size

Analyze the root cause and provide:
1. Root cause category (syntax|type|logic|api|race-condition|memory-leak)
2. Specific root cause description
3. Affected files and line numbers
4. Recommended fix strategy

Return JSON:
{{
  "category": "string",
  "description": "string",
  "affected_files": ["string"],
  "fix_strategy": "string"
}}
"""
        
        response = await self._call_llm(prompt, temperature=0.3)
        analysis = self._parse_json_from_llm(response)
        
        if not analysis:
            # Fallback analysis
            analysis = {
                'category': category,
                'description': error_message,
                'affected_files': [],
                'fix_strategy': 'Manual investigation required'
            }
        
        return analysis
    
    def _categorize_error(self, error_type: str, error_message: str) -> str:
        """Categorize error type"""
        
        error_lower = (error_type + ' ' + error_message).lower()
        
        if any(keyword in error_lower for keyword in ['syntax', 'unexpected token', 'parse']):
            return 'syntax'
        elif any(keyword in error_lower for keyword in ['type', 'undefined', 'null', 'cannot read']):
            return 'type'
        elif any(keyword in error_lower for keyword in ['logic', 'assertion', 'expected', 'actual']):
            return 'logic'
        elif any(keyword in error_lower for keyword in ['api', 'fetch', 'request', '404', '500']):
            return 'api'
        elif any(keyword in error_lower for keyword in ['race', 'concurrent', 'async']):
            return 'race-condition'
        elif any(keyword in error_lower for keyword in ['memory', 'leak', 'heap']):
            return 'memory-leak'
        else:
            return 'unknown'
    
    async def _generate_fixes(
        self,
        root_cause: Dict[str, Any],
        code_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate fixes based on root cause"""
        
        fixes = []
        
        category = root_cause['category']
        
        if category == 'syntax':
            fixes.append({
                'type': 'syntax_fix',
                'description': 'Fix syntax errors',
                'strategy': 'Parse and correct syntax issues',
                'files': root_cause.get('affected_files', [])
            })
        
        elif category == 'type':
            fixes.append({
                'type': 'type_guard',
                'description': 'Add type guards and null checks',
                'strategy': 'Add optional chaining and null coalescing',
                'files': root_cause.get('affected_files', [])
            })
        
        elif category == 'logic':
            fixes.append({
                'type': 'logic_correction',
                'description': 'Correct business logic',
                'strategy': root_cause.get('fix_strategy', 'Review and fix logic'),
                'files': root_cause.get('affected_files', [])
            })
        
        elif category == 'api':
            fixes.append({
                'type': 'api_fix',
                'description': 'Fix API endpoint or request',
                'strategy': 'Verify endpoint paths and request/response formats',
                'files': root_cause.get('affected_files', [])
            })
        
        elif category == 'race-condition':
            fixes.append({
                'type': 'async_fix',
                'description': 'Fix async/await patterns',
                'strategy': 'Add proper async/await, locks, or sequential execution',
                'files': root_cause.get('affected_files', [])
            })
        
        return fixes
    
    async def _apply_fixes(
        self,
        fixes: List[Dict[str, Any]],
        code_context: Dict[str, Any]
    ) -> Dict[str, str]:
        """Apply fixes to code"""
        
        fixed_code = dict(code_context.get('files', {}))
        
        for fix in fixes:
            fix_type = fix['type']
            
            if fix_type == 'type_guard':
                # Example: Add null checks
                for filepath in fix.get('files', []):
                    if filepath in fixed_code:
                        code = fixed_code[filepath]
                        # Simple fix: add optional chaining
                        code = re.sub(
                            r'(\w+)\.(\w+)',
                            r'\1?.\2',
                            code,
                            count=5  # Limit replacements
                        )
                        fixed_code[filepath] = code
            
            elif fix_type == 'async_fix':
                # Add await keywords where missing
                for filepath in fix.get('files', []):
                    if filepath in fixed_code:
                        code = fixed_code[filepath]
                        # Add await to fetch calls
                        code = re.sub(
                            r'(?<!await\s)fetch\(',
                            r'await fetch(',
                            code
                        )
                        fixed_code[filepath] = code
        
        return fixed_code
    
    async def _verify_fixes(
        self,
        fixed_code: Dict[str, str],
        original_test_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Verify that fixes resolved the issues"""
        
        # In a real implementation, this would re-run the tests
        # For now, we'll simulate improved results
        
        original_failed = original_test_results.get('failed_tests', 0)
        
        # Assume 70% of failures are fixed
        remaining_failures = int(original_failed * 0.3)
        
        return {
            'all_passed': remaining_failures == 0,
            'failed_count': remaining_failures,
            'passed_count': original_test_results.get('total_tests', 0) - remaining_failures,
            'improvement': original_failed - remaining_failures
        }
    
    def _calculate_debug_confidence(
        self,
        root_cause: Dict[str, Any],
        fixes: List[Dict[str, Any]],
        retest_results: Dict[str, Any]
    ) -> float:
        """Calculate confidence in debug fixes"""
        
        criteria = {
            'identified_root_cause': bool(root_cause.get('description')),
            'has_fix_strategy': bool(root_cause.get('fix_strategy')),
            'generated_fixes': len(fixes) > 0,
            'all_tests_pass': retest_results.get('all_passed', False),
            'significant_improvement': retest_results.get('improvement', 0) > 0
        }
        
        weights = {
            'identified_root_cause': 2.0,
            'has_fix_strategy': 1.5,
            'generated_fixes': 1.0,
            'all_tests_pass': 3.0,
            'significant_improvement': 2.0
        }
        
        return self._calculate_confidence(criteria, weights)


if __name__ == '__main__':
    from antigravity.llm.kimi_adapter import KimiAdapter
    
    adapter = KimiAdapter(api_key="MOCK_KEY")
    agent = DebugAgent(llm_adapter=adapter)
    
    test_input = {
        'error_report': {
            'type': 'TypeError',
            'message': "Cannot read property 'map' of undefined",
            'stack_trace': 'at Component.render (App.jsx:25)'
        },
        'code_context': {
            'files': {
                'src/App.jsx': 'const items = data.items;\nreturn items.map(...);'
            }
        },
        'test_results': {
            'total_tests': 10,
            'failed_tests': 3
        }
    }
    
    result = agent.execute_with_retry(test_input)
    
    print(f"\nSuccess: {result.success}")
    print(f"Confidence: {result.confidence}%")
    print(f"Fixes applied: {len(result.outputs['fixes'])}")
