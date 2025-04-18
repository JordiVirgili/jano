import uuid
from fastapi import APIRouter, Depends, HTTPException
from argos.database import get_db
from argos.database.repository import ChatSessionRepository, ChatMessageRepository
import argos.models.schemas as schemas
from sqlalchemy.orm import Session
from typing import List

router = APIRouter(
    prefix="/api/v1/chat",
    tags=["chat"]
)

chat_session_repo = ChatSessionRepository()
chat_message_repo = ChatMessageRepository()

# Endpoints for chat
@router.post("/query", response_model=schemas.ChatResponse)
def chat_query(query: schemas.ChatQuery, db: Session = Depends(get_db)):
    """Process a user query and return a response."""
    # Generate a session_id if not provided
    session_id = query.session_id or str(uuid.uuid4())

    # Get or create the session
    chat_session = chat_session_repo.get_or_create_session(db, session_id)

    # Save the user message
    chat_message_repo.add_message(db, chat_session.id, "user", query.message)

    # Here the query would be processed with the LLM to get a response
    # This is a placeholder, the real implementation would depend on the LLM used
    response = "This is an example response. In the real implementation, the LLM response would go here."

    # Save the system response
    chat_message_repo.add_message(db, chat_session.id, "system", response)

    return {"response": response, "session_id": session_id}


@router.get("/sessions", response_model=List[schemas.ChatSessionInDB])
def get_chat_sessions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get the list of all chat sessions."""
    return chat_session_repo.get_all(db)[skip: skip + limit]


@router.get("/sessions/{session_id}", response_model=schemas.ChatSessionWithMessages)
def get_chat_session(session_id: str, db: Session = Depends(get_db)):
    """Get details of a specific chat session including its messages."""
    session = chat_session_repo.get_by_session_id(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return session


@router.delete("/sessions/{session_id}")
def delete_chat_session(session_id: str, db: Session = Depends(get_db)):
    """Delete a chat session."""
    session = chat_session_repo.get_by_session_id(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Chat session not found")

    success = chat_session_repo.delete(db, session.id)
    if not success:
        raise HTTPException(status_code=500, detail="Error deleting chat session")

    return {"detail": "Chat session successfully deleted"}
