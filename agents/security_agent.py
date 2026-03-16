"""
Security & Quality Agent

Performs security audits and code quality analysis.
"""

import json
from typing import Dict, List, Any, Tuple, Optional
from agents.base_agent import BaseAgent, AgentType, AgentResult


class SecurityAgent(BaseAgent):
    """
    Agent responsible for security and quality audits.
    
    Inputs:
        - code_files: All code files to audit
        - dependencies: Package dependencies
        - api_endpoints: API endpoint specifications
    
    Outputs:
        - security_report: Security vulnerabilities found
        - quality_report: Code quality issues
        - performance_analysis: Performance bottlenecks
        - recommendations: Fix recommendations
    """
    
    def __init__(self, llm_adapter: Any, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            agent_type=AgentType.SECURITY,
            llm_adapter=llm_adapter,
            config=config
        )
        
        self.security_threshold = self.config.get('security_threshold', 90)
        self.quality_threshold = self.config.get('quality_threshold', 80)
    
    def validate_inputs(self, inputs: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate input data"""
        errors = []
        
        if 'code_files' not in inputs:
            errors.append("Missing required field: 'code_files'")
        
        return len(errors) == 0, errors
    
    def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """
        Execute security and quality audit
        
        Args:
            inputs: Dict with code_files and optional dependencies
        
        Returns:
            AgentResult with security and quality reports
        """
        self.logger.info("Starting security and quality audit")
        
        code_files = inputs['code_files']
        dependencies = inputs.get('dependencies', {})
        api_endpoints = inputs.get('api_endpoints', [])
        
        # Step 1: Security audit
        self.logger.info("Performing security audit")
        security_report = self._security_audit(code_files, api_endpoints)
        
        # Step 2: Dependency vulnerability scan
        self.logger.info("Scanning dependencies")
        dependency_report = self._scan_dependencies(dependencies)
        
        # Step 3: Code quality analysis
        self.logger.info("Analyzing code quality")
        quality_report = self._quality_analysis(code_files)
        
        # Step 4: Performance analysis
        self.logger.info("Analyzing performance")
        performance_report = self._performance_analysis(code_files)
        
        # Step 5: Generate recommendations
        recommendations = self._generate_recommendations(
            security_report,
            dependency_report,
            quality_report,
            performance_report
        )
        
        # Calculate scores
        security_score = security_report['score']
        quality_score = quality_report['score']
        
        # Determine success (no critical vulnerabilities)
        has_critical = any(
            v['severity'] == 'critical'
            for v in security_report['vulnerabilities']
        )
        
        success = not has_critical and security_score >= self.security_threshold
        
        # Calculate confidence
        confidence = self._calculate_security_confidence(
            security_report,
            quality_report,
            performance_report
        )
        
        # Log decision
        self.log_decision(
            decision=f"Security score: {security_score}/100, Quality score: {quality_score}/100",
            reasoning=f"Found {len(security_report['vulnerabilities'])} security issues, "
                     f"{len(quality_report['issues'])} quality issues, "
                     f"{'BLOCKING' if has_critical else 'PASSING'}"
        )
        
        return AgentResult(
            success=success,
            confidence=confidence,
            outputs={
                'security_report': security_report,
                'dependency_report': dependency_report,
                'quality_report': quality_report,
                'performance_report': performance_report,
                'recommendations': recommendations
            },
            metadata={
                'security_score': security_score,
                'quality_score': quality_score,
                'critical_issues': len([v for v in security_report['vulnerabilities'] if v['severity'] == 'critical'])
            },
            errors=[] if success else [f"Critical security vulnerabilities found: {len([v for v in security_report['vulnerabilities'] if v['severity'] == 'critical'])}"]
        )
    
    def _security_audit(
        self,
        code_files: Dict[str, str],
        api_endpoints: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Perform OWASP Top 10 security audit"""
        
        vulnerabilities = []
        
        # Check 1: SQL Injection
        sql_injection_issues = self._check_sql_injection(code_files)
        vulnerabilities.extend(sql_injection_issues)
        
        # Check 2: XSS (Cross-Site Scripting)
        xss_issues = self._check_xss(code_files)
        vulnerabilities.extend(xss_issues)
        
        # Check 3: CSRF
        csrf_issues = self._check_csrf(code_files, api_endpoints)
        vulnerabilities.extend(csrf_issues)
        
        # Check 4: Broken Authentication
        auth_issues = self._check_authentication(code_files)
        vulnerabilities.extend(auth_issues)
        
        # Check 5: Sensitive Data Exposure
        data_exposure_issues = self._check_data_exposure(code_files)
        vulnerabilities.extend(data_exposure_issues)
        
        # Check 6: Security Misconfiguration
        config_issues = self._check_security_config(code_files)
        vulnerabilities.extend(config_issues)
        
        # Calculate security score
        total_checks = 10
        critical_count = len([v for v in vulnerabilities if v['severity'] == 'critical'])
        high_count = len([v for v in vulnerabilities if v['severity'] == 'high'])
        
        # Deduct points for issues
        score = 100 - (critical_count * 20) - (high_count * 10)
        score = max(0, score)
        
        return {
            'score': score,
            'vulnerabilities': vulnerabilities,
            'owasp_checks': total_checks
        }
    
    def _check_sql_injection(self, code_files: Dict[str, str]) -> List[Dict[str, Any]]:
        """Check for SQL injection vulnerabilities"""
        issues = []
        
        for filepath, code in code_files.items():
            # Look for raw SQL queries
            if 'query(' in code and '${' in code:
                issues.append({
                    'type': 'SQL Injection',
                    'severity': 'critical',
                    'file': filepath,
                    'description': 'Potential SQL injection - using string interpolation in queries',
                    'recommendation': 'Use parameterized queries or ORM'
                })
            
            # Check for unsafe query construction
            if '.query(' in code and '+' in code:
                issues.append({
                    'type': 'SQL Injection',
                    'severity': 'high',
                    'file': filepath,
                    'description': 'Unsafe SQL query construction',
                    'recommendation': 'Use parameterized queries'
                })
        
        return issues
    
    def _check_xss(self, code_files: Dict[str, str]) -> List[Dict[str, Any]]:
        """Check for XSS vulnerabilities"""
        issues = []
        
        for filepath, code in code_files.items():
            # Check for dangerouslySetInnerHTML
            if 'dangerouslySetInnerHTML' in code:
                issues.append({
                    'type': 'XSS',
                    'severity': 'high',
                    'file': filepath,
                    'description': 'Using dangerouslySetInnerHTML without sanitization',
                    'recommendation': 'Sanitize HTML with DOMPurify before rendering'
                })
            
            # Check for eval()
            if 'eval(' in code:
                issues.append({
                    'type': 'XSS',
                    'severity': 'critical',
                    'file': filepath,
                    'description': 'Using eval() with user input',
                    'recommendation': 'Never use eval() - find alternative approach'
                })
        
        return issues
    
    def _check_csrf(
        self,
        code_files: Dict[str, str],
        api_endpoints: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Check for CSRF protection"""
        issues = []
        
        # Check if CSRF middleware is present
        has_csrf_middleware = any(
            'csrf' in code.lower()
            for code in code_files.values()
        )
        
        if not has_csrf_middleware:
            # Check if there are state-changing endpoints
            state_changing = [
                ep for ep in api_endpoints
                if ep.get('method') in ['POST', 'PUT', 'DELETE']
            ]
            
            if state_changing:
                issues.append({
                    'type': 'CSRF',
                    'severity': 'high',
                    'file': 'server configuration',
                    'description': 'No CSRF protection found for state-changing endpoints',
                    'recommendation': 'Implement CSRF token validation'
                })
        
        return issues
    
    def _check_authentication(self, code_files: Dict[str, str]) -> List[Dict[str, Any]]:
        """Check authentication implementation"""
        issues = []
        
        for filepath, code in code_files.items():
            # Check for hardcoded secrets
            if 'secret' in code.lower() and ('=' in code or ':' in code):
                if not 'process.env' in code and not 'os.getenv' in code:
                    issues.append({
                        'type': 'Broken Authentication',
                        'severity': 'critical',
                        'file': filepath,
                        'description': 'Hardcoded secret or API key',
                        'recommendation': 'Use environment variables for secrets'
                    })
            
            # Check for weak password hashing
            if 'md5' in code.lower() or 'sha1' in code.lower():
                issues.append({
                    'type': 'Broken Authentication',
                    'severity': 'high',
                    'file': filepath,
                    'description': 'Weak password hashing algorithm',
                    'recommendation': 'Use bcrypt or argon2 for password hashing'
                })
        
        return issues
    
    def _check_data_exposure(self, code_files: Dict[str, str]) -> List[Dict[str, Any]]:
        """Check for sensitive data exposure"""
        issues = []
        
        for filepath, code in code_files.items():
            # Check for logging sensitive data
            if 'console.log' in code and ('password' in code.lower() or 'token' in code.lower()):
                issues.append({
                    'type': 'Sensitive Data Exposure',
                    'severity': 'medium',
                    'file': filepath,
                    'description': 'Potentially logging sensitive data',
                    'recommendation': 'Remove or mask sensitive data in logs'
                })
        
        return issues
    
    def _check_security_config(self, code_files: Dict[str, str]) -> List[Dict[str, Any]]:
        """Check security configuration"""
        issues = []
        
        # Check for security headers
        has_helmet = any('helmet' in code for code in code_files.values())
        
        if not has_helmet:
            issues.append({
                'type': 'Security Misconfiguration',
                'severity': 'medium',
                'file': 'server configuration',
                'description': 'Missing security headers middleware',
                'recommendation': 'Use helmet.js to set security headers'
            })
        
        return issues
    
    def _scan_dependencies(self, dependencies: Dict[str, Any]) -> Dict[str, Any]:
        """Scan dependencies for known vulnerabilities"""
        
        # In a real implementation, this would use npm audit or similar
        # For now, we'll simulate results
        
        vulnerabilities = []
        
        # Simulate finding a vulnerability
        if 'dependencies' in dependencies:
            deps = dependencies['dependencies']
            if 'express' in deps:
                # Simulate outdated version
                vulnerabilities.append({
                    'package': 'express',
                    'severity': 'low',
                    'description': 'Outdated version',
                    'recommendation': 'Update to latest version'
                })
        
        return {
            'vulnerabilities': vulnerabilities,
            'total_dependencies': len(dependencies.get('dependencies', {})),
            'vulnerable_count': len(vulnerabilities)
        }
    
    def _quality_analysis(self, code_files: Dict[str, str]) -> Dict[str, Any]:
        """Analyze code quality"""
        
        issues = []
        
        for filepath, code in code_files.items():
            # Check for code smells
            
            # Long functions (> 50 lines)
            lines = code.split('\n')
            if len(lines) > 50:
                issues.append({
                    'type': 'Code Smell',
                    'severity': 'low',
                    'file': filepath,
                    'description': 'Function is too long',
                    'recommendation': 'Break into smaller functions'
                })
            
            # Duplicate code
            # (Simplified check)
            
            # Missing error handling
            if 'try' not in code and ('fetch' in code or 'await' in code):
                issues.append({
                    'type': 'Error Handling',
                    'severity': 'medium',
                    'file': filepath,
                    'description': 'Missing error handling for async operations',
                    'recommendation': 'Add try-catch blocks'
                })
        
        # Calculate quality score
        score = 100 - (len(issues) * 5)
        score = max(0, score)
        
        return {
            'score': score,
            'issues': issues,
            'code_smells': len([i for i in issues if i['type'] == 'Code Smell'])
        }
    
    def _performance_analysis(self, code_files: Dict[str, str]) -> Dict[str, Any]:
        """Analyze performance"""
        
        bottlenecks = []
        
        for filepath, code in code_files.items():
            # Check for N+1 queries
            if code.count('.map(') > 0 and code.count('await') > code.count('.map('):
                bottlenecks.append({
                    'type': 'N+1 Query',
                    'file': filepath,
                    'description': 'Potential N+1 query in loop',
                    'recommendation': 'Batch database queries'
                })
            
            # Check for large bundle size indicators
            if code.count('import') > 20:
                bottlenecks.append({
                    'type': 'Bundle Size',
                    'file': filepath,
                    'description': 'Many imports may increase bundle size',
                    'recommendation': 'Use code splitting and lazy loading'
                })
        
        score = 100 - (len(bottlenecks) * 10)
        score = max(0, score)
        
        return {
            'score': score,
            'bottlenecks': bottlenecks
        }
    
    def _generate_recommendations(
        self,
        security_report: Dict[str, Any],
        dependency_report: Dict[str, Any],
        quality_report: Dict[str, Any],
        performance_report: Dict[str, Any]
    ) -> List[str]:
        """Generate fix recommendations"""
        
        recommendations = []
        
        # Security recommendations
        for vuln in security_report['vulnerabilities']:
            if vuln['severity'] in ['critical', 'high']:
                recommendations.append(f"🔴 {vuln['type']}: {vuln['recommendation']}")
        
        # Dependency recommendations
        if dependency_report['vulnerable_count'] > 0:
            recommendations.append(f"⚠️ Update {dependency_report['vulnerable_count']} vulnerable dependencies")
        
        # Quality recommendations
        if quality_report['score'] < 80:
            recommendations.append(f"📊 Improve code quality (current score: {quality_report['score']})")
        
        # Performance recommendations
        if performance_report['score'] < 80:
            recommendations.append(f"⚡ Address performance bottlenecks")
        
        return recommendations
    
    def _calculate_security_confidence(
        self,
        security_report: Dict[str, Any],
        quality_report: Dict[str, Any],
        performance_report: Dict[str, Any]
    ) -> float:
        """Calculate confidence in security audit"""
        
        criteria = {
            'high_security_score': security_report['score'] >= self.security_threshold,
            'no_critical_vulns': len([v for v in security_report['vulnerabilities'] if v['severity'] == 'critical']) == 0,
            'good_quality': quality_report['score'] >= self.quality_threshold,
            'good_performance': performance_report['score'] >= 80,
            'few_dependencies_vulns': len(security_report.get('vulnerabilities', [])) < 5
        }
        
        weights = {
            'high_security_score': 3.0,
            'no_critical_vulns': 3.0,
            'good_quality': 1.5,
            'good_performance': 1.0,
            'few_dependencies_vulns': 1.0
        }
        
        base_confidence = self._calculate_confidence(criteria, weights)
        
        # Average with actual scores
        avg_score = (security_report['score'] + quality_report['score'] + performance_report['score']) / 3
        
        return (base_confidence + avg_score) / 2


if __name__ == '__main__':
    from antigravity.llm.kimi_adapter import KimiAdapter
    
    adapter = KimiAdapter(api_key="MOCK_KEY")
    agent = SecurityAgent(llm_adapter=adapter)
    
    test_input = {
        'code_files': {
            'src/server.js': 'const query = `SELECT * FROM users WHERE id = ${userId}`;',
            'src/App.jsx': '<div dangerouslySetInnerHTML={{__html: userInput}} />'
        },
        'dependencies': {
            'dependencies': {
                'express': '^4.17.0'
            }
        },
        'api_endpoints': [
            {'method': 'POST', 'path': '/api/users'}
        ]
    }
    
    result = agent.execute_with_retry(test_input)
    
    print(f"\nSuccess: {result.success}")
    print(f"Security Score: {result.outputs['security_report']['score']}/100")
    print(f"Vulnerabilities: {len(result.outputs['security_report']['vulnerabilities'])}")
