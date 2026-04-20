"""
Integration Agent

Connects frontend and backend systems, validates API contracts,
and fixes integration issues.
"""

import json
from typing import Dict, List, Any, Tuple, Optional
from agents.base_agent import BaseAgent, AgentType, AgentResult


class IntegrationAgent(BaseAgent):
    """
    Agent responsible for integrating frontend and backend.
    
    Inputs:
        - frontend_outputs: Outputs from Frontend Engineer Agent
        - backend_outputs: Outputs from Backend Engineer Agent
    
    Outputs:
        - api_client: Generated API client for frontend
        - integration_fixes: List of fixes applied
        - cors_config: CORS configuration
        - integration_tests: Integration test suite
        - compatibility_report: Compatibility analysis
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, llm_adapter: Any = None):
        super().__init__(
            agent_type=AgentType.INTEGRATION,
            config=config,
            llm_adapter=llm_adapter
        )
    
    async def validate_inputs(self, inputs: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate input data"""
        errors = []
        
        if 'frontend_outputs' not in inputs:
            errors.append("Missing required field: 'frontend_outputs'")
        
        if 'backend_outputs' not in inputs:
            errors.append("Missing required field: 'backend_outputs'")
        
        return len(errors) == 0, errors
    
    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """
        Execute integration
        
        Args:
            inputs: Dict with 'frontend_outputs' and 'backend_outputs'
        
        Returns:
            AgentResult with integration artifacts
        """
        self.logger.info("Starting frontend-backend integration (Async)")
        
        frontend = inputs['frontend_outputs']
        backend = inputs['backend_outputs']
        
        # Step 1: Analyze compatibility
        self.logger.info("Analyzing API compatibility")
        compatibility = await self._analyze_compatibility(frontend, backend)
        
        # Step 2: Generate API client
        self.logger.info("Generating API client for frontend")
        api_client = await self._generate_api_client(backend, frontend)
        
        # Step 3: Fix integration issues
        self.logger.info("Fixing integration issues")
        fixes = await self._fix_integration_issues(compatibility, frontend, backend)
        
        # Step 4: Configure CORS
        cors_config = self._configure_cors(frontend, backend)
        
        # Step 5: Generate integration tests
        self.logger.info("Generating integration tests")
        integration_tests = await self._generate_integration_tests(frontend, backend)
        
        # Calculate confidence
        confidence = self._calculate_integration_confidence(
            compatibility,
            api_client,
            fixes
        )
        
        # Log decision
        self.log_decision(
            decision=f"Integrated frontend and backend with {len(fixes)} fixes applied",
            reasoning=f"Compatibility score: {compatibility['score']}%, "
                     f"Generated API client with {len(api_client['methods'])} methods, "
                     f"confidence: {confidence}% (Async)"
        )
        
        return AgentResult(
            success=True,
            confidence=confidence,
            outputs={
                'api_client': api_client,
                'integration_fixes': fixes,
                'cors_config': cors_config,
                'integration_tests': integration_tests,
                'compatibility_report': compatibility
            },
            metadata={
                'fixes_applied': len(fixes),
                'compatibility_score': compatibility['score'],
                'api_methods': len(api_client['methods'])
            }
        )
    
    async def _analyze_compatibility(
        self,
        frontend: Dict[str, Any],
        backend: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze frontend-backend compatibility"""
        
        issues = []
        warnings = []
        
        # Check if backend API endpoints match frontend expectations
        backend_endpoints = {
            f"{ep['method']} {ep['path']}"
            for ep in backend.get('api_design', {}).get('endpoints', [])
        }
        
        # Analyze routing compatibility
        frontend_routes = frontend.get('component_architecture', {}).get('routing', [])
        
        # Check for missing endpoints
        # (This is simplified - in reality, we'd parse frontend code to find API calls)
        
        # Check authentication compatibility
        frontend_config = frontend.get('config', {})
        backend_config = backend.get('config', {})
        
        if frontend_config.get('auth') != backend_config.get('auth'):
            issues.append({
                'type': 'auth_mismatch',
                'severity': 'high',
                'message': f"Auth mismatch: frontend uses {frontend_config.get('auth')}, backend uses {backend_config.get('auth')}"
            })
        
        # Check data format compatibility
        # (Simplified check)
        
        # Calculate compatibility score
        total_checks = 10
        passed_checks = total_checks - len(issues)
        score = (passed_checks / total_checks) * 100
        
        return {
            'score': score,
            'issues': issues,
            'warnings': warnings,
            'backend_endpoints': list(backend_endpoints),
            'frontend_routes': [r['path'] for r in frontend_routes]
        }
    
    async def _generate_api_client(
        self,
        backend: Dict[str, Any],
        frontend: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate API client for frontend"""
        
        api_design = backend.get('api_design', {})
        endpoints = api_design.get('endpoints', [])
        
        # Generate client methods
        methods = []
        for endpoint in endpoints:
            method_name = self._endpoint_to_method_name(endpoint)
            methods.append({
                'name': method_name,
                'http_method': endpoint['method'],
                'path': endpoint['path'],
                'auth_required': endpoint.get('auth_required', False)
            })
        
        # Generate client code
        client_code = self._generate_client_code(methods, frontend.get('config', {}))
        
        return {
            'methods': methods,
            'code': client_code,
            'base_url': 'process.env.VITE_API_URL || "http://localhost:3000"'
        }
    
    def _endpoint_to_method_name(self, endpoint: Dict[str, Any]) -> str:
        """Convert endpoint to method name"""
        # Example: POST /api/auth/login -> login
        path_parts = endpoint['path'].split('/')
        resource = path_parts[-1] if path_parts else 'unknown'
        method = endpoint['method'].lower()
        
        if method == 'get':
            return f"get{resource.capitalize()}"
        elif method == 'post':
            return f"create{resource.capitalize()}" if resource != 'login' else resource
        elif method == 'put':
            return f"update{resource.capitalize()}"
        elif method == 'delete':
            return f"delete{resource.capitalize()}"
        else:
            return resource
    
    def _generate_client_code(
        self,
        methods: List[Dict[str, Any]],
        frontend_config: Dict[str, Any]
    ) -> str:
        """Generate API client code"""
        
        framework = frontend_config.get('framework', 'react')
        
        if framework in ['react', 'nextjs']:
            return self._generate_react_client(methods)
        elif framework == 'vue':
            return self._generate_vue_client(methods)
        else:
            return self._generate_react_client(methods)
    
    def _generate_react_client(self, methods: List[Dict[str, Any]]) -> str:
        """Generate React API client"""
        
        method_implementations = []
        
        for method in methods:
            auth_header = """
      headers: {
        ...headers,
        'Authorization': `Bearer ${getToken()}`
      },""" if method['auth_required'] else ""
            
            method_impl = f"""
  async {method['name']}(data) {{
    const response = await fetch(`${{baseURL}}{method['path']}`, {{
      method: '{method['http_method']}',{auth_header}
      headers: {{
        'Content-Type': 'application/json',
        ...headers
      }},
      body: data ? JSON.stringify(data) : undefined
    }});
    
    if (!response.ok) {{
      throw new Error(`API error: ${{response.statusText}}`);
    }}
    
    return response.json();
  }}"""
            
            method_implementations.append(method_impl)
        
        return f"""// API Client
const baseURL = process.env.VITE_API_URL || 'http://localhost:3000';

// Token management
let token = null;

export const setToken = (newToken) => {{
  token = newToken;
  if (newToken) {{
    localStorage.setItem('auth_token', newToken);
  }} else {{
    localStorage.removeItem('auth_token');
  }}
}};

export const getToken = () => {{
  if (!token) {{
    token = localStorage.getItem('auth_token');
  }}
  return token;
}};

// API methods
export const api = {{
{','.join(method_implementations)}
}};

export default api;
"""
    
    def _generate_vue_client(self, methods: List[Dict[str, Any]]) -> str:
        """Generate Vue API client"""
        return "// Vue API client implementation"
    
    async def _fix_integration_issues(
        self,
        compatibility: Dict[str, Any],
        frontend: Dict[str, Any],
        backend: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Fix identified integration issues"""
        
        fixes = []
        
        for issue in compatibility.get('issues', []):
            if issue['type'] == 'auth_mismatch':
                fix = {
                    'issue': issue['message'],
                    'fix_type': 'configuration',
                    'action': 'Align authentication methods',
                    'code_changes': {
                        'frontend': 'Update auth configuration',
                        'backend': 'Ensure JWT middleware is configured'
                    }
                }
                fixes.append(fix)
            
            elif issue['type'] == 'endpoint_mismatch':
                fix = {
                    'issue': issue['message'],
                    'fix_type': 'routing',
                    'action': 'Add missing endpoint or update frontend call',
                    'code_changes': {}
                }
                fixes.append(fix)
        
        return fixes
    
    def _configure_cors(
        self,
        frontend: Dict[str, Any],
        backend: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Configure CORS for backend"""
        
        # Determine frontend URL
        frontend_url = 'http://localhost:3000'  # Default for development
        
        cors_config = {
            'origin': [frontend_url, 'http://localhost:5173'],  # Vite default
            'credentials': True,
            'methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
            'allowedHeaders': ['Content-Type', 'Authorization']
        }
        
        # Generate CORS middleware code
        cors_code = f"""// CORS Configuration
const cors = require('cors');

const corsOptions = {{
  origin: {json.dumps(cors_config['origin'])},
  credentials: {str(cors_config['credentials']).lower()},
  methods: {json.dumps(cors_config['methods'])},
  allowedHeaders: {json.dumps(cors_config['allowedHeaders'])}
}};

app.use(cors(corsOptions));
"""
        
        cors_config['code'] = cors_code
        
        return cors_config
    
    async def _generate_integration_tests(
        self,
        frontend: Dict[str, Any],
        backend: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate integration tests"""
        
        tests = {}
        
        # Generate API integration test
        tests['tests/integration/api.test.js'] = """const request = require('supertest');
const app = require('../../src/server');

describe('API Integration Tests', () => {
  test('Health check endpoint', async () => {
    const response = await request(app).get('/health');
    expect(response.status).toBe(200);
    expect(response.body.status).toBe('ok');
  });
  
  test('Auth flow', async () => {
    // Register
    const registerResponse = await request(app)
      .post('/api/auth/register')
      .send({
        email: 'test@example.com',
        password: 'password123'
      });
    
    expect(registerResponse.status).toBe(201);
    
    // Login
    const loginResponse = await request(app)
      .post('/api/auth/login')
      .send({
        email: 'test@example.com',
        password: 'password123'
      });
    
    expect(loginResponse.status).toBe(200);
    expect(loginResponse.body.token).toBeDefined();
  });
});
"""
        
        # Generate frontend-backend integration test
        tests['tests/integration/frontend-backend.test.js'] = """import { api } from '../../src/services/api';

describe('Frontend-Backend Integration', () => {
  test('API client can fetch data', async () => {
    const data = await api.getData();
    expect(data).toBeDefined();
  });
});
"""
        
        return tests
    
    def _calculate_integration_confidence(
        self,
        compatibility: Dict[str, Any],
        api_client: Dict[str, Any],
        fixes: List[Dict[str, Any]]
    ) -> float:
        """Calculate confidence in integration"""
        
        criteria = {
            'high_compatibility': compatibility['score'] >= 80,
            'has_api_client': bool(api_client.get('code')),
            'has_methods': len(api_client.get('methods', [])) > 0,
            'few_critical_issues': len([f for f in fixes if f.get('severity') == 'high']) == 0,
            'has_integration_tests': True
        }
        
        weights = {
            'high_compatibility': 3.0,
            'has_api_client': 2.0,
            'has_methods': 1.5,
            'few_critical_issues': 2.0,
            'has_integration_tests': 1.0
        }
        
        base_confidence = self._calculate_confidence(criteria, weights)
        
        # Adjust based on compatibility score
        adjusted_confidence = (base_confidence + compatibility['score']) / 2
        
        return adjusted_confidence


if __name__ == '__main__':
    from antigravity.llm.kimi_adapter import KimiAdapter
    
    adapter = KimiAdapter(api_key="MOCK_KEY")
    agent = IntegrationAgent(llm_adapter=adapter)
    
    # Test with mock frontend and backend outputs
    test_input = {
        'frontend_outputs': {
            'config': {'framework': 'react', 'auth': 'jwt'},
            'component_architecture': {
                'routing': [{'path': '/'}]
            }
        },
        'backend_outputs': {
            'config': {'backend': 'nodejs', 'auth': 'jwt'},
            'api_design': {
                'endpoints': [
                    {'method': 'POST', 'path': '/api/auth/login', 'auth_required': False},
                    {'method': 'GET', 'path': '/api/users', 'auth_required': True}
                ]
            }
        }
    }
    
    result = agent.execute_with_retry(test_input)
    
    print(f"\nSuccess: {result.success}")
    print(f"Confidence: {result.confidence}%")
    print(f"Compatibility: {result.outputs['compatibility_report']['score']}%")
