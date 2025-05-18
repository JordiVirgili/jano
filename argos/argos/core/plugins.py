from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple


class LLMPlugin(ABC):
    """Base abstract class for LLM plugins"""

    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the plugin with the provided configuration."""
        pass

    @abstractmethod
    def generate_response(self, prompt: str, context: Optional[List[Dict[str, str]]] = None, force_advanced: bool = False) -> str:
        """
        Generate a response based on the prompt and optional conversation context.

        Args:
            prompt: The user's message
            context: Optional list of previous messages in the conversation
                     Each message should be a dict with 'role' and 'content' keys
            force_advanced: Force advanced model

        Returns:
            The generated response text
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Return the capabilities of the LLM model.

        Returns:
            List of capability strings (e.g., "text_generation", "code_analysis")
        """
        pass


class ConfigFixerPlugin(ABC):
    """
    Base abstract class for configuration fixing plugins.
    These plugins can automatically apply fixes to configuration files.
    """

    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the plugin with the provided configuration."""
        pass

    @abstractmethod
    def analyze_configuration(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze a configuration file and identify security issues.

        Args:
            file_path: Path to the configuration file

        Returns:
            Dictionary containing analysis results including:
            - issues: List of identified security issues
            - severity: Assessed severity level for each issue
            - fixes: Suggested fixes for each issue
        """
        pass

    @abstractmethod
    def apply_fixes(self, file_path: str, fixes: List[Dict[str, Any]], backup: bool = True) -> Tuple[bool, str]:
        """
        Apply the suggested fixes to a configuration file.

        Args:
            file_path: Path to the configuration file
            fixes: List of fixes to apply (each as a dict with needed details)
            backup: Whether to create a backup before modifying the file

        Returns:
            Tuple of (success, message) where:
            - success: Boolean indicating if fixes were applied successfully
            - message: Detailed message about the results
        """
        pass

    @abstractmethod
    def restart_service(self, service_name: str) -> Tuple[bool, str]:
        """
        Restart a service after applying configuration changes.

        Args:
            service_name: Name of the service to restart

        Returns:
            Tuple of (success, message) where:
            - success: Boolean indicating if service was restarted successfully
            - message: Detailed message about the restart process
        """
        pass

    @abstractmethod
    def get_supported_services(self) -> List[str]:
        """
        Return a list of services supported by this plugin.

        Returns:
            List of service names that this plugin can handle
        """
        pass