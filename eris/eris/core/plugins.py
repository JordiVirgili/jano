from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class AttackPlugin(ABC):
    """Base abstract class for attack plugins"""

    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the plugin with the provided configuration."""
        pass

    @abstractmethod
    def execute_attack(self, target: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute an attack against the specified target with optional parameters.

        Args:
            target: The target (hostname, IP, service name) to attack
            options: Optional configuration options for the attack

        Returns:
            Dictionary containing the attack results including:
            - success: boolean indicating if vulnerability was found
            - details: detailed information about the findings
            - severity: assessed severity level (low, medium, high, critical)
            - recommendations: suggestions to fix the vulnerability
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Return the capabilities of the attack plugin.

        Returns:
            List of capability strings (e.g., "ssh_brute_force", "port_scan")
        """
        pass