from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import os
import logging

from argos.database import ChatSessionRepository, ChatMessageRepository
from argos.core import PluginManager

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

        # Generate response using the LLM plugin
        # The plugin will automatically select the appropriate model based on the message
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
                               "timestamp": message.timestamp.isoformat()} for message in messages]

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