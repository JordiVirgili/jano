from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
import os
import logging

from argos.database import ChatSessionRepository, ChatMessageRepository
from argos.core import PluginManager, FixerPluginManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FixerService:
    """Service for handling automated fixing of configurations."""

    def __init__(self):
        """Initialize the fixer service."""
        self.fixer_plugin_manager = FixerPluginManager()
        self.fixer_plugin_manager.discover_plugins()

    def get_supported_services(self) -> Dict[str, List[str]]:
        """
        Get a list of all services supported by the available plugins.

        Returns:
            Dictionary mapping plugin names to the services they support
        """
        return self.fixer_plugin_manager.list_supported_services()

    def analyze_configuration(self, service_name: str, file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze the configuration of a specific service.

        Args:
            service_name: Name of the service to analyze
            file_path: Path to the configuration file (optional)

        Returns:
            Dictionary containing analysis results
        """
        plugin = self.fixer_plugin_manager.find_plugin_for_service(service_name)
        if not plugin:
            return {"success": False, "message": f"No plugin found for service: {service_name}", "issues": []}

        # Analyze the configuration
        result = plugin.analyze_configuration(file_path)

        return result

    def apply_fixes(self, service_name: str, file_path: Optional[str] = None,
                    fixes: Optional[List[Dict[str, Any]]] = None, backup: bool = True, restart: bool = False) -> Dict[
        str, Any]:
        """
        Apply fixes to a service configuration.

        Args:
            service_name: Name of the service to fix
            file_path: Path to the configuration file (optional)
            fixes: List of specific fixes to apply (optional)
            backup: Whether to create a backup before modifying the file
            restart: Whether to restart the service after applying fixes

        Returns:
            Dictionary containing the result of the fix operation
        """
        plugin = self.fixer_plugin_manager.find_plugin_for_service(service_name)
        if not plugin:
            return {"success": False, "message": f"No plugin found for service: {service_name}"}

        # Apply the fixes
        success, message = plugin.apply_fixes(file_path, fixes, backup)

        result = {"success": success, "message": message, "service": service_name}

        # Restart the service if requested and fixes were applied successfully
        if restart and success:
            restart_success, restart_message = plugin.restart_service(service_name)
            result["restart_success"] = restart_success
            result["restart_message"] = restart_message

        return result

    def get_plugin_for_service(self, service_name: str):
        """
        Get the appropriate plugin for a service.

        Args:
            service_name: Name of the service

        Returns:
            Plugin instance or None if not found
        """
        return self.fixer_plugin_manager.find_plugin_for_service(service_name)


# Create a singleton instance
fixer_service = FixerService()
