import os
import re
import shutil
import subprocess
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from argos.core.plugins import ConfigFixerPlugin

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NginxConfigFixer(ConfigFixerPlugin):
    """Plugin for automatically fixing Nginx server configurations."""

    def __init__(self):
        """Initialize the Nginx Config Fixer plugin."""
        self.common_nginx_paths = ["/etc/nginx/nginx.conf", "/etc/nginx/conf.d/default.conf",
            "/usr/local/nginx/conf/nginx.conf", "/usr/local/etc/nginx/nginx.conf", "C:\\nginx\\conf\\nginx.conf"]
        self.backup_suffix = f".bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Common security fixes and their patterns
        self.security_fixes = {
            "server_tokens": {"pattern": r"^\s*server_tokens\s+(on|off);", "replacement": "server_tokens off;",
                "add_if_missing": True, "add_location": "http",  # Add to http block if missing
                "description": "Hide Nginx version in headers", "severity": "medium"},
            "x_frame_options": {"pattern": r"^\s*add_header\s+X-Frame-Options\s+.*;",
                "replacement": "add_header X-Frame-Options SAMEORIGIN;", "add_if_missing": True,
                "add_location": "server",  # Add to server block if missing
                "description": "Set X-Frame-Options header to prevent clickjacking", "severity": "medium"},
            "x_content_type_options": {"pattern": r"^\s*add_header\s+X-Content-Type-Options\s+.*;",
                "replacement": "add_header X-Content-Type-Options nosniff;", "add_if_missing": True,
                "add_location": "server",  # Add to server block if missing
                "description": "Set X-Content-Type-Options header to prevent MIME sniffing", "severity": "medium"},
            "strict_transport_security": {"pattern": r"^\s*add_header\s+Strict-Transport-Security\s+.*;",
                "replacement": "add_header Strict-Transport-Security \"max-age=31536000; includeSubDomains\";",
                "add_if_missing": True, "add_location": "server",  # Add to server block if missing
                "description": "Enable HSTS to enforce HTTPS", "severity": "high"},
            "ssl_protocols": {"pattern": r"^\s*ssl_protocols\s+.*;", "replacement": "ssl_protocols TLSv1.2 TLSv1.3;",
                "add_if_missing": True, "add_location": "server",  # Add to server block if missing
                "description": "Use only secure SSL/TLS protocols", "severity": "high"},
            "ssl_ciphers": {"pattern": r"^\s*ssl_ciphers\s+.*;",
                "replacement": "ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384';",
                "add_if_missing": True, "add_location": "server",  # Add to server block if missing
                "description": "Use only secure ciphers", "severity": "high"},
            "ssl_prefer_server_ciphers": {"pattern": r"^\s*ssl_prefer_server_ciphers\s+.*;",
                "replacement": "ssl_prefer_server_ciphers on;", "add_if_missing": True, "add_location": "server",
                # Add to server block if missing
                "description": "Prefer server ciphers over client ciphers", "severity": "medium"}}

    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the plugin with the provided configuration."""
        if config.get("nginx_config_path"):
            self.common_nginx_paths.insert(0, config["nginx_config_path"])

    def _find_nginx_config(self) -> Optional[str]:
        """Find the Nginx configuration file."""
        for path in self.common_nginx_paths:
            if os.path.isfile(path):
                return path
        return None

    def _identify_block_positions(self, content: List[str]) -> Dict[str, List[Tuple[int, int]]]:
        """
        Identify positions of http, server, and location blocks in the configuration.

        Args:
            content: List of lines from the config file

        Returns:
            Dictionary mapping block types to lists of (start_line, end_line) tuples
        """
        blocks = {"http": [], "server": [], "location": []}

        # Stack to keep track of nested blocks
        stack = []

        for i, line in enumerate(content):
            # Check for block start
            for block_type in blocks.keys():
                if re.search(rf"\b{block_type}\b.*{{", line):
                    stack.append((block_type, i))
                    break

            # Check for block end
            if "}" in line and stack:
                block_type, start_line = stack.pop()
                blocks[block_type].append((start_line, i))

        return blocks

    def analyze_configuration(self, file_path: str = None) -> Dict[str, Any]:
        """
        Analyze the Nginx configuration file and identify security issues.

        Args:
            file_path: Path to the Nginx config file (optional, will be auto-detected if not provided)

        Returns:
            Dictionary containing analysis results
        """
        # Find Nginx config if not provided
        if not file_path:
            file_path = self._find_nginx_config()
            if not file_path:
                return {"success": False, "message": "Nginx configuration file not found", "issues": []}

        try:
            with open(file_path, 'r') as f:
                content = f.read()
                content_lines = content.splitlines()

            # Identify block positions for adding missing directives
            block_positions = self._identify_block_positions(content_lines)

            issues = []

            # Check each security rule
            for fix_id, fix_info in self.security_fixes.items():
                pattern = fix_info["pattern"]
                matches = re.findall(pattern, content, re.MULTILINE)

                if not matches:
                    # Setting is missing
                    if fix_info["add_if_missing"]:
                        # Check if we have the right block to add it to
                        add_location = fix_info.get("add_location", "http")
                        if add_location in block_positions and block_positions[add_location]:
                            issues.append(
                                {"id": fix_id, "description": fix_info["description"], "severity": fix_info["severity"],
                                    "issue_type": "missing", "fix": fix_info["replacement"],
                                    "add_location": add_location})
                else:
                    # Check if setting has correct value
                    setting_line = re.search(pattern, content, re.MULTILINE).group(0)
                    if setting_line.strip() != fix_info["replacement"]:
                        issues.append(
                            {"id": fix_id, "description": fix_info["description"], "severity": fix_info["severity"],
                                "issue_type": "incorrect", "current": setting_line.strip(),
                                "fix": fix_info["replacement"]})

            return {"success": True, "file_path": file_path, "issues": issues, "block_positions": block_positions,
                "message": f"Found {len(issues)} security issues in Nginx configuration"}

        except Exception as e:
            logger.error(f"Error analyzing Nginx configuration: {str(e)}")
            return {"success": False, "message": f"Error analyzing Nginx configuration: {str(e)}", "issues": []}

    def apply_fixes(self, file_path: str = None, fixes: List[Dict[str, Any]] = None, backup: bool = True) -> Tuple[
        bool, str]:
        """
        Apply the suggested fixes to the Nginx configuration file.

        Args:
            file_path: Path to the Nginx config file (optional, will be auto-detected if not provided)
            fixes: List of fixes to apply (if None, all discovered issues will be fixed)
            backup: Whether to create a backup before modifying the file

        Returns:
            Tuple of (success, message)
        """
        # Find Nginx config if not provided
        if not file_path:
            file_path = self._find_nginx_config()
            if not file_path:
                return False, "Nginx configuration file not found"

        # If no specific fixes are provided, analyze and fix all issues
        if fixes is None:
            analysis_result = self.analyze_configuration(file_path)
            if not analysis_result["success"]:
                return False, analysis_result["message"]
            fixes = analysis_result["issues"]
            block_positions = analysis_result.get("block_positions", {})
        else:
            # We need block positions for adding missing directives
            with open(file_path, 'r') as f:
                content_lines = f.read().splitlines()
            block_positions = self._identify_block_positions(content_lines)

        try:
            # Read the current configuration
            with open(file_path, 'r') as f:
                content = f.readlines()

            # Create a backup if requested
            if backup:
                backup_path = f"{file_path}{self.backup_suffix}"
                shutil.copyfile(file_path, backup_path)
                logger.info(f"Created backup of Nginx configuration at {backup_path}")

            # Track which fixes have been applied
            applied_fixes = []

            # Process each fix
            for fix in fixes:
                fix_id = fix.get("id")
                fix_text = fix.get("fix")

                if not fix_id or not fix_text:
                    continue

                # Get the fix details from our security fixes dict
                fix_info = self.security_fixes.get(fix_id)
                if not fix_info:
                    continue

                pattern = fix_info["pattern"]
                issue_type = fix.get("issue_type", "unknown")

                # Handle different issue types
                if issue_type == "missing":
                    # Find appropriate block to add the directive
                    add_location = fix.get("add_location", fix_info.get("add_location", "http"))
                    if add_location in block_positions and block_positions[add_location]:
                        # Get the first block of the required type
                        start_line, end_line = block_positions[add_location][0]

                        # Add directive at the beginning of the block, right after the opening brace
                        indentation = re.match(r"^\s*", content[start_line]).group(0) + "    "
                        content.insert(start_line + 1, f"{indentation}{fix_text}\n")

                        # Update block positions as we've added a line
                        for block_type in block_positions:
                            for i, (s, e) in enumerate(block_positions[block_type]):
                                if s > start_line:
                                    block_positions[block_type][i] = (s + 1, e + 1)
                                elif e > start_line:
                                    block_positions[block_type][i] = (s, e + 1)

                        applied_fixes.append(f"Added: {fix_text} to {add_location} block")
                    else:
                        logger.warning(f"Could not find appropriate {add_location} block to add {fix_id}")

                elif issue_type == "incorrect":
                    # Update the existing setting
                    fixed = False
                    for i, line in enumerate(content):
                        if re.search(pattern, line):
                            # Preserve indentation
                            indentation = re.match(r"^\s*", line).group(0)
                            content[i] = f"{indentation}{fix_text}\n"
                            applied_fixes.append(f"Modified: {line.strip()} -> {fix_text}")
                            fixed = True
                            break

                    # If somehow we didn't find the line (shouldn't happen), log it
                    if not fixed:
                        logger.warning(f"Could not find line to update for {fix_id}")

            # Write the updated configuration back to the file
            with open(file_path, 'w') as f:
                f.writelines(content)

            if applied_fixes:
                return True, f"Successfully applied {len(applied_fixes)} fixes to Nginx configuration.\nDetails:\n" + "\n".join(
                    applied_fixes)
            else:
                return False, "No fixes were applied to the Nginx configuration"

        except Exception as e:
            logger.error(f"Error applying Nginx configuration fixes: {str(e)}")
            return False, f"Error applying Nginx configuration fixes: {str(e)}"

    def restart_service(self, service_name: str = "nginx") -> Tuple[bool, str]:
        """
        Restart the Nginx service after applying configuration changes.

        Args:
            service_name: Name of the Nginx service (defaults to 'nginx')

        Returns:
            Tuple of (success, message)
        """
        # Test configuration before restarting
        try:
            test_result = subprocess.run(['nginx', '-t'], check=False, capture_output=True, text=True)
            if test_result.returncode != 0:
                return False, f"Configuration test failed, not restarting: {test_result.stderr}"
        except FileNotFoundError:
            logger.warning("Could not test Nginx configuration before restarting")

        # Detect the operating system for appropriate service commands
        if os.name == 'posix':  # Linux/Unix
            # Try systemctl first (modern Linux)
            try:
                result = subprocess.run(['systemctl', 'restart', service_name], check=True, capture_output=True,
                                        text=True)
                return True, f"Successfully restarted {service_name} service using systemctl"
            except subprocess.CalledProcessError as e:
                logger.warning(f"Failed to restart using systemctl: {e}")

                # Try service command (older Linux/Unix)
                try:
                    result = subprocess.run(['service', service_name, 'restart'], check=True, capture_output=True,
                                            text=True)
                    return True, f"Successfully restarted {service_name} service using service command"
                except subprocess.CalledProcessError as e:
                    logger.error(f"Failed to restart service: {e}")
                    return False, f"Failed to restart {service_name} service: {e}"
                except FileNotFoundError:
                    # Try nginx -s signal directly
                    try:
                        result = subprocess.run(['nginx', '-s', 'reload'], check=True, capture_output=True, text=True)
                        return True, f"Successfully reloaded {service_name} using direct signal"
                    except (subprocess.CalledProcessError, FileNotFoundError) as e:
                        return False, f"Could not restart {service_name}, please restart manually: {e}"
            except FileNotFoundError:
                # Try service command if systemctl is not available
                try:
                    result = subprocess.run(['service', service_name, 'restart'], check=True, capture_output=True,
                                            text=True)
                    return True, f"Successfully restarted {service_name} service using service command"
                except (subprocess.CalledProcessError, FileNotFoundError) as e:
                    # Try nginx -s signal directly
                    try:
                        result = subprocess.run(['nginx', '-s', 'reload'], check=True, capture_output=True, text=True)
                        return True, f"Successfully reloaded {service_name} using direct signal"
                    except (subprocess.CalledProcessError, FileNotFoundError) as e:
                        return False, f"Could not restart {service_name}, please restart manually: {e}"

        elif os.name == 'nt':  # Windows
            try:
                # For Windows Nginx
                result = subprocess.run(['net', 'stop', service_name], check=False, capture_output=True, text=True)
                result = subprocess.run(['net', 'start', service_name], check=True, capture_output=True, text=True)
                return True, f"Successfully restarted {service_name} service on Windows"
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to restart {service_name} service on Windows: {e}")
                return False, f"Failed to restart {service_name} service on Windows: {e}"

        return False, f"Unsupported operating system: {os.name}, please restart {service_name} manually"

    def get_supported_services(self) -> List[str]:
        """
        Return a list of services supported by this plugin.

        Returns:
            List of service names that this plugin can handle
        """
        return ["nginx", "nginx-service"]
