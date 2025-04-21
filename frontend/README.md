# Jano Streamlit Frontend

This is a Streamlit-based frontend for the Jano security configuration assistant. It provides a user-friendly interface to interact with the Jano backend API.

## Features

- Chat-based interface for interacting with Jano's AI assistant
- Session management (create, load, delete conversations)
- Command detection and execution
- Option to toggle between regular and advanced LLM models
- Real-time display of chat history

## Installation

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file with your configuration:
   ```bash
   cp .env.example .env
   ```
   
3. Edit the `.env` file with your specific settings:
   ```
   JANO_API_URL=http://localhost:8005/api/v1
   JANO_API_USERNAME=admin
   JANO_API_PASSWORD=secure_password_here
   ```

## Usage

1. Make sure the Jano backend API is running (default port 8005)

2. Run the Streamlit application:
   ```bash
   streamlit run app.py
   ```

3. Open your browser at http://localhost:8501 to access the application

## Configuration

You can modify the following in the script:
- `API_URL`: Set this to the address where your Jano backend is running
- `API_USERNAME` and `API_PASSWORD`: Update these with your Jano API credentials

## Functionality

### Initial Screen
The initial screen presents:
- A welcome message
- A sidebar with options to create a new chat or select an existing one

### Chat Interface
The chat interface includes:
- A message area displaying the conversation history
- A text input area for typing new messages
- A "Send" button to submit messages
- A checkbox to toggle between regular and advanced LLM models
- Automatically detected command buttons that execute shell commands when clicked

### Command Execution
When the assistant suggests commands (prefixed with "/"), they will appear as clickable buttons. Clicking a button will:
1. Execute the command in a terminal
2. Display the command output in the chat
3. Send the output back to the assistant for context

## Troubleshooting

If you encounter API connection issues:
1. Verify that the Jano backend is running
2. Check that the API URL is correct in the script
3. Ensure your authentication credentials are valid
4. Examine browser network logs for more specific error information