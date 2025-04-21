from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


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