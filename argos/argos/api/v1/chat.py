import uuid
from fastapi import APIRouter, Depends, HTTPException
from argos.database import get_db
from argos.database.repository import ChatSessionRepository, ChatMessageRepository
import argos.models.schemas as schemas
from sqlalchemy.orm import Session
from typing import List
from argos.services import ChatService

router = APIRouter(
    prefix="/api/v1/chat",
    tags=["chat"]
)

# Initialize repositories
chat_session_repo = ChatSessionRepository()
chat_message_repo = ChatMessageRepository()


# Initialize service
chat_service = ChatService(chat_session_repo, chat_message_repo)


@router.post("/query", response_model=schemas.ChatResponse)
def process_chat_query(query: schemas.EnhancedChatQuery, db: Session = Depends(get_db)):
    """
    Process a user query and return an AI-generated response using Claude.

    The system automatically selects between Claude 3.5 (regular conversations)
    and Claude 3.7 (complex security tasks) based on the query content.

    You can force the use of Claude 3.7 by setting force_advanced=true.
    """
    try:
        result = chat_service.process_query(db, query.message, query.session_id, force_advanced=query.force_advanced)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat query: {str(e)}")


@router.get("/sessions", response_model=List[schemas.ChatSessionInDB])
def get_chat_sessions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all chat sessions."""
    return chat_session_repo.get_all(db)[skip:skip + limit]


@router.get("/sessions/{session_id}", response_model=schemas.ChatSessionWithMessages)
def get_chat_session(session_id: str, db: Session = Depends(get_db)):
    """Get details of a specific chat session including all messages."""
    session = chat_session_repo.get_by_session_id(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return session


@router.get("/history/{session_id}")
def get_chat_history(session_id: str, db: Session = Depends(get_db)):
    """
    Get the conversation history for a specific session.

    Returns a formatted list of messages with role, content, and timestamp.
    """
    messages = chat_service.get_chat_history(db, session_id)
    if not messages and not chat_session_repo.get_by_session_id(db, session_id):
        raise HTTPException(status_code=404, detail="Chat session not found")
    return messages


@router.delete("/sessions/{session_id}")
def delete_chat_session(session_id: str, db: Session = Depends(get_db)):
    """Delete a chat session and all its messages."""
    success = chat_service.clear_chat_history(db, session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return {"detail": "Chat session successfully deleted"}


@router.post("/new")
def create_new_chat(db: Session = Depends(get_db)):
    """Create a new chat session and return its ID."""
    session_id = str(uuid.uuid4())
    session = chat_session_repo.get_or_create_session(db, session_id)
    return {"session_id": session_id}
