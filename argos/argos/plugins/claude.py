import os
from typing import Optional, Dict, Any, List
import anthropic
import re


class ClaudePlugin:
    """Plugin for interacting with Anthropic's Claude API with dynamic model selection."""

    def __init__(self):
        """Initialize the Claude plugin."""
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.default_model = os.getenv("ANTHROPIC_DEFAULT_MODEL", "claude-3-5-sonnet-20240620")
        self.advanced_model = os.getenv("ANTHROPIC_ADVANCED_MODEL", "claude-3-7-sonnet-20240229")
        self.client = anthropic.Anthropic(api_key=self.api_key)

        # Regex patterns to identify advanced tasks
        self.advanced_task_patterns = [r"(?i)evaluat(e|ing|ion)", r"(?i)analy(ze|sis|zing)",
            r"(?i)secur(e|ity) (audit|assessment)", r"(?i)vulnerabilit(y|ies)", r"(?i)penetration test",
            r"(?i)threat model", r"(?i)comprehensive", r"(?i)in-depth", r"(?i)detailed (review|analysis|report)",
            r"(?i)generate (a|full|complete) (report|assessment)",
            r"(?i)scan (my|the|this) (system|server|service|configuration)", ]

    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the plugin with the provided configuration."""
        if config.get("api_key"):
            self.api_key = config["api_key"]
            self.client = anthropic.Anthropic(api_key=self.api_key)

        if config.get("default_model"):
            self.default_model = config["default_model"]

        if config.get("advanced_model"):
            self.advanced_model = config["advanced_model"]

        if config.get("advanced_task_patterns"):
            self.advanced_task_patterns = config["advanced_task_patterns"]

    def _select_model(self, prompt: str, context: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Dynamically select the appropriate Claude model based on the task complexity.

        Args:
            prompt: The user's message
            context: Optional conversation history

        Returns:
            The model ID to use
        """
        # Check if any advanced task patterns match the prompt
        for pattern in self.advanced_task_patterns:
            if re.search(pattern, prompt):
                return self.advanced_model

        # If the message is unusually long, use the advanced model
        if len(prompt) > 2000:
            return self.advanced_model

        # Default to the simpler model for regular conversation
        return self.default_model

    def generate_response(self, prompt: str, context: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Generate a response using Claude with dynamic model selection.

        Args:
            prompt: The user's message
            context: Optional list of previous messages in the conversation
                     Each message should be a dict with 'role' and 'content' keys

        Returns:
            The generated response text
        """
        messages = []

        # Add system message if context is empty
        if not context:
            messages.append({"role": "assistant",
                "content": "I am a security configuration assistant. I'll help analyze and improve security configurations for various services and systems."})

        # Add conversation history if provided
        if context:
            # Convert from OpenAI format to Anthropic format if needed
            for msg in context:
                role = msg["role"]
                # Map 'user' and 'assistant' roles directly
                # Map 'system' role to 'assistant' with a note that it's a system message
                if role == "system":
                    messages.append({"role": "assistant", "content": f"[System instruction: {msg['content']}]"})
                else:
                    messages.append({"role": role, "content": msg["content"]})

        # Add the current user message
        messages.append({"role": "user", "content": prompt})

        # Select the appropriate model
        selected_model = self._select_model(prompt, context)

        try:
            # Make the API call with the selected model
            response = self.client.messages.create(model=selected_model, messages=messages, max_tokens=4096,
                temperature=0.7)

            # Extract the response text
            return response.content[0].text

        except Exception as e:
            # Handle any errors
            return f"Error generating response: {str(e)}"

    def get_capabilities(self) -> List[str]:
        """Return the capabilities of the Claude model."""
        return ["text_generation", "code_analysis", "security_assessment", "configuration_review",
            "vulnerability_analysis", "dynamic_model_selection"]