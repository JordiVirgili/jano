import socket
import logging
from typing import Dict, Any, List, Optional
from eris.core.plugins import AttackPlugin

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WeakSSHPlugin(AttackPlugin):
    """Plugin for testing weak SSH configurations."""

    def __init__(self):
        """Initialize the Weak SSH plugin."""
        self.common_passwords = ["password", "admin", "root", "123456", "qwerty"]
        self.common_usernames = ["admin", "root", "user", "test"]
        self.timeout = 5  # Connection timeout in seconds

    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the plugin with the provided configuration."""
        if config.get("common_passwords"):
            self.common_passwords = config["common_passwords"]

        if config.get("common_usernames"):
            self.common_usernames = config["common_usernames"]

        if config.get("timeout"):
            self.timeout = config["timeout"]

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

    def execute_attack(self, target: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a simulated weak password attack against an SSH server.

        This is a simulation only - it does not actually attempt to authenticate.
        It only checks if the SSH port is open and returns educational information.

        Args:
            target: The target hostname or IP address
            options: Optional attack parameters
                - port: SSH port (default: 22)

        Returns:
            Dictionary with attack results
        """
        options = options or {}
        port = options.get("port", 22)

        # Check if SSH port is open
        is_ssh_open = self._check_ssh_port_open(target, port)

        if not is_ssh_open:
            return {"success": False, "details": f"SSH port {port} is closed or filtered on {target}",
                "severity": "info", "recommendations": "No action needed as the service is not accessible."}

        # This is a simulation - we don't actually try to brute force
        # Instead, we return educational information
        return {"success": True, "details": (f"SSH service detected on {target}:{port}. "
                                             "This is a simulated result showing what would happen if weak credentials were used. "
                                             "Real attackers could try common username/password combinations."),
            "severity": "medium", "recommendations": ["Use strong, unique passwords for all SSH accounts",
                "Implement SSH key-based authentication instead of password authentication",
                "Consider using fail2ban to prevent brute force attacks",
                "Restrict SSH access to specific IP addresses if possible",
                "Change the default SSH port to reduce automated scanning"],
            "details_extended": {"simulated_usernames": self.common_usernames,
                "simulated_passwords": self.common_passwords,
                "educational_note": "This plugin does not attempt actual authentication. It only checks for open ports."}}

    def get_capabilities(self) -> List[str]:
        """Return the capabilities of the plugin."""
        return ["ssh_weak_credentials_simulation", "port_check"]