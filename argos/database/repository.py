from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional, Dict, Any, TypeVar, Generic, Type
from argos.models import Task, Process, ChatSession, ChatMessage

# Define a generic type for models
T = TypeVar('T')


class Repository(Generic[T]):
    """Generic base class for data repositories."""

    def __init__(self, model: Type[T]):
        self.model = model

    def get_all(self, db: Session) -> List[T]:
        """Get all records of the model."""
        return db.query(self.model).all()

    def get_by_id(self, db: Session, id: int) -> Optional[T]:
        """Get a record by its ID."""
        return db.query(self.model).filter(self.model.id == id).first()

    def create(self, db: Session, data: Dict[str, Any]) -> T:
        """Create a new record."""
        db_item = self.model(**data)
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item

    def update(self, db: Session, id: int, data: Dict[str, Any]) -> Optional[T]:
        """Update an existing record by its ID."""
        db_item = db.query(self.model).filter(self.model.id == id).first()
        if not db_item:
            return None

        for key, value in data.items():
            setattr(db_item, key, value)

        db.commit()
        db.refresh(db_item)
        return db_item

    def delete(self, db: Session, id: int) -> bool:
        """Delete a record by its ID."""
        db_item = db.query(self.model).filter(self.model.id == id).first()
        if not db_item:
            return False

        db.delete(db_item)
        db.commit()
        return True


class TaskRepository(Repository[Task]):
    """Repository for managing tasks."""

    def __init__(self):
        super().__init__(Task)

    def get_pending_tasks(self, db: Session) -> List[Task]:
        """Get all pending tasks (without acceptance date)."""
        return db.query(Task).filter(Task.acceptance_date == None).all()

    def accept_task(self, db: Session, task_id: int) -> Optional[Task]:
        """Mark a task as accepted."""
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return None

        task.acceptance_date = datetime.now()
        db.commit()
        db.refresh(task)
        return task


class ProcessRepository(Repository[Process]):
    """Repository for managing processes."""

    def __init__(self):
        super().__init__(Process)

    def get_by_task_id(self, db: Session, task_id: int) -> List[Process]:
        """Get all processes associated with a task."""
        return db.query(Process).filter(Process.task_id == task_id).all()


class ChatSessionRepository(Repository[ChatSession]):
    """Repository for managing chat sessions."""

    def __init__(self):
        super().__init__(ChatSession)

    def get_by_session_id(self, db: Session, session_id: str) -> Optional[ChatSession]:
        """Get a chat session by its session_id."""
        return db.query(ChatSession).filter(ChatSession.session_id == session_id).first()

    def get_or_create_session(self, db: Session, session_id: str) -> ChatSession:
        """Get an existing session or create a new one if it doesn't exist."""
        session = self.get_by_session_id(db, session_id)
        if not session:
            session = self.create(db, {"session_id": session_id})
        return session


class ChatMessageRepository(Repository[ChatMessage]):
    """Repository for managing chat messages."""

    def __init__(self):
        super().__init__(ChatMessage)

    def get_by_session_id(self, db: Session, session_id: int) -> List[ChatMessage]:
        """Get all messages in a session ordered by timestamp."""
        return db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.timestamp).all()

    def add_message(self, db: Session, session_id: int, role: str, content: str) -> ChatMessage:
        """Add a new message to a chat session."""
        message_data = {"session_id": session_id, "role": role, "content": content, "timestamp": datetime.now()}
        return self.create(db, message_data)
