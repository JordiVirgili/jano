# Argos

## Overview
Argos is a security configuration analysis module within the Jano project. Named after the mythological giant with a hundred eyes, Argos constantly monitors and supervises system configurations to ensure security compliance and best practices.

## Features
- **Configuration Analysis**: Scans and analyzes service configurations to identify security issues
- **Automatic Service Detection**: Identifies running services on the system
- **Security Recommendations**: Provides actionable recommendations to improve security posture
- **Plugin Architecture**: Extensible design allows adding support for additional services

## Installation
Argos is part of the Jano project. To set up Argos:

1. Ensure you're in the Argos directory of the Jano project
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and configure your environment variables:
   ```bash
   cp .env.example .env
   ```
4. Edit `.env` with your specific configuration settings
5. Execute argos (as it is a standalone package):
   ```bash
   python -m argos
   ```

## Usage
Argos provides a RESTful API for interacting with its functionality:

### API Endpoints
- `POST /api/argos/scan`: Triggers a security configuration scan of the specified service
- `GET /api/tasks/`: Lists all security analysis tasks
- `GET /api/tasks/{task_id}`: Retrieves detailed information about a specific task
- `GET /api/tasks/{task_id}/processes`: Gets all processes associated with a task

### API Authentication
Argos uses HTTP Basic authentication. Provide the username and password set in your `.env` file when making API requests:

```bash
   curl -X POST "http://localhost:8000/api/argos/scan?service_name=nginx" \
        -H "accept: application/json" \
        -u "username:password"
```

## Database
Argos uses SQLAlchemy ORM to interact with its database. It supports:
- SQLite (default for development)
- PostgreSQL (recommended for production)

Configure the database connection in the `.env` file.

## Development
To extend Argos with new service analyzers:

1. Create a new plugin in the `argos/plugins` directory
2. Implement the required plugin interface
3. Register the plugin in the plugin registry

Example plugin structure:
```python
from argos.core.plugins import AnalyzerPlugin

class NginxAnalyzer(AnalyzerPlugin):
    def analyze(self, configuration):
        # Implementation for analyzing Nginx configurations
        pass
```

## License
This project is licensed under the Mozilla Public License 2.0 (MPL-2.0) - see the LICENSE file for details.
