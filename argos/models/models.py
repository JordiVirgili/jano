from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from argos.database import Base


class Task(Base):
    """Represents tasks to be performed by the system."""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    start_date = Column(DateTime, default=datetime.now)
    task_to_perform = Column(String, nullable=False)
    user_prompt = Column(Text, nullable=False)
    result = Column(Text, nullable=True)
    acceptance_date = Column(DateTime, nullable=True)

    # Relationship with processes associated with this task
    processes = relationship("Process", back_populates="task")


class Process(Base):
    """Represents the execution of a specific plugin within the system."""
    __tablename__ = "processes"

    id = Column(Integer, primary_key=True, index=True)
    plugin_name = Column(String, nullable=False)
    configuration = Column(JSON, nullable=True)
    execution_date = Column(DateTime, default=datetime.now)

    # Relationship with the main task
    task_id = Column(Integer, ForeignKey("tasks.id"))
    task = relationship("Task", back_populates="processes")


class ChatSession(Base):
    """Manages chat sessions between the user and the system."""
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.now)

    # Relationship with messages in this session
    messages = relationship("ChatMessage", back_populates="session")


class ChatMessage(Base):
    """Represents an individual message in a conversation."""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"))
    role = Column(String, nullable=False)  # 'user' or 'system'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)

    # Relationship with the session it belongs to
    session = relationship("ChatSession", back_populates="messages")
