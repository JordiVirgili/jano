from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from eris.database import Base


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