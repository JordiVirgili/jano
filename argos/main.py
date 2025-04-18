import uuid
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from argos.database import engine, get_db, Base
from argos.database.repository import TaskRepository, ProcessRepository, ChatSessionRepository, ChatMessageRepository
from argos.database.auth import verify_credentials
import argos.models.schemas as schemas

# Create tables in the database
Base.metadata.create_all(bind=engine)

# Initialize repositories
task_repo = TaskRepository()
process_repo = ProcessRepository()
chat_session_repo = ChatSessionRepository()
chat_message_repo = ChatMessageRepository()

app = FastAPI(title="Jano API", description="API for the Jano AI-powered security configuration system",
    version="1.0.0", )


# Endpoints for Tasks
@app.post("/api/tasks/", response_model=schemas.TaskInDB, tags=["Tasks"])
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db), username: str = Depends(verify_credentials)):
    """Create a new task."""
    return task_repo.create(db, task.model_dump())


@app.get("/api/tasks/", response_model=List[schemas.TaskInDB], tags=["Tasks"])
def get_tasks(skip: int = 0, limit: int = 100, pending_only: bool = False, db: Session = Depends(get_db),
        username: str = Depends(verify_credentials)):
    """Get the list of tasks with option to filter for pending ones."""
    if pending_only:
        return task_repo.get_pending_tasks(db)
    return task_repo.get_all(db)[skip: skip + limit]


@app.get("/api/tasks/{task_id}", response_model=schemas.TaskWithProcesses, tags=["Tasks"])
def get_task(task_id: int, db: Session = Depends(get_db), username: str = Depends(verify_credentials)):
    """Get details of a specific task including its processes."""
    task = task_repo.get_by_id(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.put("/api/tasks/{task_id}", response_model=schemas.TaskInDB, tags=["Tasks"])
def update_task(task_id: int, task_update: schemas.TaskUpdate, db: Session = Depends(get_db),
        username: str = Depends(verify_credentials)):
    """Update an existing task."""
    updated_task = task_repo.update(db, task_id, task_update.model_dump(exclude_unset=True))
    if updated_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated_task


@app.put("/api/tasks/{task_id}/accept", response_model=schemas.TaskInDB, tags=["Tasks"])
def accept_task(task_id: int, db: Session = Depends(get_db), username: str = Depends(verify_credentials)):
    """Mark a task as accepted."""
    task = task_repo.accept_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.delete("/api/tasks/{task_id}", tags=["Tasks"])
def delete_task(task_id: int, db: Session = Depends(get_db), username: str = Depends(verify_credentials)):
    """Delete a task."""
    success = task_repo.delete(db, task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"detail": "Task successfully deleted"}


# Endpoints for Processes
@app.post("/api/processes/", response_model=schemas.ProcessInDB, tags=["Processes"])
def create_process(process: schemas.ProcessCreate, db: Session = Depends(get_db),
        username: str = Depends(verify_credentials)):
    """Create a new process associated with a task."""
    # Verify that the task exists
    task = task_repo.get_by_id(db, process.task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return process_repo.create(db, process.model_dump())


@app.get("/api/processes/", response_model=List[schemas.ProcessInDB], tags=["Processes"])
def get_processes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
        username: str = Depends(verify_credentials)):
    """Get the list of all processes."""
    return process_repo.get_all(db)[skip: skip + limit]


@app.get("/api/processes/{process_id}", response_model=schemas.ProcessInDB, tags=["Processes"])
def get_process(process_id: int, db: Session = Depends(get_db), username: str = Depends(verify_credentials)):
    """Get details of a specific process."""
    process = process_repo.get_by_id(db, process_id)
    if process is None:
        raise HTTPException(status_code=404, detail="Process not found")
    return process


@app.get("/api/tasks/{task_id}/processes", response_model=List[schemas.ProcessInDB], tags=["Processes"])
def get_processes_by_task(task_id: int, db: Session = Depends(get_db), username: str = Depends(verify_credentials)):
    """Get all processes associated with a task."""
    # Verify that the task exists
    task = task_repo.get_by_id(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return process_repo.get_by_task_id(db, task_id)


@app.put("/api/processes/{process_id}", response_model=schemas.ProcessInDB, tags=["Processes"])
def update_process(process_id: int, process_update: schemas.ProcessUpdate, db: Session = Depends(get_db),
        username: str = Depends(verify_credentials)):
    """Update an existing process."""
    updated_process = process_repo.update(db, process_id, process_update.model_dump(exclude_unset=True))
    if updated_process is None:
        raise HTTPException(status_code=404, detail="Process not found")
    return updated_process


@app.delete("/api/processes/{process_id}", tags=["Processes"])
def delete_process(process_id: int, db: Session = Depends(get_db), username: str = Depends(verify_credentials)):
    """Delete a process."""
    success = process_repo.delete(db, process_id)
    if not success:
        raise HTTPException(status_code=404, detail="Process not found")
    return {"detail": "Process successfully deleted"}


# Endpoints for chat
@app.post("/api/chat/query", response_model=schemas.ChatResponse, tags=["Chat"])
def chat_query(query: schemas.ChatQuery, db: Session = Depends(get_db), username: str = Depends(verify_credentials)):
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


@app.get("/api/chat/sessions", response_model=List[schemas.ChatSessionInDB], tags=["Chat"])
def get_chat_sessions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
        username: str = Depends(verify_credentials)):
    """Get the list of all chat sessions."""
    return chat_session_repo.get_all(db)[skip: skip + limit]


@app.get("/api/chat/sessions/{session_id}", response_model=schemas.ChatSessionWithMessages, tags=["Chat"])
def get_chat_session(session_id: str, db: Session = Depends(get_db), username: str = Depends(verify_credentials)):
    """Get details of a specific chat session including its messages."""
    session = chat_session_repo.get_by_session_id(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return session


@app.delete("/api/chat/sessions/{session_id}", tags=["Chat"])
def delete_chat_session(session_id: str, db: Session = Depends(get_db), username: str = Depends(verify_credentials)):
    """Delete a chat session."""
    session = chat_session_repo.get_by_session_id(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Chat session not found")

    success = chat_session_repo.delete(db, session.id)
    if not success:
        raise HTTPException(status_code=500, detail="Error deleting chat session")

    return {"detail": "Chat session successfully deleted"}


# Specific endpoint for Argos subsystem
@app.post("/api/scan", tags=["Argos"])
def argos_scan(service_name: str, db: Session = Depends(get_db), username: str = Depends(verify_credentials)):
    """
    Activate the configuration analysis plugin for a specific service.

    This endpoint is a placeholder. The real implementation would depend on available
    plugins and the module architecture.
    """
    # Here a task would be created to start the scanning process with Argos
    task_data = {"task_to_perform": f"Configuration analysis for {service_name}",
        "user_prompt": f"Scan configuration of {service_name}"}

    task = task_repo.create(db, task_data)

    # This is a placeholder, in the real implementation the corresponding plugin would be started
    return {"task_id": task.id, "service": service_name, "status": "started",
        "message": f"Analysis of {service_name} has been started. Check the task status for progress."}


# Root path to verify the API is running
@app.get("/", tags=["Status"])
def read_root(username: str = Depends(verify_credentials)):
    """Verify that the API is running."""
    return {"status": "API running", "version": "1.0.0", "authenticated_as": username}