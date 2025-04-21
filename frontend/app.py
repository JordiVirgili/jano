import streamlit as st
import requests
import uuid
import json
import base64
import subprocess
import os
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API configuration
API_URL = os.getenv("JANO_API_URL", "http://localhost:8005/api/v1")  # Can be overridden in .env file
API_USERNAME = os.getenv("JANO_API_USERNAME", "admin")
API_PASSWORD = os.getenv("JANO_API_PASSWORD", "secure_password_here")


# Basic configuration for API requests
def get_auth_header():
    credentials = f"{API_USERNAME}:{API_PASSWORD}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    return {"Authorization": f"Basic {encoded_credentials}"}


# Helper functions for API calls
def api_get(endpoint: str):
    try:
        response = requests.get(f"{API_URL}/{endpoint}", headers=get_auth_header())
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None


def api_post(endpoint: str, data: Dict[str, Any]):
    try:
        full_url = f"{API_URL}/{endpoint}"
        print(f"Making POST request to: {full_url}")

        headers = {**get_auth_header(), "Content-Type": "application/json"}
        response = requests.post(full_url, json=data, headers=headers)

        # Print response status for debugging
        print(f"Response status code: {response.status_code}")

        # Check for error status codes
        response.raise_for_status()

        # Try to parse JSON
        try:
            return response.json()
        except ValueError:
            print(f"Invalid JSON response: {response.text[:200]}...")
            return {"response": "Error: Invalid JSON response from API"}

    except requests.exceptions.ConnectionError as e:
        error_msg = f"Connection error: Could not connect to API at {API_URL}. Is the server running?"
        print(error_msg)
        st.error(error_msg)
        return {"response": error_msg}
    except requests.exceptions.Timeout as e:
        error_msg = "Timeout error: The API request timed out."
        print(error_msg)
        st.error(error_msg)
        return {"response": error_msg}
    except requests.exceptions.HTTPError as e:
        error_msg = f"HTTP error: {e} - Response: {e.response.text[:200] if hasattr(e, 'response') else 'No response'}"
        print(error_msg)
        st.error(error_msg)
        return {"response": error_msg}
    except Exception as e:
        error_msg = f"API Error: {str(e)}"
        print(error_msg)
        st.error(error_msg)
        return {"response": error_msg}


def api_delete(endpoint: str):
    try:
        response = requests.delete(f"{API_URL}/{endpoint}", headers=get_auth_header())
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None


# Session management functions
def get_chat_sessions():
    return api_get("chat/sessions")


def get_chat_history(session_id: str):
    return api_get(f"chat/history/{session_id}")


def create_new_session():
    result = api_post("chat/new", {})
    if result:
        return result.get("session_id")
    return None


def delete_session(session_id: str):
    return api_delete(f"chat/sessions/{session_id}")


def send_message(message: str, session_id: str, force_advanced: bool = False):
    try:
        data = {"message": message, "session_id": session_id, "force_advanced": force_advanced}
        response = api_post("chat/query", data)

        # Verify that the response has the expected structure
        if response is None:
            print("API returned None response")
            return None

        if "message" not in response:
            print(f"Unexpected API response format: {response}")
            return {"response": "Error: Unexpected response format from API"}

        return response
    except Exception as e:
        print(f"Error in send_message: {str(e)}")
        return {"response": f"Error: {str(e)}"}


def run_command(command: str) -> str:
    """Execute a shell command and return its output."""
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error executing command: {e.stderr}"


def extract_commands(text: str) -> List[str]:
    """Extract commands from text using a regex pattern for /command format."""
    # Pattern to match commands like /scan, /attack etc.
    pattern = r'/([a-zA-Z_]+)(?:\s+([^\n]+))?'
    matches = re.findall(pattern, text)
    commands = []

    for match in matches:
        cmd, args = match
        if args:
            commands.append(f"/{cmd} {args}")
        else:
            commands.append(f"/{cmd}")

    return commands


def clean_command(cmd: str) -> str:
    """Clean command string from API response format."""
    # Remove language identifier if present (like 'bash\n')
    if '\n' in cmd:
        parts = cmd.split('\n', 1)
        # If first part looks like a language identifier, remove it
        if len(parts[0]) < 10:  # Arbitrary length limit for language identifier
            cmd = parts[1]

    # Trim whitespace
    cmd = cmd.strip()

    return cmd


def initialize_session_state():
    """Initialize session state variables if they don't exist."""
    if "chat_sessions" not in st.session_state:
        st.session_state.chat_sessions = []

    if "current_session_id" not in st.session_state:
        st.session_state.current_session_id = None

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "commands" not in st.session_state:
        st.session_state.commands = []


def refresh_sessions():
    """Refresh the list of available chat sessions."""
    sessions = get_chat_sessions()
    if sessions:
        st.session_state.chat_sessions = sessions
    else:
        st.session_state.chat_sessions = []


def load_session(session_id: str):
    """Load messages from a specific session."""
    history = get_chat_history(session_id)
    if history:
        st.session_state.messages = history
        st.session_state.current_session_id = session_id
    else:
        st.error("Failed to load chat history")


def format_timestamp(timestamp_str: str) -> str:
    """Format ISO timestamp string to a user-friendly format."""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime("%H:%M:%S")
    except:
        return ""


def sidebar_ui():
    """Create the sidebar UI with session management controls."""
    with st.sidebar:
        st.title("Jano Security Assistant")

        # New chat button
        if st.button("New Chat", key="new_chat"):
            new_session_id = create_new_session()
            if new_session_id:
                st.session_state.current_session_id = new_session_id
                st.session_state.messages = []
                refresh_sessions()
                st.rerun()

        # Refresh sessions button
        if st.button("Refresh Sessions", key="refresh"):
            refresh_sessions()

        # Display available sessions
        st.subheader("Available Sessions")

        if not st.session_state.chat_sessions:
            st.info("No sessions available")
        else:
            for session in st.session_state.chat_sessions:
                col1, col2 = st.columns([3, 1])
                timestamp = format_timestamp(session.get("created_at", ""))
                with col1:
                    if st.button(f"Session {session['id']} ({timestamp})", key=f"session_{session['id']}"):
                        load_session(session["session_id"])
                        st.rerun()

                with col2:
                    if st.button("🗑️", key=f"delete_{session['id']}"):
                        if delete_session(session["session_id"]):
                            if session["session_id"] == st.session_state.current_session_id:
                                st.session_state.current_session_id = None
                                st.session_state.messages = []
                            refresh_sessions()
                            st.rerun()


def display_message(message):
    """Display a single message in the chat UI."""
    is_user = message["role"] == "user"
    message_div = f"""
    <div style="display: flex; flex-direction: {'row-reverse' if is_user else 'row'}; margin-bottom: 10px;">
        <div style="background-color: {'#241a3d' if is_user else '#1a363d'}; 
                    padding: 10px; 
                    border-radius: 10px; 
                    max-width: 80%; 
                    box-shadow: 0 1px 2px rgba(0,0,0,0.1);">
            <p style="margin: 0; white-space: pre-wrap;">{message['content']}</p>
            <p style="margin: 0; font-size: 0.7em; color: #888; text-align: right;">
                {format_timestamp(message.get('timestamp', ''))}
            </p>
        </div>
    </div>
    """
    st.markdown(message_div, unsafe_allow_html=True)

    # Extract and display command buttons for assistant messages
    if message["role"] == "assistant":
        commands = extract_commands(message["content"])
        if commands:
            cols = st.columns(min(len(commands), 4))
            for i, cmd in enumerate(commands):
                col_index = i % len(cols)
                if cols[col_index].button(cmd, key=f"cmd_{cmd}_{i}"):
                    # Execute command
                    actual_cmd = cmd[1:]  # Remove the leading slash

                    # Show a spinner while executing
                    with st.spinner(f"Executing {cmd}..."):
                        result = run_command(actual_cmd)

                    # Add the command and its result to the chat
                    st.session_state.messages.append({"role": "user", "content": f"Executed command: {cmd}",
                        "timestamp": datetime.now().isoformat()})

                    st.session_state.messages.append(
                        {"role": "assistant", "content": f"Command result:\n```\n{result}\n```",
                            "timestamp": datetime.now().isoformat()})

                    # Send the result to the API to maintain context
                    if st.session_state.current_session_id:
                        send_message(f"Command executed: {cmd}\nResult: {result}", st.session_state.current_session_id)

                    st.rerun()


def main():
    """Main application function."""
    st.set_page_config(page_title="Jano Security Assistant", layout="wide")

    # Initialize session state
    initialize_session_state()

    # Create sidebar
    sidebar_ui()

    # Main chat area
    if not st.session_state.current_session_id:
        # Welcome screen when no session is active
        st.title("Welcome to Jano Security Assistant")
        st.write("Start a new chat or select an existing session from the sidebar.")

        st.markdown("""
        ## About Jano

        Jano is an AI-powered security configuration assistant that helps you:

        - Analyze service configurations for security issues
        - Generate secure configuration files for various services
        - Test configurations for vulnerabilities
        - Provide actionable security recommendations

        Use the sidebar to start a new conversation or continue an existing one.
        """)
    else:
        # Chat interface
        st.title("Chat")

        # Display messages
        for message in st.session_state.messages:
            display_message(message)

        # Message input
        with st.form(key="message_form", clear_on_submit=True):
            user_input = st.text_area("Type your message:", height=100, key="user_input")
            col1, col2, col3 = st.columns([1, 1, 4])

            with col1:
                submit = st.form_submit_button("Send")

            with col2:
                use_advanced = st.checkbox("Use advanced model", value=False)

        if submit and user_input:
            # Add user message to display
            user_message = {"role": "user", "content": user_input, "timestamp": datetime.now().isoformat()}
            st.session_state.messages.append(user_message)

            # Send to API
            with st.spinner("Thinking..."):
                response = send_message(user_input, st.session_state.current_session_id, use_advanced)

            if response:
                # Add response to display
                assistant_message = {"role": "assistant", "content": response["message"],
                    "timestamp": datetime.now().isoformat()}
                st.session_state.messages.append(assistant_message)

                # Extract commands for easy access
                st.session_state.commands = extract_commands(response["message"])

            # Rerun to update the UI with new messages
            st.rerun()


if __name__ == "__main__":
    main()