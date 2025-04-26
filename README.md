# Jano

## Overview
Jano is an AI-powered security configuration management system named after the Roman god Janus, who had two faces looking to the past and future. Similarly, Jano provides dual perspectives on system security: proactive supervision and adversarial testing.

## Architecture
Jano consists of two main components:

1. **Argos** - The security supervisor system that monitors, analyzes, and recommends secure configurations
2. **Eris** - The adversarial testing system that simulates attacks to verify configuration robustness

Both components are built on a modular, plugin-based architecture that allows for easy extension and customization.

## Project Structure
```
jano/
├── argos/            # Security supervision system
│   ├── plugins/      # Service-specific analysis plugins
│   └── ...
├── eris/             # Security testing system
│   ├── plugins/      # Service-specific attack plugins
│   └── ...
├── frontend/         # Web interface
└── README.md         # This file
```

## Features
- **Dual Security Perspective**: Both defensive and offensive security capabilities
- **Modular Plugin System**: Easily extensible for different services and technologies
- **LLM Integration**: Leverages large language models for intelligent analysis and testing
- **Configuration Analysis**: Detects security issues in service configurations
- **Vulnerability Testing**: Simulates attacks to verify security posture
- **RESTful API**: Programmatic access to all functionality

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/JordiVirgili/jano
   cd jano
   ```

2. Install dependencies for each component:
   ```bash
   # Install Argos dependencies
   cd argos
   pip install -r requirements.txt
   
   # Install Eris dependencies
   cd ../eris
   pip install -r requirements.txt
   
   # Install frontend dependencies
   cd ../frontend
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   - Copy `.env.example` to `.env` in each component directory
   - Edit the files with your specific settings (API keys, database configuration, etc.)


## Usage
Each component of Jano can be used independently or together:

### Argos (Security Supervisor)
```bash
cd argos
python -m argos
```

### Eris (Security Tester)
```bash
cd eris
python -m eris
```

### Frontend
```bash
cd frontend
streamlit run app.py
```

## API Authentication
Jano uses HTTP Basic authentication. Set your credentials in the `.env` file:
```
JANO_API_USERNAME=admin
JANO_API_PASSWORD=secure_password_here
```

## Development
To extend Jano with new functionality:

1. **Adding Service Support**: Create new plugins in either `argos/plugins/` or `eris/plugins/`
2. **LLM Integration**: Configure additional LLM providers in the `.env` file
3. **Custom Analysis Rules**: Extend the analysis capabilities by implementing new rule sets

## Requirements
- Python 3.11+
- FastAPI
- SQLAlchemy
- Pydantic v2+
- Access to LLM APIs (OpenAI, Anthropic)

## License
This project is licensed under the Mozilla Public License 2.0 (MPL-2.0) - see the LICENSE file for details.

## Author
Jordi Virgili Gomà <jordi@virgili.org>

## Acknowledgments
- This project was developed as part of a Master's Thesis in Cybersecurity and Privacy
