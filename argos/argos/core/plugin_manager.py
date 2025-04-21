import os
import importlib
import inspect
import logging
from typing import Dict, Type, List, Optional

from argos.core.plugins import LLMPlugin

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PluginManager:
    """Manager for loading and managing plugins."""

    def __init__(self, plugins_dir: str = "argos/plugins"):
        """
        Initialize the plugin manager.

        Args:
            plugins_dir: Directory containing plugin modules
        """
        self.plugins_dir = plugins_dir
        self.plugin_classes: Dict[str, Type[LLMPlugin]] = {}
        self.loaded_plugins: Dict[str, LLMPlugin] = {}

    def discover_plugins(self) -> List[str]:
        """
        Discover available LLM plugins in the plugins directory.

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

        # Import each module and find LLMPlugin subclasses
        for plugin_file in plugin_files:
            try:
                module_name = f"{module_path}.{plugin_file}"
                module = importlib.import_module(module_name)

                # Scan all classes in the module
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    # Check if the class inherits from LLMPlugin and is not LLMPlugin itself
                    if issubclass(obj, LLMPlugin) and obj is not LLMPlugin:
                        self.plugin_classes[name.lower()] = obj
                        logger.info(f"Discovered LLM plugin: {name}")
            except Exception as e:
                logger.error(f"Error loading plugin '{plugin_file}': {str(e)}")

        return list(self.plugin_classes.keys())

    def get_plugin(self, plugin_name: str, config: Optional[Dict] = None) -> Optional[LLMPlugin]:
        """
        Get an instance of a plugin by name, creating it if necessary.

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

            # Cache the instance
            self.loaded_plugins[plugin_name] = plugin_instance

            return plugin_instance
        except Exception as e:
            logger.error(f"Error instantiating plugin '{plugin_name}': {str(e)}")
            return None