# LLM Plugins for Argos

This directory contains plugins for different Language Learning Models (LLMs) that can be used by the Argos system.

## Available Plugins

- **ClaudePlugin**: Integration with Anthropic's Claude models with automatic model selection based on task complexity
- **OpenAIPlugin**: Integration with OpenAI's GPT models

## Creating New Plugins

To create a new LLM plugin, follow these steps:

1. Create a new Python file in this directory (e.g., `my_custom_llm.py`)
2. Import the LLMPlugin base class: `from argos.core.plugins import LLMPlugin`
3. Create a class that inherits from LLMPlugin and implements all required methods:
   - `initialize(self, config)`: Set up the plugin with configuration parameters
   - `generate_response(self, prompt, context=None)`: Generate a response based on user input
   - `get_capabilities(self)`: Return a list of model capabilities

### Example Plugin Structure

```python
from argos.core.plugins import LLMPlugin

class MyCustomLLM(LLMPlugin):
    def __init__(self):
        # Initialize your plugin
        pass
        
    def initialize(self, config):
        # Configure your plugin based on the provided configuration
        pass
        
    def generate_response(self, prompt, context=None):
        # Generate a response using your custom LLM
        return "Your response here"
        
    def get_capabilities(self):
        # Return capabilities list
        return ["text_generation", "custom_capability"]
```

## Using Plugins

To select which plugin to use, set the `LLM_TYPE` in your `.env` file to the name of the plugin class (case-insensitive). For example:

```
LLM_TYPE=MyCustomLLM
```

The system will automatically discover and load the appropriate plugin from this directory.