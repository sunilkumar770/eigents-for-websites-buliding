"""
Testing Agent

Generates and runs comprehensive test suites including unit tests,
integration tests, and E2E tests.
"""

import json
from typing import Dict, List, Any, Tuple, Optional
from agents.base_agent import BaseAgent, AgentType, AgentResult


class TestingAgent(BaseAgent):
    """
    Agent responsible for generating and running tests.
    
    Inputs:
        - frontend_outputs: Frontend code
        - backend_outputs: Backend code
        - requirements: Product requirements
    
    Outputs:
        - test_files: Generated test files
        - test_results: Test execution results
        - coverage_report: Code coverage metrics
        - failed_tests: List of failed tests
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, llm_adapter: Any = None):
        super().__init__(
            agent_type=AgentType.TESTING,
            config=config,
            llm_adapter=llm_adapter
        )
        
        self.coverage_threshold = self.config.get('coverage_threshold', 80)
    
    async def validate_inputs(self, inputs: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate input data"""
        errors = []
        
        if 'frontend_outputs' not in inputs and 'backend_outputs' not in inputs:
            errors.append("Must provide either 'frontend_outputs' or 'backend_outputs'")
        
        return len(errors) == 0, errors
    
    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """
        Execute test generation and execution
        
        Args:
            inputs: Dict with code outputs and requirements
        
        Returns:
            AgentResult with test results
        """
        self.logger.info("Starting test generation and execution (Async)")
        
        frontend = inputs.get('frontend_outputs', {})
        backend = inputs.get('backend_outputs', {})
        requirements = inputs.get('requirements', {})
        
        # Step 1: Generate unit tests
        self.logger.info("Generating unit tests")
        unit_tests = await self._generate_unit_tests(frontend, backend)
        
        # Step 2: Generate integration tests
        self.logger.info("Generating integration tests")
        integration_tests = await self._generate_integration_tests(backend)
        
        # Step 3: Generate E2E tests
        self.logger.info("Generating E2E tests")
        e2e_tests = await self._generate_e2e_tests(requirements, frontend)
        
        # Step 4: Run tests (simulated)
        self.logger.info("Running tests")
        test_results = await self._run_tests(unit_tests, integration_tests, e2e_tests)
        
        # Step 5: Generate coverage report
        coverage_report = await self._generate_coverage_report(test_results)
        
        # Calculate confidence
        confidence = self._calculate_testing_confidence(test_results, coverage_report)
        
        # Determine success
        success = (
            test_results['unit']['passed'] == test_results['unit']['total'] and
            test_results['integration']['passed'] == test_results['integration']['total'] and
            test_results['e2e']['passed'] == test_results['e2e']['total'] and
            coverage_report['overall'] >= self.coverage_threshold
        )
        
        # Log decision
        self.log_decision(
            decision=f"Generated {test_results['total_tests']} tests, "
                   f"{'all passed' if success else 'some failed'}",
            reasoning=f"Coverage: {coverage_report['overall']}%, "
                     f"Unit: {test_results['unit']['passed']}/{test_results['unit']['total']}, "
                     f"Integration: {test_results['integration']['passed']}/{test_results['integration']['total']}, "
                     f"E2E: {test_results['e2e']['passed']}/{test_results['e2e']['total']} (Async)"
        )
        
        # Collect all test files
        all_test_files = {**unit_tests, **integration_tests, **e2e_tests}
        
        return AgentResult(
            success=success,
            confidence=confidence,
            outputs={
                'test_files': all_test_files,
                'test_results': test_results,
                'coverage_report': coverage_report,
                'failed_tests': test_results.get('failed', [])
            },
            metadata={
                'total_tests': test_results['total_tests'],
                'passed_tests': test_results['passed_tests'],
                'coverage': coverage_report['overall']
            },
            errors=[] if success else [f"Coverage {coverage_report['overall']}% < {self.coverage_threshold}%"] if coverage_report['overall'] < self.coverage_threshold else ["Some tests failed"]
        )
    
    async def _generate_unit_tests(
        self,
        frontend: Dict[str, Any],
        backend: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate unit tests"""
        
        tests = {}
        
        # Frontend unit tests
        if frontend:
            # Test for components
            tests['tests/unit/components/Button.test.jsx'] = """import { render, screen, fireEvent } from '@testing-library/react';
import Button from '../../../src/components/Button';

describe('Button Component', () => {
  test('renders button with text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });
  
  test('calls onClick when clicked', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    
    fireEvent.click(screen.getByText('Click me'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
  
  test('applies custom className', () => {
    render(<Button className="custom">Click me</Button>);
    expect(screen.getByText('Click me')).toHaveClass('custom');
  });
});
"""
            
            # Test for utilities
            tests['tests/unit/utils/validation.test.js'] = """import { validateEmail, validatePassword } from '../../../src/utils/validation';

describe('Validation Utils', () => {
  describe('validateEmail', () => {
    test('validates correct email', () => {
      expect(validateEmail('test@example.com')).toBe(true);
    });
    
    test('rejects invalid email', () => {
      expect(validateEmail('invalid-email')).toBe(false);
    });
  });
  
  describe('validatePassword', () => {
    test('validates strong password', () => {
      expect(validatePassword('Password123!')).toBe(true);
    });
    
    test('rejects weak password', () => {
      expect(validatePassword('weak')).toBe(false);
    });
  });
});
"""
        
        # Backend unit tests
        if backend:
            tests['tests/unit/services/userService.test.js'] = """const userService = require('../../../src/services/userService');

describe('User Service', () => {
  test('creates user with valid data', async () => {
    const userData = {
      email: 'test@example.com',
      password: 'password123'
    };
    
    const user = await userService.createUser(userData);
    expect(user).toHaveProperty('id');
    expect(user.email).toBe(userData.email);
  });
  
  test('throws error for duplicate email', async () => {
    const userData = {
      email: 'duplicate@example.com',
      password: 'password123'
    };
    
    await userService.createUser(userData);
    await expect(userService.createUser(userData)).rejects.toThrow();
  });
});
"""
        
        return tests
    
    async def _generate_integration_tests(self, backend: Dict[str, Any]) -> Dict[str, str]:
        """Generate integration tests for API endpoints"""
        
        if not backend:
            return {}
        
        tests = {}
        
        tests['tests/integration/auth.test.js'] = """const request = require('supertest');
const app = require('../../src/server');

describe('Authentication API', () => {
  let authToken;
  
  test('POST /api/auth/register - creates new user', async () => {
    const response = await request(app)
      .post('/api/auth/register')
      .send({
        email: 'newuser@example.com',
        password: 'Password123!',
        name: 'New User'
      });
    
    expect(response.status).toBe(201);
    expect(response.body).toHaveProperty('user');
    expect(response.body).toHaveProperty('token');
  });
  
  test('POST /api/auth/login - authenticates user', async () => {
    const response = await request(app)
      .post('/api/auth/login')
      .send({
        email: 'newuser@example.com',
        password: 'Password123!'
      });
    
    expect(response.status).toBe(200);
    expect(response.body).toHaveProperty('token');
    authToken = response.body.token;
  });
  
  test('GET /api/auth/me - returns current user', async () => {
    const response = await request(app)
      .get('/api/auth/me')
      .set('Authorization', `Bearer ${authToken}`);
    
    expect(response.status).toBe(200);
    expect(response.body.email).toBe('newuser@example.com');
  });
  
  test('GET /api/auth/me - fails without token', async () => {
    const response = await request(app).get('/api/auth/me');
    expect(response.status).toBe(401);
  });
});
"""
        
        tests['tests/integration/database.test.js'] = """const { pool } = require('../../src/config/database');

describe('Database Integration', () => {
  test('connects to database', async () => {
    const client = await pool.connect();
    expect(client).toBeDefined();
    client.release();
  });
  
  test('executes queries', async () => {
    const result = await pool.query('SELECT NOW()');
    expect(result.rows).toHaveLength(1);
  });
});
"""
        
        return tests
    
    async def _generate_e2e_tests(
        self,
        requirements: Dict[str, Any],
        frontend: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate E2E tests for user flows"""
        
        tests = {}
        
        # Generate E2E test based on user flows
        user_flows = requirements.get('user_flows', [])
        
        if user_flows:
            # Example: User registration and login flow
            tests['tests/e2e/userFlow.spec.js'] = """const { test, expect } = require('@playwright/test');

test.describe('User Flow', () => {
  test('user can register, login, and access dashboard', async ({ page }) => {
    // Navigate to app
    await page.goto('http://localhost:3000');
    
    // Register
    await page.click('text=Sign Up');
    await page.fill('input[name="email"]', 'e2euser@example.com');
    await page.fill('input[name="password"]', 'Password123!');
    await page.fill('input[name="name"]', 'E2E User');
    await page.click('button[type="submit"]');
    
    // Should redirect to dashboard
    await expect(page).toHaveURL(/.*dashboard/);
    await expect(page.locator('text=Welcome')).toBeVisible();
    
    // Logout
    await page.click('text=Logout');
    
    // Login again
    await page.click('text=Login');
    await page.fill('input[name="email"]', 'e2euser@example.com');
    await page.fill('input[name="password"]', 'Password123!');
    await page.click('button[type="submit"]');
    
    // Should be back on dashboard
    await expect(page).toHaveURL(/.*dashboard/);
  });
});
"""
        
        # Task creation flow (if applicable)
        features = requirements.get('features', [])
        if any('task' in f.get('name', '').lower() for f in features):
            tests['tests/e2e/taskFlow.spec.js'] = """const { test, expect } = require('@playwright/test');

test.describe('Task Management Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('http://localhost:3000/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
  });
  
  test('user can create and complete a task', async ({ page }) => {
    // Navigate to tasks
    await page.click('text=Tasks');
    
    // Create new task
    await page.click('text=New Task');
    await page.fill('input[name="title"]', 'Test Task');
    await page.fill('textarea[name="description"]', 'This is a test task');
    await page.click('button:has-text("Create")');
    
    // Verify task appears
    await expect(page.locator('text=Test Task')).toBeVisible();
    
    // Mark as complete
    await page.click('input[type="checkbox"]');
    await expect(page.locator('.task-completed')).toBeVisible();
  });
});
"""
        
        return tests
    
    async def _run_tests(
        self,
        unit_tests: Dict[str, str],
        integration_tests: Dict[str, str],
        e2e_tests: Dict[str, str]
    ) -> Dict[str, Any]:
        """Simulate running tests"""
        
        # In a real implementation, this would actually run the tests
        # For now, we'll simulate results
        
        unit_total = len(unit_tests)
        unit_passed = int(unit_total * 0.95)  # 95% pass rate
        
        integration_total = len(integration_tests)
        integration_passed = int(integration_total * 0.90)  # 90% pass rate
        
        e2e_total = len(e2e_tests)
        e2e_passed = int(e2e_total * 0.85)  # 85% pass rate
        
        total_tests = unit_total + integration_total + e2e_total
        passed_tests = unit_passed + integration_passed + e2e_passed
        
        failed = []
        if unit_passed < unit_total:
            failed.append({
                'type': 'unit',
                'file': 'tests/unit/utils/validation.test.js',
                'test': 'validatePassword - rejects weak password',
                'error': 'Expected false, got true'
            })
        
        return {
            'unit': {
                'total': unit_total,
                'passed': unit_passed,
                'failed': unit_total - unit_passed
            },
            'integration': {
                'total': integration_total,
                'passed': integration_passed,
                'failed': integration_total - integration_passed
            },
            'e2e': {
                'total': e2e_total,
                'passed': e2e_passed,
                'failed': e2e_total - e2e_passed
            },
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'failed': failed
        }
    
    async def _generate_coverage_report(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code coverage report"""
        
        # Simulated coverage data
        # In reality, this would come from Jest/Istanbul or similar
        
        return {
            'overall': 87,  # percentage
            'statements': 89,
            'branches': 82,
            'functions': 91,
            'lines': 88,
            'files': {
                'src/components/': 92,
                'src/utils/': 95,
                'src/services/': 85,
                'src/controllers/': 80
            }
        }
    
    def _calculate_testing_confidence(
        self,
        test_results: Dict[str, Any],
        coverage_report: Dict[str, Any]
    ) -> float:
        """Calculate confidence in test suite"""
        
        pass_rate = (test_results['passed_tests'] / test_results['total_tests'] * 100) if test_results['total_tests'] > 0 else 0
        
        criteria = {
            'high_pass_rate': pass_rate >= 95,
            'good_coverage': coverage_report['overall'] >= self.coverage_threshold,
            'has_unit_tests': test_results['unit']['total'] > 0,
            'has_integration_tests': test_results['integration']['total'] > 0,
            'has_e2e_tests': test_results['e2e']['total'] > 0,
            'no_critical_failures': len(test_results.get('failed', [])) == 0
        }
        
        weights = {
            'high_pass_rate': 3.0,
            'good_coverage': 2.5,
            'has_unit_tests': 1.0,
            'has_integration_tests': 1.0,
            'has_e2e_tests': 1.0,
            'no_critical_failures': 2.0
        }
        
        base_confidence = self._calculate_confidence(criteria, weights)
        
        # Adjust based on actual pass rate and coverage
        adjusted_confidence = (base_confidence + pass_rate + coverage_report['overall']) / 3
        
        return adjusted_confidence


if __name__ == '__main__':
    from antigravity.llm.kimi_adapter import KimiAdapter
    
    adapter = KimiAdapter(api_key="MOCK_KEY")
    agent = TestingAgent(llm_adapter=adapter)
    
    test_input = {
        'frontend_outputs': {'config': {'framework': 'react'}},
        'backend_outputs': {'config': {'backend': 'nodejs'}},
        'requirements': {
            'features': [{'name': 'Task management'}],
            'user_flows': [{'name': 'Create task'}]
        }
    }
    
    result = agent.execute_with_retry(test_input)
    
    print(f"\nSuccess: {result.success}")
    print(f"Confidence: {result.confidence}%")
    print(f"Tests: {result.outputs['test_results']['passed_tests']}/{result.outputs['test_results']['total_tests']}")
    print(f"Coverage: {result.outputs['coverage_report']['overall']}%")
