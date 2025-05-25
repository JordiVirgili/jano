# Configuration Fixer Plugin Development Guide

## Overview

This document outlines the implementation requirements and development process for creating configuration fixer plugins within the Argos subsystem. These plugins perform automated security configuration analysis and remediation for various services.

## Architecture

### Abstract Base Class

All fixer plugins must inherit from `ConfigFixerPlugin` defined in `argos/core/plugins.py`:

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple

class ConfigFixerPlugin(ABC):
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize plugin with configuration parameters."""
        
    @abstractmethod
    def analyze_configuration(self, file_path: str) -> Dict[str, Any]:
        """
        Parse and analyze configuration file for security issues.
        
        Returns:
            {
                "success": bool,
                "file_path": str,
                "issues": List[Dict],
                "message": str
            }
        """
        
    @abstractmethod
    def apply_fixes(self, file_path: str, fixes: List[Dict[str, Any]], backup: bool = True) -> Tuple[bool, str]:
        """Apply configuration fixes with optional backup creation."""
        
    @abstractmethod
    def restart_service(self, service_name: str) -> Tuple[bool, str]:
        """Handle service restart after configuration changes."""
        
    @abstractmethod
    def get_supported_services(self) -> List[str]:
        """Return list of service identifiers handled by this plugin."""
```

### Plugin Discovery

The `FixerPluginManager` (`argos/core/fixer_plugin_manager.py`) handles:
- Dynamic module loading from `argos/plugins/fixers/`
- Class registration and instantiation
- Service-to-plugin mapping resolution
- Instance caching and lifecycle management

## Implementation Patterns

### 1. Configuration Analysis Pattern

Most plugins follow this analysis pattern:

```python
def analyze_configuration(self, file_path: str = None) -> Dict[str, Any]:
    # 1. File location resolution
    if not file_path:
        file_path = self._find_config_file()
        if not file_path:
            return {"success": False, "message": "Config file not found", "issues": []}
    
    # 2. File parsing and content extraction
    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except Exception as e:
        return {"success": False, "message": f"Read error: {str(e)}", "issues": []}
    
    # 3. Rule-based issue detection
    issues = []
    for rule_id, rule_config in self.security_rules.items():
        pattern = rule_config["pattern"]
        matches = re.findall(pattern, content, re.MULTILINE)
        
        if not matches and rule_config.get("required", False):
            issues.append({
                "id": rule_id,
                "description": rule_config["description"],
                "severity": rule_config["severity"],
                "issue_type": "missing",
                "fix": rule_config["replacement"]
            })
        elif matches:
            # Validate existing configuration
            current_value = matches[0] if matches else None
            if current_value != rule_config["expected_value"]:
                issues.append({
                    "id": rule_id,
                    "description": rule_config["description"],
                    "severity": rule_config["severity"],
                    "issue_type": "incorrect",
                    "current": current_value,
                    "fix": rule_config["replacement"]
                })
    
    return {
        "success": True,
        "file_path": file_path,
        "issues": issues,
        "message": f"Analysis complete: {len(issues)} issues found"
    }
```

### 2. Rule Definition Structure

Define security rules as class attributes:

```python
def __init__(self):
    self.security_rules = {
        "rule_identifier": {
            "pattern": r"regex_pattern_for_detection",
            "replacement": "secure_configuration_line",
            "description": "Human-readable issue description",
            "severity": "high|medium|low",
            "required": True,  # Must be present in config
            "add_location": "specific_block_type"  # For structured configs
        }
    }
```

### 3. Fix Application Strategy

Implement fixes using pattern matching and content modification:

```python
def apply_fixes(self, file_path: str = None, fixes: List[Dict[str, Any]] = None, backup: bool = True) -> Tuple[bool, str]:
    # File resolution and backup creation
    if backup:
        backup_path = f"{file_path}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
        shutil.copyfile(file_path, backup_path)
    
    # Content modification
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    applied_fixes = []
    for fix in fixes:
        fix_id = fix.get("id")
        issue_type = fix.get("issue_type")
        
        if issue_type == "missing":
            # Append new configuration
            lines.append(f"{fix['fix']}\n")
            applied_fixes.append(f"Added: {fix['fix']}")
            
        elif issue_type == "incorrect":
            # Replace existing configuration
            pattern = self.security_rules[fix_id]["pattern"]
            for i, line in enumerate(lines):
                if re.match(pattern, line):
                    lines[i] = f"{fix['fix']}\n"
                    applied_fixes.append(f"Modified: {line.strip()} -> {fix['fix']}")
                    break
    
    # Write modified content
    with open(file_path, 'w') as f:
        f.writelines(lines)
    
    return True, f"Applied {len(applied_fixes)} fixes"
```

## Implementation Example

Here's a complete implementation for Apache HTTP Server:

```python
# argos/plugins/fixers/apache_config_fixer.py
import os
import re
import shutil
import subprocess
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from argos.core.plugins import ConfigFixerPlugin

class ApacheConfigFixer(ConfigFixerPlugin):
    def __init__(self):
        self.config_paths = [
            "/etc/apache2/apache2.conf",
            "/etc/httpd/conf/httpd.conf",
            "/usr/local/apache2/conf/httpd.conf"
        ]
        
        self.security_rules = {
            "server_tokens": {
                "pattern": r"^\s*ServerTokens\s+(\w+)",
                "replacement": "ServerTokens Prod",
                "description": "Hide detailed server information",
                "severity": "medium",
                "required": True
            },
            "server_signature": {
                "pattern": r"^\s*ServerSignature\s+(\w+)",
                "replacement": "ServerSignature Off",
                "description": "Disable server signature in error pages",
                "severity": "medium",
                "required": True
            },
            "directory_browsing": {
                "pattern": r"^\s*Options\s+.*Indexes",
                "replacement": "Options -Indexes",
                "description": "Disable directory browsing",
                "severity": "high",
                "required": False
            }
        }

    def initialize(self, config: Dict[str, Any]) -> None:
        custom_path = config.get("apache_config_path")
        if custom_path and os.path.exists(custom_path):
            self.config_paths.insert(0, custom_path)

    def _find_config_file(self) -> Optional[str]:
        for path in self.config_paths:
            if os.path.isfile(path):
                return path
        return None

    def analyze_configuration(self, file_path: str = None) -> Dict[str, Any]:
        if not file_path:
            file_path = self._find_config_file()
            if not file_path:
                return {
                    "success": False,
                    "message": "Apache configuration file not found",
                    "issues": []
                }

        try:
            with open(file_path, 'r') as f:
                content = f.read()
        except IOError as e:
            return {
                "success": False,
                "message": f"Failed to read config file: {str(e)}",
                "issues": []
            }

        issues = []
        for rule_id, rule_config in self.security_rules.items():
            pattern = rule_config["pattern"]
            matches = re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)
            
            if not matches and rule_config.get("required", False):
                issues.append({
                    "id": rule_id,
                    "description": rule_config["description"],
                    "severity": rule_config["severity"],
                    "issue_type": "missing",
                    "fix": rule_config["replacement"]
                })
            elif matches:
                current_setting = matches[0]
                expected_pattern = rule_config["replacement"].split()[-1]
                if current_setting != expected_pattern:
                    issues.append({
                        "id": rule_id,
                        "description": rule_config["description"],
                        "severity": rule_config["severity"],
                        "issue_type": "incorrect",
                        "current": f"{rule_config['replacement'].split()[0]} {current_setting}",
                        "fix": rule_config["replacement"]
                    })

        return {
            "success": True,
            "file_path": file_path,
            "issues": issues,
            "message": f"Found {len(issues)} security issues"
        }

    def apply_fixes(self, file_path: str = None, fixes: List[Dict[str, Any]] = None, backup: bool = True) -> Tuple[bool, str]:
        if not file_path:
            file_path = self._find_config_file()
            if not file_path:
                return False, "Configuration file not found"

        if fixes is None:
            analysis_result = self.analyze_configuration(file_path)
            if not analysis_result["success"]:
                return False, analysis_result["message"]
            fixes = analysis_result["issues"]

        try:
            # Create backup
            if backup:
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                backup_path = f"{file_path}.bak.{timestamp}"
                shutil.copyfile(file_path, backup_path)

            # Read current configuration
            with open(file_path, 'r') as f:
                lines = f.readlines()

            applied_fixes = []
            for fix in fixes:
                fix_id = fix.get("id")
                issue_type = fix.get("issue_type")
                
                if fix_id not in self.security_rules:
                    continue

                rule = self.security_rules[fix_id]
                pattern = rule["pattern"]
                replacement = fix.get("fix", rule["replacement"])

                if issue_type == "missing":
                    lines.append(f"{replacement}\n")
                    applied_fixes.append(f"Added: {replacement}")
                    
                elif issue_type == "incorrect":
                    for i, line in enumerate(lines):
                        if re.match(pattern, line, re.IGNORECASE):
                            lines[i] = f"{replacement}\n"
                            applied_fixes.append(f"Modified line {i+1}: {replacement}")
                            break

            # Write updated configuration
            with open(file_path, 'w') as f:
                f.writelines(lines)

            return True, f"Successfully applied {len(applied_fixes)} fixes:\n" + "\n".join(applied_fixes)

        except Exception as e:
            return False, f"Error applying fixes: {str(e)}"

    def restart_service(self, service_name: str = "apache2") -> Tuple[bool, str]:
        # Test configuration before restart
        try:
            test_cmd = ["apache2ctl", "configtest"] if service_name == "apache2" else ["httpd", "-t"]
            result = subprocess.run(test_cmd, capture_output=True, text=True, check=False)
            if result.returncode != 0:
                return False, f"Configuration test failed: {result.stderr}"
        except FileNotFoundError:
            pass  # Skip test if command not available

        # Attempt service restart
        restart_commands = [
            ["systemctl", "restart", service_name],
            ["service", service_name, "restart"],
            ["apache2ctl", "restart"] if service_name == "apache2" else ["httpd", "-k", "restart"]
        ]

        for cmd in restart_commands:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                return True, f"Service {service_name} restarted successfully"
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue

        return False, f"Failed to restart {service_name}. Manual restart required."

    def get_supported_services(self) -> List[str]:
        return ["apache2", "httpd", "apache"]
```

## Integration Requirements

### 1. Plugin Registration

Add your plugin to the imports in `argos/plugins/fixers/__init__.py`:

```python
from .ssh_config_fixer import *
from .nginx_config_fixer import *
from .apache_config_fixer import *  # Add this line
```

### 2. Service Configuration

The plugin will be automatically discovered and mapped to services based on the return value of `get_supported_services()`.

### 3. API Integration

Your plugin integrates with these API endpoints:
- `POST /api/v1/argos/fix/analyze` - Calls `analyze_configuration()`
- `POST /api/v1/argos/fix/apply` - Calls `apply_fixes()`
- `POST /api/v1/argos/fix/auto` - Calls both methods sequentially


## Performance Considerations

- Cache compiled regex patterns as class attributes
- Use efficient file I/O operations
- Minimize subprocess calls during analysis
- Implement lazy loading for large configuration files

## Security Guidelines

- Validate all file paths to prevent directory traversal
- Use absolute paths for system commands
- Sanitize user inputs in configuration validation
- Implement proper file permission checks before modification
- Create backups before any file modification
