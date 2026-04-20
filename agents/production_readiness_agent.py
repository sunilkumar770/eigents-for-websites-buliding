"""
Production Readiness Agent

Validates that the application is ready for production deployment.
"""

import json
from typing import Dict, List, Any, Tuple, Optional
from agents.base_agent import BaseAgent, AgentType, AgentResult


class ProductionReadinessAgent(BaseAgent):
    """
    Agent responsible for production readiness validation.
    
    Inputs:
        - frontend_outputs: Frontend code and config
        - backend_outputs: Backend code and config
        - test_results: Testing results
        - security_report: Security audit results
    
    Outputs:
        - readiness_report: Production readiness assessment
        - deployment_checklist: Checklist of deployment steps
        - infrastructure_config: Infrastructure as code templates
        - monitoring_config: Monitoring and alerting setup
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, llm_adapter: Any = None):
        super().__init__(
            agent_type=AgentType.PRODUCTION_READINESS,
            config=config,
            llm_adapter=llm_adapter
        )
        
        self.readiness_threshold = self.config.get('readiness_threshold', 90)
    
    async def validate_inputs(self, inputs: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate input data"""
        errors = []
        
        if 'backend_outputs' not in inputs and 'frontend_outputs' not in inputs:
            errors.append("Must provide either 'backend_outputs' or 'frontend_outputs'")
        
        return len(errors) == 0, errors
    
    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """
        Execute production readiness validation
        
        Args:
            inputs: Dict with code outputs and test results
        
        Returns:
            AgentResult with readiness assessment
        """
        self.logger.info("Starting production readiness validation (Async)")
        
        frontend = inputs.get('frontend_outputs', {})
        backend = inputs.get('backend_outputs', {})
        test_results = inputs.get('test_results', {})
        security_report = inputs.get('security_report', {})
        
        # Step 1: Environment configuration check
        self.logger.info("Checking environment configuration")
        env_check = await self._check_environment_config(frontend, backend)
        
        # Step 2: Database readiness
        self.logger.info("Checking database readiness")
        db_check = await self._check_database_readiness(backend)
        
        # Step 3: API health checks
        self.logger.info("Validating API health endpoints")
        api_check = await self._check_api_health(backend)
        
        # Step 4: Frontend build optimization
        self.logger.info("Checking frontend build optimization")
        frontend_check = await self._check_frontend_optimization(frontend)
        
        # Step 5: Security headers and HTTPS
        self.logger.info("Validating security configuration")
        security_check = await self._check_security_config(backend, security_report)
        
        # Step 6: Monitoring and logging
        self.logger.info("Checking monitoring setup")
        monitoring_check = await self._check_monitoring(backend)
        
        # Step 7: Backup and recovery
        self.logger.info("Validating backup strategy")
        backup_check = await self._check_backup_strategy(backend)
        
        # Step 8: Performance and scalability
        self.logger.info("Checking performance readiness")
        performance_check = await self._check_performance(frontend, backend)
        
        # Compile all checks
        all_checks = {
            'environment': env_check,
            'database': db_check,
            'api_health': api_check,
            'frontend_optimization': frontend_check,
            'security': security_check,
            'monitoring': monitoring_check,
            'backup': backup_check,
            'performance': performance_check
        }
        
        # Calculate overall readiness score
        readiness_score = self._calculate_readiness_score(all_checks)
        
        # Generate deployment checklist
        deployment_checklist = self._generate_deployment_checklist(all_checks)
        
        # Generate infrastructure config
        infrastructure_config = self._generate_infrastructure_config(frontend, backend)
        
        # Generate monitoring config
        monitoring_config = self._generate_monitoring_config(backend)
        
        # Determine success
        critical_failures = [
            name for name, check in all_checks.items()
            if not check['passed'] and check['severity'] == 'critical'
        ]
        
        success = len(critical_failures) == 0 and readiness_score >= self.readiness_threshold
        
        # Calculate confidence
        confidence = self._calculate_production_confidence(all_checks, readiness_score)
        
        # Log decision
        self.log_decision(
            decision=f"Production readiness: {readiness_score}/100, "
                   f"{'READY' if success else 'NOT READY'}",
            reasoning=f"Passed {sum(1 for c in all_checks.values() if c['passed'])}/{len(all_checks)} checks, "
                     f"Critical failures: {len(critical_failures)} (Async)"
        )
        
        return AgentResult(
            success=success,
            confidence=confidence,
            outputs={
                'readiness_report': {
                    'score': readiness_score,
                    'checks': all_checks,
                    'critical_failures': critical_failures
                },
                'deployment_checklist': deployment_checklist,
                'infrastructure_config': infrastructure_config,
                'monitoring_config': monitoring_config
            },
            metadata={
                'readiness_score': readiness_score,
                'checks_passed': sum(1 for c in all_checks.values() if c['passed']),
                'total_checks': len(all_checks)
            },
            errors=[] if success else [f"Critical failures: {', '.join(critical_failures)}"]
        )
    
    async def _check_environment_config(
        self,
        frontend: Dict[str, Any],
        backend: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check environment configuration"""
        
        issues = []
        
        # Check for .env.example
        backend_files = backend.get('code_files', {})
        if '.env.example' not in backend_files:
            issues.append("Missing .env.example file")
        
        # Check for environment variable validation
        has_env_validation = any(
            'process.env' in code or 'os.getenv' in code
            for code in backend_files.values()
        )
        
        if not has_env_validation:
            issues.append("No environment variable usage detected")
        
        passed = len(issues) == 0
        
        return {
            'passed': passed,
            'severity': 'high',
            'issues': issues,
            'recommendations': ['Add environment variable validation', 'Document all required env vars']
        }
    
    async def _check_database_readiness(self, backend: Dict[str, Any]) -> Dict[str, Any]:
        """Check database configuration and migrations"""
        
        issues = []
        
        migrations = backend.get('migrations', [])
        
        if not migrations:
            issues.append("No database migrations found")
        
        # Check for connection pooling
        backend_files = backend.get('code_files', {})
        has_pooling = any(
            'pool' in code.lower() or 'connection' in code.lower()
            for code in backend_files.values()
        )
        
        if not has_pooling:
            issues.append("No database connection pooling detected")
        
        passed = len(issues) == 0
        
        return {
            'passed': passed,
            'severity': 'critical',
            'issues': issues,
            'recommendations': ['Set up connection pooling', 'Test migrations in staging']
        }
    
    async def _check_api_health(self, backend: Dict[str, Any]) -> Dict[str, Any]:
        """Check for health check endpoints"""
        
        issues = []
        
        api_design = backend.get('api_design', {})
        endpoints = api_design.get('endpoints', [])
        
        # Check for health endpoint
        has_health = any(
            'health' in ep.get('path', '').lower()
            for ep in endpoints
        )
        
        if not has_health:
            issues.append("No health check endpoint found")
        
        # Check for readiness endpoint
        has_readiness = any(
            'ready' in ep.get('path', '').lower() or 'readiness' in ep.get('path', '').lower()
            for ep in endpoints
        )
        
        if not has_readiness:
            issues.append("No readiness check endpoint found")
        
        passed = len(issues) == 0
        
        return {
            'passed': passed,
            'severity': 'high',
            'issues': issues,
            'recommendations': ['Add /health endpoint', 'Add /ready endpoint for k8s']
        }
    
    async def _check_frontend_optimization(self, frontend: Dict[str, Any]) -> Dict[str, Any]:
        """Check frontend build optimization"""
        
        issues = []
        
        config = frontend.get('config', {})
        
        # Check for production build configuration
        # (In a real implementation, would check webpack/vite config)
        
        # Check for code splitting
        code_files = frontend.get('code_files', {})
        has_lazy_loading = any(
            'lazy' in code or 'Suspense' in code
            for code in code_files.values()
        )
        
        if not has_lazy_loading:
            issues.append("No code splitting or lazy loading detected")
        
        passed = len(issues) <= 1  # Allow some optimization issues
        
        return {
            'passed': passed,
            'severity': 'medium',
            'issues': issues,
            'recommendations': ['Enable code splitting', 'Optimize bundle size', 'Use lazy loading']
        }
    
    async def _check_security_config(
        self,
        backend: Dict[str, Any],
        security_report: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check security configuration"""
        
        issues = []
        
        # Check security report
        if security_report:
            security_score = security_report.get('score', 0)
            if security_score < 90:
                issues.append(f"Security score too low: {security_score}/100")
            
            critical_vulns = [
                v for v in security_report.get('vulnerabilities', [])
                if v.get('severity') == 'critical'
            ]
            
            if critical_vulns:
                issues.append(f"Critical vulnerabilities found: {len(critical_vulns)}")
        
        # Check for HTTPS configuration
        backend_files = backend.get('code_files', {})
        has_https_config = any(
            'https' in code.lower() or 'ssl' in code.lower()
            for code in backend_files.values()
        )
        
        passed = len(issues) == 0
        
        return {
            'passed': passed,
            'severity': 'critical',
            'issues': issues,
            'recommendations': ['Fix all critical vulnerabilities', 'Enable HTTPS', 'Set security headers']
        }
    
    async def _check_monitoring(self, backend: Dict[str, Any]) -> Dict[str, Any]:
        """Check monitoring and logging setup"""
        
        issues = []
        
        backend_files = backend.get('code_files', {})
        
        # Check for logging
        has_logging = any(
            'logger' in code.lower() or 'console.log' in code
            for code in backend_files.values()
        )
        
        if not has_logging:
            issues.append("No logging implementation found")
        
        # Check for error tracking (Sentry, etc.)
        has_error_tracking = any(
            'sentry' in code.lower() or 'errorHandler' in code
            for code in backend_files.values()
        )
        
        if not has_error_tracking:
            issues.append("No error tracking service configured")
        
        passed = has_logging  # Logging is minimum requirement
        
        return {
            'passed': passed,
            'severity': 'high',
            'issues': issues,
            'recommendations': ['Set up structured logging', 'Configure error tracking (Sentry)', 'Add APM monitoring']
        }
    
    async def _check_backup_strategy(self, backend: Dict[str, Any]) -> Dict[str, Any]:
        """Check backup and recovery strategy"""
        
        issues = []
        
        # Check for database backup configuration
        # (In a real implementation, would check for backup scripts or config)
        
        issues.append("Backup strategy not configured")
        
        passed = False  # Requires manual configuration
        
        return {
            'passed': passed,
            'severity': 'high',
            'issues': issues,
            'recommendations': [
                'Set up automated database backups',
                'Test restore procedures',
                'Configure point-in-time recovery'
            ]
        }
    
    async def _check_performance(
        self,
        frontend: Dict[str, Any],
        backend: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check performance readiness"""
        
        issues = []
        
        # Check for caching
        backend_files = backend.get('code_files', {})
        has_caching = any(
            'cache' in code.lower() or 'redis' in code.lower()
            for code in backend_files.values()
        )
        
        if not has_caching:
            issues.append("No caching strategy implemented")
        
        # Check for rate limiting
        has_rate_limiting = any(
            'rateLimit' in code or 'rate-limit' in code
            for code in backend_files.values()
        )
        
        if not has_rate_limiting:
            issues.append("No rate limiting configured")
        
        passed = len(issues) <= 1
        
        return {
            'passed': passed,
            'severity': 'medium',
            'issues': issues,
            'recommendations': ['Implement caching (Redis)', 'Add rate limiting', 'Set up CDN']
        }
    
    def _calculate_readiness_score(self, checks: Dict[str, Dict[str, Any]]) -> float:
        """Calculate overall readiness score"""
        
        weights = {
            'environment': 1.0,
            'database': 2.0,
            'api_health': 1.5,
            'frontend_optimization': 1.0,
            'security': 3.0,
            'monitoring': 1.5,
            'backup': 1.5,
            'performance': 1.0
        }
        
        total_weight = sum(weights.values())
        weighted_score = 0
        
        for name, check in checks.items():
            if check['passed']:
                weighted_score += weights.get(name, 1.0)
        
        score = (weighted_score / total_weight) * 100
        
        return round(score, 1)
    
    def _generate_deployment_checklist(self, checks: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate deployment checklist"""
        
        checklist = []
        
        # Pre-deployment
        checklist.append({
            'phase': 'Pre-Deployment',
            'tasks': [
                {'task': 'Run all tests', 'status': 'required'},
                {'task': 'Security audit passed', 'status': 'required'},
                {'task': 'Database migrations tested', 'status': 'required'},
                {'task': 'Environment variables configured', 'status': 'required'}
            ]
        })
        
        # Deployment
        checklist.append({
            'phase': 'Deployment',
            'tasks': [
                {'task': 'Build production bundle', 'status': 'required'},
                {'task': 'Run database migrations', 'status': 'required'},
                {'task': 'Deploy backend services', 'status': 'required'},
                {'task': 'Deploy frontend assets to CDN', 'status': 'required'},
                {'task': 'Update DNS records', 'status': 'optional'}
            ]
        })
        
        # Post-deployment
        checklist.append({
            'phase': 'Post-Deployment',
            'tasks': [
                {'task': 'Verify health endpoints', 'status': 'required'},
                {'task': 'Run smoke tests', 'status': 'required'},
                {'task': 'Monitor error rates', 'status': 'required'},
                {'task': 'Check performance metrics', 'status': 'recommended'}
            ]
        })
        
        return checklist
    
    def _generate_infrastructure_config(
        self,
        frontend: Dict[str, Any],
        backend: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate infrastructure as code templates"""
        
        configs = {}
        
        # Docker Compose
        configs['docker-compose.yml'] = """version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=${DATABASE_URL}
      - JWT_SECRET=${JWT_SECRET}
    depends_on:
      - db
  
  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - db_data:/var/lib/postgresql/data

volumes:
  db_data:
"""
        
        # Kubernetes deployment (simplified)
        configs['k8s-deployment.yaml'] = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: your-registry/backend:latest
        ports:
        - containerPort: 3000
        env:
        - name: NODE_ENV
          value: production
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
        readinessProbe:
          httpGet:
            path: /ready
            port: 3000
"""
        
        return configs
    
    def _generate_monitoring_config(self, backend: Dict[str, Any]) -> Dict[str, Any]:
        """Generate monitoring configuration"""
        
        return {
            'metrics': [
                'http_requests_total',
                'http_request_duration_seconds',
                'database_connections_active',
                'error_rate'
            ],
            'alerts': [
                {
                    'name': 'HighErrorRate',
                    'condition': 'error_rate > 5%',
                    'severity': 'critical'
                },
                {
                    'name': 'HighResponseTime',
                    'condition': 'p95_latency > 1s',
                    'severity': 'warning'
                }
            ],
            'dashboards': [
                'Application Performance',
                'Database Metrics',
                'Error Tracking'
            ]
        }
    
    def _calculate_production_confidence(
        self,
        checks: Dict[str, Dict[str, Any]],
        readiness_score: float
    ) -> float:
        """Calculate confidence in production readiness"""
        
        critical_checks_passed = all(
            check['passed']
            for check in checks.values()
            if check['severity'] == 'critical'
        )
        
        criteria = {
            'high_readiness_score': readiness_score >= self.readiness_threshold,
            'critical_checks_passed': critical_checks_passed,
            'most_checks_passed': sum(1 for c in checks.values() if c['passed']) >= len(checks) * 0.75,
            'security_ready': checks.get('security', {}).get('passed', False),
            'database_ready': checks.get('database', {}).get('passed', False)
        }
        
        weights = {
            'high_readiness_score': 2.0,
            'critical_checks_passed': 3.0,
            'most_checks_passed': 1.5,
            'security_ready': 2.5,
            'database_ready': 2.0
        }
        
        base_confidence = self._calculate_confidence(criteria, weights)
        
        # Average with readiness score
        return (base_confidence + readiness_score) / 2


if __name__ == '__main__':
    from antigravity.llm.kimi_adapter import KimiAdapter
    
    adapter = KimiAdapter(api_key="MOCK_KEY")
    agent = ProductionReadinessAgent(llm_adapter=adapter)
    
    test_input = {
        'frontend_outputs': {'config': {'framework': 'react'}},
        'backend_outputs': {
            'code_files': {'src/server.js': 'app.listen(3000)'},
            'migrations': [{'name': 'create_users'}],
            'api_design': {'endpoints': [{'path': '/health', 'method': 'GET'}]}
        },
        'test_results': {'passed': True},
        'security_report': {'score': 95, 'vulnerabilities': []}
    }
    
    result = agent.execute_with_retry(test_input)
    
    print(f"\nSuccess: {result.success}")
    print(f"Readiness Score: {result.outputs['readiness_report']['score']}/100")
    print(f"Checks Passed: {result.metadata['checks_passed']}/{result.metadata['total_checks']}")
