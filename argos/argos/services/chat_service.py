from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import os
import logging
import re

from argos.database import ChatSessionRepository, ChatMessageRepository
from argos.core import PluginManager
from argos.services.fixer_service import fixer_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChatService:
    """Service for handling chat functionality with dynamic model selection."""

    def __init__(self, session_repo: ChatSessionRepository, message_repo: ChatMessageRepository):
        """Initialize the chat service with repositories."""
        self.session_repo = session_repo
        self.message_repo = message_repo
        self.plugin_manager = PluginManager()
        self.plugin_manager.discover_plugins()
        self.llm_plugin = self._load_llm_plugin()

    def _load_llm_plugin(self):
        """Load the LLM plugin based on the configuration."""
        llm_type = os.getenv("LLM_TYPE", "claudeplugin").lower()

        try:
            # Create plugin configuration from custom variables
            config = {}

            # Get the plugin instance
            plugin = self.plugin_manager.get_plugin(llm_type, config)

            if not plugin:
                available_plugins = self.plugin_manager.discover_plugins()
                logger.error(f"Plugin '{llm_type}' not available. Available plugins: {available_plugins}")
                # Fall back to first available plugin if requested one is not found
                if available_plugins:
                    fallback_plugin = available_plugins[0]
                    logger.warning(f"Falling back to plugin '{fallback_plugin}'")
                    plugin = self.plugin_manager.get_plugin(fallback_plugin, config)

            if not plugin:
                raise ValueError(f"No LLM plugins available")

            return plugin

        except Exception as e:
            logger.error(f"Error loading LLM plugin: {str(e)}")
            raise

    def process_query(self, db: Session, message: str, session_id: Optional[str] = None,
                      force_advanced: bool = False) -> Dict[str, Any]:
        """
        Process a user message and generate a response.

        Args:
            db: The database session
            message: The user's message
            session_id: Optional session ID for continuing a conversation
            force_advanced: If True, forces the use of the advanced model

        Returns:
            Dict containing the response and session_id
        """
        # Get or create session
        chat_session = self.session_repo.get_or_create_session(db, session_id)

        # Save user message
        self.message_repo.add_message(db, chat_session.id, "user", message)

        # Retrieve conversation history
        messages = self.message_repo.get_by_session_id(db, chat_session.id)

        # Format messages for the LLM
        formatted_history = [{"role": msg.role, "content": msg.content} for msg in messages if
                             msg.role in ["system", "user", "assistant"]  # Ensure only valid roles are included
                             ]

        # Check if the message is a request to fix a configuration
        fix_command_pattern = r"^fix\s+([a-zA-Z0-9_\-]+)(?:\s+(.+))?$"
        match = re.match(fix_command_pattern, message.lower().strip())

        if match:
            if 'help command' in message.lower().strip():
                plugins = fixer_service.get_supported_services()
                all_services = [service for services in plugins.values() for service in services]
                services_list = '\n\n'.join(all_services)
                response_text = f"help() list of available fixers:\n\n{services_list}\n\n"
                self.message_repo.add_message(db, chat_session.id, "assistant", response_text)
                return {"response": response_text, "session_id": chat_session.session_id,
                        "model_used": "Configuration Analyzer"}
            else:
                service_name = match.group(1)
                file_path = match.group(2) if match.group(2) else None

                # Check if we support this service
                supported_services = fixer_service.get_supported_services()
                service_supported = False

                for plugin, services in supported_services.items():
                    if service_name.lower() in [s.lower() for s in services]:
                        service_supported = True
                        break

                if service_supported:
                    # Analyze the configuration
                    analysis_result = fixer_service.analyze_configuration(service_name, file_path)

                    if analysis_result.get("success") and analysis_result.get("issues"):
                        # Generate a response summarizing the issues
                        response_text = f"I found {len(analysis_result['issues'])} security issues in the {service_name} configuration:\n\n"

                        for i, issue in enumerate(analysis_result["issues"], 1):
                            severity = issue.get("severity", "unknown").upper()
                            response_text += f"{i}. [{severity}] {issue.get('description')}\n"
                            if "current" in issue:
                                response_text += f"   Current: {issue.get('current')}\n"
                            response_text += f"   Recommended: {issue.get('fix')}\n\n"

                        response_text += f"Would you like me to automatically fix these issues? Reply with 'yes' to apply all fixes, or specify which ones to apply (e.g., 'fix 1,3')."

                        # Store the analysis result in the session for later use
                        self.message_repo.add_message(db, chat_session.id, "system",
                            f"ANALYSIS_RESULT:{service_name}:{str(analysis_result)}")

                    elif analysis_result.get("success") and not analysis_result.get("issues"):
                        response_text = f"I analyzed the {service_name} configuration and found no security issues. The configuration appears to be secure!"
                    else:
                        response_text = f"I encountered an error while analyzing the {service_name} configuration: {analysis_result.get('message', 'Unknown error')}"

                    # Save the response
                    self.message_repo.add_message(db, chat_session.id, "assistant", response_text)

                    return {"response": response_text, "session_id": chat_session.session_id,
                            "model_used": "Configuration Analyzer"}

        # Check if the message is a confirmation to apply fixes
        if re.match(r"^(yes|y)$", message.lower().strip()):
            # Look for the most recent analysis result in the conversation
            analysis_message = None
            for msg in reversed(messages):
                if msg.role == "system" and msg.content.startswith("ANALYSIS_RESULT:"):
                    analysis_message = msg
                    break

            if analysis_message:
                # Parse the stored analysis result
                parts = analysis_message.content.split(":", 2)
                if len(parts) == 3:
                    service_name = parts[1]

                    # Apply all fixes
                    fix_result = fixer_service.apply_fixes(service_name=service_name, backup=True, restart=False)

                    if fix_result.get("success"):
                        response_text = f"I've successfully applied fixes to the {service_name} configuration:\n\n{fix_result.get('message')}\n\n"
                        response_text += "Would you like me to restart the service to apply these changes? Reply with 'restart' to do so."
                    else:
                        response_text = f"I encountered an error while applying fixes to the {service_name} configuration:\n\n{fix_result.get('message')}"

                    # Save the response
                    self.message_repo.add_message(db, chat_session.id, "assistant", response_text)

                    return {"response": response_text, "session_id": chat_session.session_id,
                            "model_used": "Configuration Fixer"}

        # Check if the message is a specific fix selection
        fix_selection_pattern = r"^fix\s+([0-9,\s]+)$"
        match = re.match(fix_selection_pattern, message.lower().strip())

        if match:
            # Extract the indices of fixes to apply
            indices_str = match.group(1)
            try:
                indices = [int(idx.strip()) - 1 for idx in indices_str.split(",")]  # Convert to 0-based

                # Look for the most recent analysis result
                analysis_message = None
                for msg in reversed(messages):
                    if msg.role == "system" and msg.content.startswith("ANALYSIS_RESULT:"):
                        analysis_message = msg
                        break

                if analysis_message:
                    # Parse the stored analysis result
                    parts = analysis_message.content.split(":", 2)
                    if len(parts) == 3:
                        service_name = parts[1]

                        try:
                            # This is not ideal but works for simple cases - a more robust solution would store the analysis as JSON
                            import ast
                            analysis_result = ast.literal_eval(parts[2])

                            if "issues" in analysis_result and indices:
                                # Filter the issues to apply
                                selected_issues = []
                                for idx in indices:
                                    if 0 <= idx < len(analysis_result["issues"]):
                                        selected_issues.append(analysis_result["issues"][idx])

                                if selected_issues:
                                    # Apply the selected fixes
                                    fix_result = fixer_service.apply_fixes(service_name=service_name,
                                        fixes=selected_issues, backup=True, restart=False)

                                    if fix_result.get("success"):
                                        response_text = f"I've applied the selected fixes to the {service_name} configuration:\n\n{fix_result.get('message')}\n\n"
                                        response_text += "Would you like me to restart the service to apply these changes? Reply with 'restart' to do so."
                                    else:
                                        response_text = f"I encountered an error while applying fixes to the {service_name} configuration:\n\n{fix_result.get('message')}"
                                else:
                                    response_text = "No valid fixes were selected. Please try again with valid indices."
                            else:
                                response_text = "I couldn't find the issues to fix. Please try analyzing the configuration again."
                        except Exception as e:
                            response_text = f"I encountered an error processing your request: {str(e)}"
                    else:
                        response_text = "I couldn't find the analysis result. Please try analyzing the configuration again."
                else:
                    response_text = "I don't have any recent configuration analysis to apply fixes to. Please analyze a configuration first."

                # Save the response
                self.message_repo.add_message(db, chat_session.id, "assistant", response_text)

                return {"response": response_text, "session_id": chat_session.session_id,
                        "model_used": "Configuration Fixer"}
            except ValueError:
                # If we can't parse the indices, fall back to the regular LLM
                pass

        # Check if the message is a request to restart a service
        if re.match(r"^restart$", message.lower().strip()):
            # Look for the most recent analysis result
            analysis_message = None
            for msg in reversed(messages):
                if msg.role == "system" and msg.content.startswith("ANALYSIS_RESULT:"):
                    analysis_message = msg
                    break

            if analysis_message:
                # Parse the stored analysis result
                parts = analysis_message.content.split(":", 2)
                if len(parts) == 3:
                    service_name = parts[1]

                    # Get the appropriate plugin
                    plugin = fixer_service.get_plugin_for_service(service_name)
                    if plugin:
                        # Restart the service
                        success, message = plugin.restart_service(service_name)

                        if success:
                            response_text = f"I've successfully restarted the {service_name} service. The new configuration is now active."
                        else:
                            response_text = f"I encountered an error while restarting the {service_name} service: {message}"
                    else:
                        response_text = f"I couldn't find a plugin to handle the {service_name} service. Please restart it manually."
                else:
                    response_text = "I couldn't determine which service to restart. Please specify the service name."
            else:
                response_text = "I don't have any recent configuration analysis to determine which service to restart. Please specify the service name."

            # Save the response
            self.message_repo.add_message(db, chat_session.id, "assistant", response_text)

            return {"response": response_text, "session_id": chat_session.session_id,
                    "model_used": "Configuration Fixer"}

        # For all other messages, use the LLM plugin
        response_text = self.llm_plugin.generate_response(message, formatted_history, force_advanced)

        # Save the response
        self.message_repo.add_message(db, chat_session.id, "assistant", response_text)

        # Get the model that was used (if the plugin supports reporting this)
        model_used = getattr(self.llm_plugin, 'last_used_model', 'Unknown')

        return {"response": response_text, "session_id": chat_session.session_id, "model_used": model_used}

    def get_chat_history(self, db: Session, session_id: str) -> List[Dict[str, Any]]:
        """
        Get the conversation history for a session.

        Args:
            db: The database session
            session_id: The session ID

        Returns:
            List of message dictionaries
        """
        # Get the chat session
        chat_session = self.session_repo.get_by_session_id(db, session_id)
        if not chat_session:
            return []

        # Get messages for the session
        messages = self.message_repo.get_by_session_id(db, chat_session.id)

        # Format messages
        formatted_messages = [{"id": message.id, "role": message.role, "content": message.content,
                               "timestamp": message.timestamp.isoformat()} for message in messages if
                              message.role != "system"]  # Filter out system messages

        return formatted_messages

    def clear_chat_history(self, db: Session, session_id: str) -> bool:
        """
        Delete all messages for a session.

        Args:
            db: The database session
            session_id: The session ID

        Returns:
            True if successful, False otherwise
        """
        # Get the chat session
        chat_session = self.session_repo.get_by_session_id(db, session_id)
        if not chat_session:
            return False

        # Delete the session (cascade will delete messages)
        return self.session_repo.delete(db, chat_session.id)