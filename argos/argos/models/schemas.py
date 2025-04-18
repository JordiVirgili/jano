from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


# Schemas for Task
class TaskBase(BaseModel):
    task_to_perform: str
    user_prompt: str


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    task_to_perform: Optional[str] = None
    user_prompt: Optional[str] = None
    result: Optional[str] = None
    acceptance_date: Optional[datetime] = None


class TaskInDB(TaskBase):
    id: int
    start_date: datetime
    result: Optional[str] = None
    acceptance_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# Schemas for Process
class ProcessBase(BaseModel):
    plugin_name: str
    configuration: Optional[Dict[str, Any]] = None
    task_id: int


class ProcessCreate(ProcessBase):
    pass


class ProcessUpdate(BaseModel):
    plugin_name: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None


class ProcessInDB(ProcessBase):
    id: int
    execution_date: datetime

    model_config = ConfigDict(from_attributes=True)


# Schemas for ChatSession
class ChatSessionBase(BaseModel):
    session_id: str


class ChatSessionCreate(ChatSessionBase):
    pass


class ChatSessionInDB(ChatSessionBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Schemas for ChatMessage
class ChatMessageBase(BaseModel):
    role: str
    content: str


class ChatMessageCreate(ChatMessageBase):
    session_id: int


class ChatMessageInDB(ChatMessageBase):
    id: int
    session_id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


# Additional schemas for specific operations
class ChatQuery(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str


class TaskWithProcesses(TaskInDB):
    processes: List[ProcessInDB] = []

    model_config = ConfigDict(from_attributes=True)


class ChatSessionWithMessages(ChatSessionInDB):
    messages: List[ChatMessageInDB] = []

    model_config = ConfigDict(from_attributes=True)
