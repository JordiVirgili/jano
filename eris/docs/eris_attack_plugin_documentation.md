# Eris Attack Plugin Development Guide

## System Architecture

Attack plugins in Eris implement adversarial security testing through the `AttackPlugin` abstract base class. The plugin system provides standardized vulnerability assessment capabilities with configurable attack vectors and result reporting mechanisms.

## Base Interface Implementation

### AttackPlugin Abstract Class

All attack plugins inherit from `AttackPlugin` defined in `eris/core/plugins.py`:

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class AttackPlugin(ABC):
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize plugin with attack configuration parameters."""
        
    @abstractmethod
    def execute_attack(self, target: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute attack against specified target.
        
        Args:
            target: Target identifier (hostname, IP, service name)
            options: Attack-specific configuration parameters
            
        Returns:
            {
                "success": bool,
                "details": str,
                "severity": str,  # low, medium, high, critical
                "recommendations": List[str],
                "details_extended": Dict[str, Any]  # Optional additional data
            }
        """
        
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return list of attack capability identifiers."""
```

### Plugin Discovery

The `PluginManager` (`eris/core/plugin_manager.py`) implements:
- Dynamic module scanning in `eris/plugins/`
- Class registration and instantiation caching
- Capability-based plugin selection
- Configuration injection and lifecycle management

## Attack Implementation Patterns

### 1. Network Service Attack Pattern

Standard pattern for service-based attacks:

```python
class ServiceAttackPlugin(AttackPlugin):
    def __init__(self):
        self.timeout = 5
        self.max_attempts = 10
        self.delay_between_attempts = 1
        
    def _check_service_availability(self, host: str, port: int) -> bool:
        """Verify target service is accessible."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def execute_attack(self, target: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        options = options or {}
        port = options.get("port", self.default_port)
        
        # 1. Service availability check
        if not self._check_service_availability(target, port):
            return {
                "success": False,
                "details": f"Service on {target}:{port} is not accessible",
                "severity": "info",
                "recommendations": ["Verify service is running and accessible"]
            }
        
        # 2. Attack execution
        attack_results = self._perform_attack_sequence(target, port, options)
        
        # 3. Result analysis and reporting
        return self._analyze_and_report(attack_results, target, port)
```

### 2. Configuration-Based Attack Pattern

For attacks targeting configuration weaknesses:

```python
def execute_attack(self, target: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    # Parse target configuration
    config_analysis = self._analyze_target_configuration(target, options)
    
    # Identify attack vectors based on configuration
    attack_vectors = self._identify_attack_vectors(config_analysis)
    
    # Execute applicable attacks
    results = []
    for vector in attack_vectors:
        result = self._execute_attack_vector(vector, target, options)
        results.append(result)
    
    # Aggregate and prioritize findings
    return self._aggregate_results(results, target)
```

## Implementation Examples

### Web Application Attack Plugin

```python
# eris/plugins/web_vulnerability_scanner.py
import requests
import re
from urllib.parse import urljoin, urlparse
from typing import Dict, Any, List, Optional
from eris.core.plugins import AttackPlugin

class WebVulnerabilityPlugin(AttackPlugin):
    def __init__(self):
        self.timeout = 10
        self.user_agent = "Eris-Security-Scanner/1.0"
        
        # Common vulnerability payloads
        self.xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>"
        ]
        
        self.sql_payloads = [
            "' OR '1'='1",
            "' UNION SELECT NULL--",
            "'; DROP TABLE users--"
        ]

    def initialize(self, config: Dict[str, Any]) -> None:
        self.timeout = config.get("timeout", self.timeout)
        self.user_agent = config.get("user_agent", self.user_agent)

    def _test_xss_vulnerability(self, url: str) -> Dict[str, Any]:
        vulnerabilities = []
        
        for payload in self.xss_payloads:
            try:
                # Test GET parameter injection
                test_url = f"{url}?test={payload}"
                response = requests.get(
                    test_url,
                    timeout=self.timeout,
                    headers={"User-Agent": self.user_agent}
                )
                
                if payload in response.text:
                    vulnerabilities.append({
                        "type": "reflected_xss",
                        "location": "GET parameter",
                        "payload": payload,
                        "evidence": response.text[:200]
                    })
                    
            except requests.RequestException:
                continue
                
        return {"xss_vulnerabilities": vulnerabilities}

    def _test_sql_injection(self, url: str) -> Dict[str, Any]:
        vulnerabilities = []
        
        for payload in self.sql_payloads:
            try:
                test_url = f"{url}?id={payload}"
                response = requests.get(
                    test_url,
                    timeout=self.timeout,
                    headers={"User-Agent": self.user_agent}
                )
                
                # Check for SQL error indicators
                sql_errors = [
                    "SQL syntax error",
                    "mysql_fetch_array",
                    "ORA-[0-9]{4,5}",
                    "Microsoft OLE DB Provider"
                ]
                
                for error_pattern in sql_errors:
                    if re.search(error_pattern, response.text, re.IGNORECASE):
                        vulnerabilities.append({
                            "type": "sql_injection",
                            "location": "GET parameter",
                            "payload": payload,
                            "error_pattern": error_pattern,
                            "evidence": response.text[:200]
                        })
                        break
                        
            except requests.RequestException:
                continue
                
        return {"sql_vulnerabilities": vulnerabilities}

    def _check_security_headers(self, url: str) -> Dict[str, Any]:
        try:
            response = requests.get(
                url,
                timeout=self.timeout,
                headers={"User-Agent": self.user_agent}
            )
            
            missing_headers = []
            security_headers = {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": ["DENY", "SAMEORIGIN"],
                "X-XSS-Protection": "1; mode=block",
                "Strict-Transport-Security": None,
                "Content-Security-Policy": None
            }
            
            for header, expected_values in security_headers.items():
                if header not in response.headers:
                    missing_headers.append({
                        "header": header,
                        "recommendation": f"Add {header} header for security"
                    })
                elif expected_values and response.headers[header] not in expected_values:
                    missing_headers.append({
                        "header": header,
                        "current_value": response.headers[header],
                        "recommended_values": expected_values
                    })
            
            return {"missing_security_headers": missing_headers}
            
        except requests.RequestException as e:
            return {"error": f"Failed to check security headers: {str(e)}"}

    def execute_attack(self, target: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # Ensure target is a valid URL
        if not target.startswith(('http://', 'https://')):
            target = f"http://{target}"
        
        try:
            # Verify target is accessible
            response = requests.get(target, timeout=self.timeout)
            if response.status_code >= 400:
                return {
                    "success": False,
                    "details": f"Target {target} returned HTTP {response.status_code}",
                    "severity": "info",
                    "recommendations": ["Verify target URL is correct and accessible"]
                }
        except requests.RequestException as e:
            return {
                "success": False,
                "details": f"Cannot connect to {target}: {str(e)}",
                "severity": "info",
                "recommendations": ["Check network connectivity and target availability"]
            }

        # Execute vulnerability tests
        results = {}
        results.update(self._test_xss_vulnerability(target))
        results.update(self._test_sql_injection(target))
        results.update(self._check_security_headers(target))

        # Aggregate findings
        total_vulnerabilities = (
            len(results.get("xss_vulnerabilities", [])) +
            len(results.get("sql_vulnerabilities", [])) +
            len(results.get("missing_security_headers", []))
        )

        if total_vulnerabilities > 0:
            severity = "high" if any([
                results.get("xss_vulnerabilities"),
                results.get("sql_vulnerabilities")
            ]) else "medium"
            
            recommendations = [
                "Implement input validation and output encoding",
                "Use parameterized queries to prevent SQL injection",
                "Configure appropriate security headers",
                "Perform regular security assessments",
                "Implement Content Security Policy"
            ]
            
            return {
                "success": True,
                "details": f"Found {total_vulnerabilities} security issues on {target}",
                "severity": severity,
                "recommendations": recommendations,
                "details_extended": results
            }
        else:
            return {
                "success": False,
                "details": f"No obvious vulnerabilities found on {target}",
                "severity": "low",
                "recommendations": [
                    "Continue regular security monitoring",
                    "Consider more comprehensive vulnerability assessment",
                    "Implement security best practices as preventive measures"
                ],
                "details_extended": results
            }

    def get_capabilities(self) -> List[str]:
        return ["web_vulnerability_scan", "xss_detection", "sql_injection_test", "security_header_check"]
```

## Result Reporting Standards

### Standard Response Format

All plugins must return consistent result structures:

```python
{
    "success": bool,                    # Attack success indicator
    "details": str,                     # Human-readable description
    "severity": str,                    # "low" | "medium" | "high" | "critical"
    "recommendations": List[str],       # Remediation suggestions
    "details_extended": Dict[str, Any]  # Additional technical data
}
```

### Severity Classification

- **Critical**: Direct system compromise, credential theft, data access
- **High**: Service disruption, privilege escalation potential
- **Medium**: Information disclosure, configuration weaknesses
- **Low**: Minor issues, reconnaissance data

## Integration Mechanisms

### API Integration

Plugins integrate with Eris API endpoints in `eris/api/v1/eris.py`:

```python
@router.post("/attack/{plugin_name}")
def execute_attack(plugin_name: str, target: str, options: Optional[Dict[str, Any]] = None):
    # Plugin resolution and execution
    plugin = plugin_manager.get_plugin(plugin_name)
    result = plugin.execute_attack(target, options)
    
    # Database logging
    task = task_repo.create(db, {
        "task_to_perform": f"Security assessment using {plugin_name}",
        "user_prompt": f"Execute {plugin_name} attack against {target}"
    })
    
    return {
        "task_id": task.id,
        "plugin": plugin_name,
        "target": target,
        "result": result
    }
```

### Frontend Integration

Results are formatted for display in the Streamlit frontend via `format_attack_results()`:

```python
def format_attack_results(plugin_name: str, target: str, result: Dict[str, Any]) -> str:
    message = f"## Eris Security Test Results\n\n"
    message += f"**Plugin:** {plugin_name}\n"
    message += f"**Target:** {target}\n\n"
    
    if "success" in result:
        status = "✅ Successful" if result["success"] else "❌ Failed"
        message += f"**Status:** {status}\n"
    
    if "severity" in result:
        message += f"**Severity:** {result['severity'].upper()}\n"
    
    if "details" in result:
        message += f"\n### Details\n{result['details']}\n\n"
    
    # Format recommendations and extended details...
    
    return message
```

## Testing Framework

### Unit Testing Structure

```python
# tests/test_ssh_bruteforce.py
import unittest
from unittest.mock import patch, MagicMock
from eris.plugins.ssh_bruteforce import SSHBruteforcePlugin

class TestSSHBruteforcePlugin(unittest.TestCase):
    def setUp(self):
        self.plugin = SSHBruteforcePlugin()
        self.plugin.initialize({
            "usernames": ["test"],
            "passwords": ["weak"],
            "max_attempts": 2
        })
    
    @patch('socket.socket')
    def test_service_unavailable(self, mock_socket):
        mock_socket.return_value.connect_ex.return_value = 1
        
        result = self.plugin.execute_attack("192.168.1.1")
        
        self.assertFalse(result["success"])
        self.assertEqual(result["severity"], "info")
        self.assertIn("not accessible", result["details"])
    
    @patch('paramiko.SSHClient')
    @patch('socket.socket')
    def test_successful_attack(self, mock_socket, mock_ssh):
        # Mock successful connection
        mock_socket.return_value.connect_ex.return_value = 0
        mock_ssh.return_value.connect.return_value = None
        
        result = self.plugin.execute_attack("192.168.1.1")
        
        self.assertTrue(result["success"])
        self.assertEqual(result["severity"], "critical")
        self.assertIn("successful_credentials", result["details_extended"])
```

### Integration Testing

Test plugins against controlled vulnerable environments:

```python
def test_integration_ssh_attack():
    # Set up vulnerable SSH container
    container = setup_vulnerable_ssh_container()
    
    try:
        plugin = SSHBruteforcePlugin()
        plugin.initialize({"max_attempts": 5})
        
        result = plugin.execute_attack(container.ip_address)
        
        assert result["success"] == True
        assert result["severity"] == "critical"
        assert len(result["details_extended"]["successful_credentials"]) > 0
        
    finally:
        container.cleanup()
```

## Security and Ethical Considerations

### Responsible Disclosure

- Never execute attacks against unauthorized targets
- Implement rate limiting to prevent service disruption
- Log all attack attempts for audit purposes
- Provide clear remediation guidance

### Attack Limitations

```python
def execute_attack(self, target: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    # Validate target is not in prohibited ranges
    if self._is_prohibited_target(target):
        return {
            "success": False,
            "details": "Target is in prohibited range",
            "severity": "info",
            "recommendations": ["Use authorized test targets only"]
        }
    
    # Implement attack with appropriate safeguards
    return self._execute_safe_attack(target, options)
```

### Logging and Auditing

```python
import logging

class AttackPlugin(ABC):
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def execute_attack(self, target: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self.logger.info(f"Executing {self.__class__.__name__} against {target}")
        
        try:
            result = self._perform_attack(target, options)
            self.logger.info(f"Attack completed: {result['success']}")
            return result
        except Exception as e:
            self.logger.error(f"Attack failed with exception: {str(e)}")
            raise
```

## Performance Optimization

### Concurrent Execution

For plugins that test multiple vectors:

```python
import concurrent.futures
from typing import List, Callable

def _execute_concurrent_tests(self, test_functions: List[Callable], max_workers: int = 5) -> List[Dict]:
    results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_test = {executor.submit(test_func): test_func for test_func in test_functions}
        
        for future in concurrent.futures.as_completed(future_to_test):
            try:
                result = future.result(timeout=30)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Test failed: {str(e)}")
                results.append({"error": str(e)})
    
    return results
```

### Resource Management

```python
class NetworkAttackPlugin(AttackPlugin):
    def __init__(self):
        self.connection_pool = requests.Session()
        self.connection_pool.mount('http://', requests.adapters.HTTPAdapter(pool_maxsize=10))
        
    def __del__(self):
        if hasattr(self, 'connection_pool'):
            self.connection_pool.close()
```

## Plugin Registration

### Automatic Discovery

Place plugin files in `eris/plugins/` directory. The plugin manager will automatically discover and register classes inheriting from `AttackPlugin`.

### Manual Registration

Add to `eris/plugins/__init__.py`:

```python
from .weak_ssh import *
from .real_ssh import *
from .ssh_bruteforce import *     # Add new plugin
from .web_vulnerability_scanner import *
```

## Deployment Considerations

- Test plugins in isolated environments before production use
- Implement proper error handling for network timeouts and failures
- Consider target system impact and implement appropriate delays
- Document plugin requirements and dependencies
- Provide configuration examples and usage documentation