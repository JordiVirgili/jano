# LLM Plugin Development Guide for Jano

## Introduction

LLM plugins enable integration of different language model providers (OpenAI, Anthropic, local models, etc.) within the Jano ecosystem. This guide explains how to create and integrate new LLM plugins.

## Plugin System Architecture

### Base Interface: `LLMPlugin`

All LLM plugins must implement the abstract interface defined in `argos/core/plugins.py`:

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class LLMPlugin(ABC):
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
            force_advanced: Force the use of advanced model

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
```

### Discovery System

The `PluginManager` (`argos/core/plugin_manager.py`) automatically discovers plugins:
- Scans the `argos/plugins/` directory
- Dynamically imports modules
- Registers classes that inherit from `LLMPlugin`
- Provides instances with automatic caching

## Creating a New LLM Plugin

### 1. Basic Structure

Create a new file in `argos/plugins/` named after your provider:

```python
# argos/plugins/my_llm_plugin.py
import os
from typing import Optional, Dict, Any, List
from argos.core.plugins import LLMPlugin

class MyLLMPlugin(LLMPlugin):
    """Plugin for integrating my LLM provider."""

    def __init__(self):
        """Initialize the plugin."""
        self.api_key = None
        self.model = None
        self.client = None
        self.last_used_model = None
```

### 2. Implement the `initialize()` Method

```python
def initialize(self, config: Dict[str, Any]) -> None:
    """Initialize the plugin with the provided configuration."""
    # Get configuration from environment variables or config dict
    self.api_key = config.get("api_key") or os.getenv("MY_LLM_API_KEY")
    self.model = config.get("model") or os.getenv("MY_LLM_MODEL", "default-model")
    
    if not self.api_key:
        raise ValueError("API key is required for MyLLM plugin")
    
    # Initialize the API client
    try:
        import my_llm_sdk  # Import provider's SDK
        self.client = my_llm_sdk.Client(api_key=self.api_key)
        self.last_used_model = self.model
    except ImportError:
        raise ValueError("MyLLM SDK is not installed")
    except Exception as e:
        raise ValueError(f"Failed to initialize MyLLM client: {str(e)}")
```

### 3. Implement the `generate_response()` Method

```python
def generate_response(self, prompt: str, context: Optional[List[Dict[str, str]]] = None, force_advanced: bool = False) -> str:
    """Generate a response using MyLLM API."""
    if not self.client:
        raise ValueError("Plugin not initialized. Call initialize() first.")

    messages = []
    
    # Add system message if context is empty
    if not context:
        messages.append({
            "role": "system",
            "content": "You are Argos, a security configuration assistant specialized in helping users with secure server and service configurations."
        })
    
    # Add conversation history if provided
    if context:
        # Convert from standard format to provider-specific format if needed
        for msg in context:
            role = msg["role"]
            content = msg["content"]
            
            # Map roles correctly for your provider's API
            if role == "system":
                messages.append({"role": "system", "content": content})
            elif role == "user":
                messages.append({"role": "user", "content": content})
            elif role == "assistant":
                messages.append({"role": "assistant", "content": content})
    
    # Add the current user message
    messages.append({"role": "user", "content": prompt})
    
    try:
        # Make the API call
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=4096,
            temperature=0.7
        )
        
        # Extract the response text (adapt to your provider's response format)
        return response.choices[0].message.content
        
    except Exception as e:
        # Handle any errors
        return f"Error generating response: {str(e)}"
```

### 4. Implement the `get_capabilities()` Method

```python
def get_capabilities(self) -> List[str]:
    """Return the capabilities of the MyLLM model."""
    return [
        "text_generation",
        "code_analysis", 
        "security_assessment",
        "configuration_review"
    ]
```

## Advanced Features

### Dynamic Model Selection

You can implement dynamic model selection based on task complexity, similar to the Claude plugin:

```python
class MyLLMPlugin(LLMPlugin):
    def __init__(self):
        super().__init__()
        self.default_model = os.getenv("MY_LLM_DEFAULT_MODEL", "my-basic-model")
        self.advanced_model = os.getenv("MY_LLM_ADVANCED_MODEL", "my-advanced-model")
        self.advanced_task_patterns = [
            r"(?i)evaluat(e|ing|ion)",
            r"(?i)analy(ze|sis|zing)",
            r"(?i)secur(e|ity) (audit|assessment)",
            r"(?i)comprehensive",
            r"(?i)detailed (review|analysis|report)"
        ]
    
    def _select_model(self, prompt: str, force_advanced: bool = False) -> str:
        """Select appropriate model based on task complexity."""
        if force_advanced:
            return self.advanced_model
            
        # Check if any advanced task patterns match the prompt
        import re
        for pattern in self.advanced_task_patterns:
            if re.search(pattern, prompt):
                return self.advanced_model
                
        # Default to basic model for regular conversation
        return self.default_model
    
    def generate_response(self, prompt: str, context: Optional[List[Dict[str, str]]] = None, force_advanced: bool = False) -> str:
        # Select model dynamically
        selected_model = self._select_model(prompt, force_advanced)
        self.last_used_model = selected_model
        
        # Use selected_model in API call
        response = self.client.chat.completions.create(
            model=selected_model,
            messages=messages,
            # ... other parameters
        )
        # ... rest of implementation
```

### Error Handling and Retry Logic

Implement robust error handling:

```python
import time
import random

def generate_response(self, prompt: str, context: Optional[List[Dict[str, str]]] = None, force_advanced: bool = False) -> str:
    max_retries = 3
    base_delay = 1
    
    for attempt in range(max_retries):
        try:
            # Your API call here
            response = self.client.chat.completions.create(...)
            return response.choices[0].message.content
            
        except Exception as e:
            if attempt == max_retries - 1:
                return f"Error generating response after {max_retries} attempts: {str(e)}"
            
            # Exponential backoff with jitter
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            time.sleep(delay)
    
    return "Maximum retry attempts exceeded"
```

## Configuration and Environment Variables

### Environment Variables

Define the environment variables your plugin needs:

```bash
# .env file
MY_LLM_API_KEY=your-api-key-here
MY_LLM_DEFAULT_MODEL=my-basic-model
MY_LLM_ADVANCED_MODEL=my-advanced-model
MY_LLM_TIMEOUT=30
```

### Plugin Selection

Set your plugin as the active LLM provider:

```bash
# .env file
LLM_TYPE=MyLLMPlugin  # Case-insensitive, matches class name
```

## Plugin Registration

### Automatic Discovery

The plugin will be automatically discovered if:
1. It's placed in the `argos/plugins/` directory
2. The class inherits from `LLMPlugin`
3. The class name ends with "Plugin" (recommended)


## Contributing

When contributing a new LLM plugin to the Jano project:

1. Follow the coding standards and structure outlined above
2. Include comprehensive error handling
3. Add appropriate documentation and comments

5. Update the main README with information about your provider

## Support

For questions about plugin development, please:
1. Check existing plugins (Claude, OpenAI) for reference
2. Review the `PluginManager` source code
3. Open an issue on the Jano GitHub repository