import os
import importlib
import inspect
import logging
from typing import Dict, Type, List, Optional, Any

from argos.core.plugins import ConfigFixerPlugin

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FixerPluginManager:
    """Manager for loading and managing configuration fixer plugins."""

    def __init__(self, plugins_dir: str = "argos/plugins/fixers"):
        """
        Initialize the fixer plugin manager.

        Args:
            plugins_dir: Directory containing fixer plugin modules
        """
        self.plugins_dir = plugins_dir
        self.plugin_classes: Dict[str, Type[ConfigFixerPlugin]] = {}
        self.loaded_plugins: Dict[str, ConfigFixerPlugin] = {}

    def discover_plugins(self) -> List[str]:
        """
        Discover available configuration fixer plugins in the plugins directory.

        Returns:
            List of plugin names
        """
        plugin_files = []

        # Convert the plugins directory to a module path
        module_path = self.plugins_dir.replace("/", ".")

        # Scan the plugins directory for Python files
        try:
            for item in os.listdir(self.plugins_dir):
                if item.endswith('.py') and not item.startswith('__'):
                    plugin_files.append(item[:-3])  # Remove .py extension
        except FileNotFoundError:
            logger.error(f"Plugin directory {self.plugins_dir} not found")
            return []

        # Import each module and find ConfigFixerPlugin subclasses
        for plugin_file in plugin_files:
            try:
                module_name = f"{module_path}.{plugin_file}"
                module = importlib.import_module(module_name)

                # Scan all classes in the module
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    # Check if the class inherits from ConfigFixerPlugin and is not ConfigFixerPlugin itself
                    if issubclass(obj, ConfigFixerPlugin) and obj is not ConfigFixerPlugin:
                        self.plugin_classes[name.lower()] = obj
                        logger.info(f"Discovered fixer plugin: {name}")
            except Exception as e:
                logger.error(f"Error loading plugin '{plugin_file}': {str(e)}")

        return list(self.plugin_classes.keys())

    def get_plugin(self, plugin_name: str, config: Optional[Dict] = None) -> Optional[ConfigFixerPlugin]:
        """
        Get an instance of a fixer plugin by name, creating it if necessary.

        Args:
            plugin_name: The name of the plugin (case-insensitive)
            config: Optional configuration for the plugin

        Returns:
            An instance of the requested plugin or None if not found
        """
        plugin_name = plugin_name.lower()

        # Check if we already have an instance
        if plugin_name in self.loaded_plugins:
            return self.loaded_plugins[plugin_name]

        # Check if we know about this plugin
        if plugin_name not in self.plugin_classes:
            logger.error(f"Plugin '{plugin_name}' not found")
            return None

        # Create a new instance
        try:
            plugin_instance = self.plugin_classes[plugin_name]()

            # Initialize the plugin if configuration is provided
            if config:
                plugin_instance.initialize(config)
            else:
                plugin_instance.initialize({})

            # Cache the instance
            self.loaded_plugins[plugin_name] = plugin_instance

            return plugin_instance
        except Exception as e:
            logger.error(f"Error instantiating plugin '{plugin_name}': {str(e)}")
            return None

    def find_plugin_for_service(self, service_name: str) -> Optional[ConfigFixerPlugin]:
        """
        Find a fixer plugin that supports the specified service.

        Args:
            service_name: Name of the service to find a plugin for

        Returns:
            A plugin instance that supports the service, or None if not found
        """
        # Ensure plugins are discovered
        if not self.plugin_classes:
            self.discover_plugins()

        # Try to find a plugin that supports the requested service
        for plugin_name in self.plugin_classes:
            plugin = self.get_plugin(plugin_name)
            if plugin and service_name.lower() in [s.lower() for s in plugin.get_supported_services()]:
                return plugin

        return None

    def list_supported_services(self) -> Dict[str, List[str]]:
        """
        Get a list of all services supported by the available plugins.

        Returns:
            Dictionary mapping plugin names to the services they support
        """
        supported_services = {}

        # Ensure plugins are discovered
        if not self.plugin_classes:
            self.discover_plugins()

        for plugin_name in self.plugin_classes:
            plugin = self.get_plugin(plugin_name)
            if plugin:
                supported_services[plugin_name] = plugin.get_supported_services()

        return supported_services
