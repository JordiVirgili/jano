import socket
import logging
import paramiko
import time
from typing import Dict, Any, List, Optional, Tuple
from eris.core.plugins import AttackPlugin

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RealSSHPlugin(AttackPlugin):
    """Plugin for testing weak SSH configurations."""

    def __init__(self):
        """Initialize the Real SSH plugin."""
        self.common_passwords = ["password", "admin", "1990nosec"]
        self.common_usernames = ["admin", "jordivirgili", "root"]
        self.timeout = 5  # Connection timeout in seconds
        self.max_attempts = 10  # Maximum number of login attempts
        self.delay_between_attempts = 1  # Delay between attempts (seconds) to avoid triggering lockouts

    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the plugin with the provided configuration."""
        if config.get("common_passwords"):
            self.common_passwords = config["common_passwords"]

        if config.get("common_usernames"):
            self.common_usernames = config["common_usernames"]

        if config.get("timeout"):
            self.timeout = config["timeout"]

        if config.get("max_attempts"):
            self.max_attempts = config["max_attempts"]

        if config.get("delay_between_attempts"):
            self.delay_between_attempts = config["delay_between_attempts"]

    def _check_ssh_port_open(self, host: str, port: int = 22) -> bool:
        """Check if SSH port is open on the target."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception as e:
            logger.error(f"Error checking SSH port: {str(e)}")
            return False

    def _attempt_ssh_login(self, host: str, port: int, username: str, password: str) -> Tuple[bool, str]:
        """
        Attempt to authenticate to SSH with the given credentials.

        Args:
            host: Target hostname or IP
            port: SSH port
            username: Username to try
            password: Password to try

        Returns:
            Tuple of (success, error_message)
        """
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            client.connect(hostname=host, port=port, username=username, password=password, timeout=self.timeout,
                allow_agent=False, look_for_keys=False)
            client.close()
            return True, ""
        except paramiko.AuthenticationException:
            return False, "Authentication failed"
        except paramiko.SSHException as e:
            return False, f"SSH error: {str(e)}"
        except Exception as e:
            return False, f"Error: {str(e)}"
        finally:
            if client:
                client.close()

    def execute_attack(self, target: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a real weak password attack against an SSH server.

        This method actually attempts to authenticate with common username/password
        combinations, but limits attempts to avoid triggering lockout mechanisms.

        Args:
            target: The target hostname or IP address
            options: Optional attack parameters
                - port: SSH port (default: 22)
                - usernames: List of usernames to try (overrides defaults)
                - passwords: List of passwords to try (overrides defaults)
                - max_attempts: Maximum number of login attempts

        Returns:
            Dictionary with attack results
        """
        options = options or {}
        port = options.get("port", 22)
        max_attempts = options.get("max_attempts", self.max_attempts)
        usernames = options.get("usernames", self.common_usernames)
        passwords = options.get("passwords", self.common_passwords)

        # Check if SSH port is open
        is_ssh_open = self._check_ssh_port_open(target, port)

        if not is_ssh_open:
            return {"success": False, "details": f"SSH port {port} is closed or filtered on {target}",
                "severity": "info", "recommendations": "No action needed as the service is not accessible."}

        # Track authentication attempts
        attempts = 0
        successful_login = False
        successful_credentials = {}
        attempted_combinations = []

        # Try common username/password combinations
        for username in usernames:
            if successful_login or attempts >= max_attempts:
                break

            for password in passwords:
                if successful_login or attempts >= max_attempts:
                    break

                # Log the attempt
                logger.info(f"Attempting SSH login to {target}:{port} with {username}/{password}")
                attempts += 1
                attempted_combinations.append({"username": username, "password": password})

                # Try to authenticate
                login_successful, error = self._attempt_ssh_login(target, port, username, password)

                if login_successful:
                    successful_login = True
                    successful_credentials = {"username": username, "password": password}
                    logger.warning(f"Successful SSH login to {target}:{port} with {username}/{password}")
                    break

                # Add delay between attempts to avoid triggering lockout
                time.sleep(self.delay_between_attempts)

        # Prepare the results
        if successful_login:
            return {"success": True,
                "details": f"Successfully authenticated to SSH server on {target}:{port} using weak credentials",
                "severity": "critical",
                "recommendations": ["Change the password for the compromised account immediately",
                    "Implement a strong password policy",
                    "Configure SSH to use key-based authentication only (disable password authentication)",
                    "Set up fail2ban to prevent brute force attacks",
                    "Restrict SSH access to specific IP addresses if possible",
                    "Consider changing the default SSH port"],
                "details_extended": {"successful_credentials": successful_credentials, "attempts": attempts,
                    "attempted_combinations": attempted_combinations}}
        else:
            return {"success": False,
                "details": f"Could not authenticate to SSH server on {target}:{port} using common credentials (attempted {attempts} combinations)",
                "severity": "low", "recommendations": ["Continue to maintain strong password policies",
                    "Consider implementing key-based authentication for SSH",
                    "Set up fail2ban to prevent brute force attacks",
                    "Consider restricting SSH access to specific IP addresses"],
                "details_extended": {"attempts": attempts, "attempted_combinations": attempted_combinations}}

    def get_capabilities(self) -> List[str]:
        """Return the capabilities of the plugin."""
        return ["ssh_weak_credentials", "port_check", "brute_force"]