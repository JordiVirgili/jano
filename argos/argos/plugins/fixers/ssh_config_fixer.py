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


class SSHConfigFixer(ConfigFixerPlugin):
    """Plugin for automatically fixing SSH server configurations."""

    def __init__(self):
        """Initialize the SSH Config Fixer plugin."""
        self.common_ssh_paths = ["/etc/ssh/sshd_config", "/etc/sshd_config", "C:\\ProgramData\\ssh\\sshd_config"]
        self.backup_suffix = f".bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Common security fixes and their patterns
        self.security_fixes = {"disable_password_auth": {"pattern": r"^[#\s]*(PasswordAuthentication)\s+(yes|no)",
            "replacement": "PasswordAuthentication no", "add_if_missing": True,
            "description": "Disable password authentication", "severity": "high"},
            "disable_root_login": {"pattern": r"^[#\s]*(PermitRootLogin)\s+(yes|no|prohibit-password)",
                "replacement": "PermitRootLogin no", "add_if_missing": True, "description": "Disable root login",
                "severity": "high"},
            "use_protocol_2": {"pattern": r"^[#\s]*(Protocol)\s+([12])", "replacement": "Protocol 2",
                "add_if_missing": True, "description": "Use SSH Protocol 2", "severity": "high"},
            "max_auth_tries": {"pattern": r"^[#\s]*(MaxAuthTries)\s+(\d+)", "replacement": "MaxAuthTries 3",
                "add_if_missing": True, "description": "Limit authentication attempts", "severity": "medium"},
            "client_alive_interval": {"pattern": r"^[#\s]*(ClientAliveInterval)\s+(\d+)",
                "replacement": "ClientAliveInterval 300", "add_if_missing": True,
                "description": "Set client alive interval", "severity": "medium"},
            "client_alive_count_max": {"pattern": r"^[#\s]*(ClientAliveCountMax)\s+(\d+)",
                "replacement": "ClientAliveCountMax 3", "add_if_missing": True,
                "description": "Set maximum client alive count", "severity": "medium"},
            "disable_empty_passwords": {"pattern": r"^[#\s]*(PermitEmptyPasswords)\s+(yes|no)",
                "replacement": "PermitEmptyPasswords no", "add_if_missing": True,
                "description": "Disable empty passwords", "severity": "high"}}

    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the plugin with the provided configuration."""
        if config.get("ssh_config_path"):
            self.common_ssh_paths.insert(0, config["ssh_config_path"])

    def _find_ssh_config(self) -> Optional[str]:
        """Find the SSH server configuration file."""
        for path in self.common_ssh_paths:
            if os.path.isfile(path):
                return path
        return None

    def analyze_configuration(self, file_path: str = None) -> Dict[str, Any]:
        """
        Analyze the SSH configuration file and identify security issues.

        Args:
            file_path: Path to the SSH config file (optional, will be auto-detected if not provided)

        Returns:
            Dictionary containing analysis results
        """
        # Find SSH config if not provided
        if not file_path:
            file_path = self._find_ssh_config()
            if not file_path:
                return {"success": False, "message": "SSH configuration file not found", "issues": []}

        try:
            with open(file_path, 'r') as f:
                content = f.read()

            issues = []

            # Check each security rule
            for fix_id, fix_info in self.security_fixes.items():
                pattern = fix_info["pattern"]
                matches = re.findall(pattern, content, re.MULTILINE)

                if not matches:
                    # Setting is missing
                    if fix_info["add_if_missing"]:
                        issues.append(
                            {"id": fix_id, "description": fix_info["description"], "severity": fix_info["severity"],
                                "issue_type": "missing", "fix": fix_info["replacement"]})
                else:
                    # Check if setting has correct value
                    setting_line = re.search(pattern, content, re.MULTILINE).group(0)
                    if setting_line.strip() != fix_info["replacement"]:
                        issues.append(
                            {"id": fix_id, "description": fix_info["description"], "severity": fix_info["severity"],
                                "issue_type": "incorrect", "current": setting_line.strip(),
                                "fix": fix_info["replacement"]})

            return {"success": True, "file_path": file_path, "issues": issues,
                "message": f"Found {len(issues)} security issues in SSH configuration"}

        except Exception as e:
            logger.error(f"Error analyzing SSH configuration: {str(e)}")
            return {"success": False, "message": f"Error analyzing SSH configuration: {str(e)}", "issues": []}

    def apply_fixes(self, file_path: str = None, fixes: List[Dict[str, Any]] = None, backup: bool = True) -> Tuple[
        bool, str]:
        """
        Apply the suggested fixes to the SSH configuration file.

        Args:
            file_path: Path to the SSH config file (optional, will be auto-detected if not provided)
            fixes: List of fixes to apply (if None, all discovered issues will be fixed)
            backup: Whether to create a backup before modifying the file

        Returns:
            Tuple of (success, message)
        """
        # Find SSH config if not provided
        if not file_path:
            file_path = self._find_ssh_config()
            if not file_path:
                return False, "SSH configuration file not found"

        # If no specific fixes are provided, analyze and fix all issues
        if fixes is None:
            analysis_result = self.analyze_configuration(file_path)
            if not analysis_result["success"]:
                return False, analysis_result["message"]
            fixes = analysis_result["issues"]

        try:
            # Read the current configuration
            with open(file_path, 'r') as f:
                content = f.readlines()

            # Create a backup if requested
            if backup:
                backup_path = f"{file_path}{self.backup_suffix}"
                shutil.copyfile(file_path, backup_path)
                logger.info(f"Created backup of SSH configuration at {backup_path}")

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
                    # Add the new setting at the end of the file
                    content.append(f"{fix_text}\n")
                    applied_fixes.append(f"Added: {fix_text}")

                elif issue_type == "incorrect":
                    # Update the existing setting
                    fixed = False
                    for i, line in enumerate(content):
                        if re.match(pattern, line):
                            content[i] = f"{fix_text}\n"
                            applied_fixes.append(f"Modified: {line.strip()} -> {fix_text}")
                            fixed = True
                            break

                    # If somehow we didn't find the line (shouldn't happen), add it
                    if not fixed:
                        content.append(f"{fix_text}\n")
                        applied_fixes.append(f"Added missing: {fix_text}")

            # Write the updated configuration back to the file
            with open(file_path, 'w') as f:
                f.writelines(content)

            return True, f"Successfully applied {len(applied_fixes)} fixes to SSH configuration.\nDetails:\n" + "\n".join(
                applied_fixes)

        except Exception as e:
            logger.error(f"Error applying SSH configuration fixes: {str(e)}")
            return False, f"Error applying SSH configuration fixes: {str(e)}"

    def restart_service(self, service_name: str = "ssh") -> Tuple[bool, str]:
        """
        Restart the SSH service after applying configuration changes.

        Args:
            service_name: Name of the SSH service (defaults to 'ssh')

        Returns:
            Tuple of (success, message)
        """
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
                    return False, f"Service command not found, please restart {service_name} manually"
            except FileNotFoundError:
                # Try service command if systemctl is not available
                try:
                    result = subprocess.run(['service', service_name, 'restart'], check=True, capture_output=True,
                                            text=True)
                    return True, f"Successfully restarted {service_name} service using service command"
                except subprocess.CalledProcessError as e:
                    logger.error(f"Failed to restart service: {e}")
                    return False, f"Failed to restart {service_name} service: {e}"
                except FileNotFoundError:
                    return False, f"Service command not found, please restart {service_name} manually"

        elif os.name == 'nt':  # Windows
            try:
                # For Windows OpenSSH Server
                result = subprocess.run(['net', 'stop', 'sshd'], check=True, capture_output=True, text=True)
                result = subprocess.run(['net', 'start', 'sshd'], check=True, capture_output=True, text=True)
                return True, "Successfully restarted SSH service on Windows"
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to restart SSH service on Windows: {e}")
                return False, f"Failed to restart SSH service on Windows: {e}"

        return False, f"Unsupported operating system: {os.name}, please restart {service_name} manually"

    def get_supported_services(self) -> List[str]:
        """
        Return a list of services supported by this plugin.

        Returns:
            List of service names that this plugin can handle
        """
        return ["ssh", "sshd", "openssh", "openssh-server"]
