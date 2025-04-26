# Eris

## Overview
Eris is the antagonistic security testing module within the Jano project. Named after the goddess of discord, Eris proactively tests security configurations by simulating various attacks, helping identify potential vulnerabilities before they can be exploited.

## Features
- **Plugin-based Attack System**: Easily extensible with new attack plugins
- **Security Testing**: Simulates different attack vectors against services
- **Vulnerability Identification**: Identifies potential security weaknesses
- **Recommendations**: Provides actionable security recommendations
- **RESTful API**: Simple integration with other systems

## Installation
Eris is part of the Jano project. To set up Eris:

1. Ensure you're in the Eris directory of the Jano project
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and configure your environment variables:
   ```bash
   cp .env.example .env
   ```
4. Edit `.env` with your specific configuration settings
5. Execute Eris (as it is a standalone package):
   ```bash
   python -m eris
   ```

## Usage
Eris provides a RESTful API for interacting with its functionality:

### API Endpoints
- `GET /api/v1/eris/plugins`: Lists all available attack plugins
- `POST /api/v1/eris/attack/{plugin_name}`: Executes an attack using the specified plugin

### API Authentication
Eris uses HTTP Basic authentication. Provide the username and password set in your `.env` file when making API requests:

```bash
curl -X POST "http://localhost:8006/api/v1/eris/attack/weaksshplugin?target=192.168.1.1" \
     -H "accept: application/json" \
     -u "username:password"
```

## Extending Eris with New Attacks
To create a new attack plugin:

1. Create a new Python file in the `eris/plugins` directory
2. Implement the `AttackPlugin` interface
3. The plugin will be automatically discovered by the plugin manager

Example plugin structure:
```python
from eris.core.plugins import AttackPlugin

class MyCustomAttackPlugin(AttackPlugin):
    def initialize(self, config):
        # Plugin initialization logic
        pass
        
    def execute_attack(self, target, options=None):
        # Attack implementation
        return {
            "success": True,
            "details": "Vulnerability found",
            "severity": "high",
            "recommendations": ["Fix A", "Fix B"]
        }
        
    def get_capabilities(self):
        return ["custom_attack_vector"]
```

## Warning
This tool is intended for educational and legitimate security testing purposes only. Only use it against systems you own or have explicit permission to test.

## License
This project is licensed under the Mozilla Public License 2.0 (MPL-2.0) - see the LICENSE file for details.