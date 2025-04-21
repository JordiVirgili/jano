import os
from typing import Optional, Dict, Any, List
import openai
from argos.core.plugins import LLMPlugin


class OpenAIPlugin(LLMPlugin):
    """Plugin for interacting with OpenAI APIs."""

    def __init__(self):
        """Initialize the OpenAI plugin."""
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        self.client = None
        self.last_used_model = None

    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the plugin with the provided configuration."""
        if config.get("api_key"):
            self.api_key = config["api_key"]

        if not self.api_key:
            raise ValueError("API key is required for OpenAI plugin")

        # Initialize the client
        self.client = openai.OpenAI(api_key=self.api_key)

        if config.get("model"):
            self.model = config["model"]

        self.last_used_model = self.model

    def generate_response(self, prompt: str, context: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Generate a response using OpenAI API.

        Args:
            prompt: The user's message
            context: Optional list of previous messages in the conversation
                     Each message should be a dict with 'role' and 'content' keys

        Returns:
            The generated response text
        """
        if not self.client:
            raise ValueError("Plugin not initialized. Call initialize() first.")

        messages = []

        # Add system message if context is empty
        if not context:
            messages.append({"role": "system",
                             "content": "I am a security configuration assistant. I'll help analyze and improve security configurations for various services and systems."})

        # Add conversation history if provided
        if context:
            messages.extend(context)

        # Add the current user message
        messages.append({"role": "user", "content": prompt})

        try:
            # Make the API call
            response = self.client.chat.completions.create(model=self.model, messages=messages, max_tokens=4096,
                temperature=0.7)

            # Extract the response text
            return response.choices[0].message.content

        except Exception as e:
            # Handle any errors
            return f"Error generating response: {str(e)}"

    def get_capabilities(self) -> List[str]:
        """Return the capabilities of the OpenAI model."""
        return ["text_generation", "code_analysis", "security_assessment", "configuration_review"]