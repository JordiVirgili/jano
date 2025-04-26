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
API_URL = os.getenv("JANO_API_URL", "http://localhost:8005/api/v1")  # Argos API
ERIS_API_URL = os.getenv("ERIS_API_URL", "http://localhost:8006/api/v1")  # Eris API
API_USERNAME = os.getenv("JANO_API_USERNAME", "admin")
API_PASSWORD = os.getenv("JANO_API_PASSWORD", "secure_password_here")


# Basic configuration for API requests
def get_auth_header():
    credentials = f"{API_USERNAME}:{API_PASSWORD}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    return {"Authorization": f"Basic {encoded_credentials}"}


# Helper functions for API calls
def api_get(endpoint: str, eris_api: bool = False):
    try:
        base_url = ERIS_API_URL if eris_api else API_URL
        response = requests.get(f"{base_url}/{endpoint}", headers=get_auth_header())
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None


def api_post(endpoint: str, data: Dict[str, Any] = None, eris_api: bool = False):
    try:
        base_url = ERIS_API_URL if eris_api else API_URL
        full_url = f"{base_url}/{endpoint}"
        print(f"Making POST request to: {full_url}")

        headers = {**get_auth_header(), "Content-Type": "application/json"}
        response = requests.post(full_url, json=data if data else {}, headers=headers)

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
        error_msg = f"Connection error: Could not connect to API at {full_url}. Is the server running?"
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

        # Add response to display
        assistant_message = {"role": "assistant", "content": response["message"], "commands": response["commands"],
                             "timestamp": datetime.now().isoformat()}
        st.session_state.messages.append(assistant_message)

        return response
    except Exception as e:
        print(f"Error in send_message: {str(e)}")
        return {"response": f"Error: {str(e)}"}


# Eris functions
def get_eris_plugins():
    """Get the list of available Eris attack plugins."""
    return api_get("eris/plugins", eris_api=True)


def format_attack_results(plugin_name: str, target: str, result: Dict[str, Any]) -> str:
    """Format the attack results into a readable message."""
    message = f"## Eris Security Test Results\n\n"
    message += f"**Plugin:** {plugin_name}\n"
    message += f"**Target:** {target}\n\n"

    # Add success status if available
    if "success" in result:
        status = "✅ Successful" if result["success"] else "❌ Failed"
        message += f"**Status:** {status}\n"

    # Add severity if available
    if "severity" in result:
        severity = result["severity"].upper()
        message += f"**Severity:** {severity}\n"

    # Add main details
    if "details" in result:
        message += f"\n### Details\n{result['details']}\n\n"

    # Add recommendations if available
    if "recommendations" in result and result["recommendations"]:
        message += "### Recommendations\n"
        for i, rec in enumerate(result["recommendations"], 1):
            message += f"{i}. {rec}\n"
        message += "\n"

    # Add extended details if available
    if "details_extended" in result and result["details_extended"]:
        message += "### Extended Details\n"

        # Handle successful credentials
        if "successful_credentials" in result["details_extended"]:
            creds = result["details_extended"]["successful_credentials"]
            message += f"**Successful Login:** Username '{creds.get('username')}' with password '{creds.get('password')}'\n\n"

        # Handle attempts info
        if "attempts" in result["details_extended"]:
            message += f"**Total Attempts:** {result['details_extended']['attempts']}\n\n"

        # Handle attempted combinations
        if "attempted_combinations" in result["details_extended"]:
            message += "**Attempted Combinations:**\n```\n"
            for combo in result["details_extended"]["attempted_combinations"]:
                message += f"Username: {combo.get('username')}, Password: {combo.get('password')}\n"
            message += "```\n"

    return message


def run_command(command: str) -> str:
    """Execute a shell command and return its output."""
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error executing command: {e.stderr}"


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

    # Add Eris plugins to session state
    if "eris_plugins" not in st.session_state:
        plugins_response = get_eris_plugins()
        if plugins_response and "plugins" in plugins_response:
            st.session_state.eris_plugins = plugins_response["plugins"]
        else:
            st.session_state.eris_plugins = []


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
        return dt.strftime("%d/%m/%y %H:%M")
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

        # Eris Attack section (only shown when a session is active)
        if st.session_state.current_session_id:
            st.subheader("Eris Security Tests")

            # Refresh Eris plugins
            if st.button("Refresh Eris Plugins", key="refresh_eris"):
                plugins_response = get_eris_plugins()
                if plugins_response and "plugins" in plugins_response:
                    st.session_state.eris_plugins = plugins_response["plugins"]
                    st.success(f"Found {len(st.session_state.eris_plugins)} plugins")
                else:
                    st.error("Failed to load Eris plugins")

            # Eris attack form
            with st.form(key="eris_attack_form"):
                st.markdown("### Run Security Test")

                # Plugin selection
                plugin_options = []
                for plugin in st.session_state.eris_plugins:
                    plugin_options.append(plugin["name"])

                selected_plugin = st.selectbox("Select Plugin", options=plugin_options, key="eris_plugin")

                # Target input
                target = st.text_input("Target (hostname, IP, or service)", key="eris_target")

                # Submit button
                eris_submit = st.form_submit_button("Run Test")

                if eris_submit and selected_plugin and target:
                    if st.session_state.current_session_id:
                        with st.spinner(f"Running {selected_plugin} attack on {target}..."):
                            # Call the Eris attack endpoint
                            attack_result = api_post(f"eris/attack/{selected_plugin}?target={target}",
                                                     eris_api=True)

                            if attack_result and "result" in attack_result:
                                # Format the attack results
                                formatted_results = format_attack_results(selected_plugin, target,
                                                                          attack_result["result"])

                                # Add a user message showing the attack request
                                user_message = {"role": "user",
                                                "content": f"Run Eris security test: {selected_plugin} on {target}",
                                                "timestamp": datetime.now().isoformat()}
                                st.session_state.messages.append(user_message)

                                # Send to conversation to maintain context in the LLM
                                send_message(formatted_results, st.session_state.current_session_id,
                                             force_advanced=True)

                                # Refresh the conversation
                                load_session(st.session_state.current_session_id)
                                st.rerun()
                            else:
                                st.error(f"Failed to run attack: {attack_result}")
                    else:
                        st.error("Please start or select a chat session first")

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

    # Don't display system messages in the chat UI
    if message["role"] == "system":
        return

    # Get message ID to use in keys
    message_id = message.get("id", str(hash(message.get("content", ""))))

    # Sanitize content to prevent raw HTML display
    content = message.get('content', '')
    if not is_user:
        # Escape HTML tags for display in assistant messages
        content = content.replace("<", "&lt;").replace(">", "&gt;")

    message_div = f"""
    <div style="display: flex; flex-direction: {'row-reverse' if is_user else 'row'}; margin-bottom: 10px;">
        <div style="background-color: {'#241a3d' if is_user else '#1a363d'}; 
                    color: white;
                    padding: 10px; 
                    border-radius: 10px; 
                    max-width: 80%; 
                    box-shadow: 0 1px 2px rgba(0,0,0,0.1);">
            <p style="margin: 0; white-space: pre-wrap;">{content}</p>
            <p style="margin: 0; font-size: 0.7em; color: #888; text-align: right;">
                {format_timestamp(message.get('timestamp', ''))}
            </p>
        </div>
    </div>
    """
    st.markdown(message_div, unsafe_allow_html=True)

    # Extract and display command buttons for assistant messages
    if message["role"] == "assistant":
        # Check if we have commands from API response
        if isinstance(message, dict) and "commands" in message and message["commands"]:
            commands = message["commands"]
            if commands:
                st.markdown("### Suggested commands:")

                # Create a container with a distinct style for commands
                with st.container():
                    # Use columns to display multiple commands side by side
                    cols = st.columns(1)
                    for i, cmd in enumerate(commands):
                        col_index = i % len(cols)
                        with cols[col_index]:
                            cmd_clean = clean_command(cmd)
                            # Create a unique key using the message ID and command index
                            unique_key = f"cmd_{message_id}_{i}"
                            if st.button(f"🖥️ {cmd_clean}", key=unique_key, help="Click to execute command"):
                                # Execute command
                                with st.spinner(f"Executing: {cmd_clean}..."):
                                    result = run_command(cmd_clean)

                                # Format the result to escape HTML
                                safe_result = result.replace("<", "&lt;").replace(">", "&gt;")

                                st.session_state.messages.append(
                                    {"role": "user", "content": f"Command: {cmd_clean}\nResult: {result}",
                                     "timestamp": datetime.now().isoformat()})

                                # Send the result to the API to maintain context
                                if st.session_state.current_session_id:
                                    send_message(f"Command: {cmd_clean}\nResult:\n {result}",
                                                 st.session_state.current_session_id)

                                # Use standard rerun method in current Streamlit versions
                                st.rerun()

        # Also try to extract commands from code blocks if not already provided
        elif isinstance(message, dict) and "commands" not in message:
            # Extract commands from markdown code blocks in the message content
            content = message.get('content', '')
            code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', content, re.DOTALL)

            if code_blocks:
                commands = []
                for block in code_blocks:
                    # Split block into lines and add each non-empty line as a command
                    lines = [line.strip() for line in block.strip().splitlines() if line.strip()]
                    commands.extend(lines)

                if commands:
                    st.markdown("### Detected commands:")

                    with st.container():
                        cols = st.columns(1)
                        for i, cmd in enumerate(commands):
                            col_index = i % len(cols)
                            with cols[col_index]:
                                cmd_clean = clean_command(cmd)
                                # Create a unique key using the message ID and command index
                                unique_key = f"detected_{message_id}_{i}"
                                if st.button(f"🖥️ {cmd_clean}", key=unique_key, help="Click to execute command"):
                                    with st.spinner(f"Executing: {cmd_clean}..."):
                                        result = run_command(cmd_clean)

                                    # Format the result to escape HTML
                                    safe_result = result.replace("<", "&lt;").replace(">", "&gt;")

                                    st.session_state.messages.append(
                                        {"role": "user", "content": f"Command: {cmd_clean}\nResult: {result}",
                                         "timestamp": datetime.now().isoformat()})

                                    if st.session_state.current_session_id:
                                        send_message(f"Command: {cmd_clean}\nResult: {result}",
                                                     st.session_state.current_session_id)

                                    # Use standard rerun method in current Streamlit versions
                                    st.rerun()

        # Also try to extract commands from code blocks if not already provided
        elif isinstance(message, dict) and "commands" not in message:
            # Extract commands from markdown code blocks in the message content
            content = message.get('content', '')
            code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', content, re.DOTALL)

            if code_blocks:
                commands = []
                for block in code_blocks:
                    # Split block into lines and add each non-empty line as a command
                    lines = [line.strip() for line in block.strip().splitlines() if line.strip()]
                    commands.extend(lines)

                if commands:
                    st.markdown("### Detected commands:")

                    with st.container():
                        cols = st.columns(1)
                        for i, cmd in enumerate(commands):
                            col_index = i % len(cols)
                            with cols[col_index]:
                                cmd_clean = clean_command(cmd)
                                # Create a unique key using the message ID and command index
                                unique_key = f"detected_{message_id}_{i}"
                                if st.button(f"🖥️ {cmd_clean}", key=unique_key, help="Click to execute command"):
                                    with st.spinner(f"Executing: {cmd_clean}..."):
                                        result = run_command(cmd_clean)

                                    st.session_state.messages.append(
                                        {"role": "user", "content": f"Command: {cmd_clean}\nResult: {result}",
                                         "timestamp": datetime.now().isoformat()})

                                    if st.session_state.current_session_id:
                                        send_message(f"Comand: {cmd_clean}\nResult: {result}",
                                                     st.session_state.current_session_id)

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

            # Rerun to update the UI with new messages
            st.rerun()


if __name__ == "__main__":
    main()