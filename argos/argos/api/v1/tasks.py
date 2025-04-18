from fastapi import APIRouter, Depends, HTTPException
from argos.database import get_db
from argos.database.repository import TaskRepository, ProcessRepository
import argos.models.schemas as schemas
from sqlalchemy.orm import Session
from typing import List

router = APIRouter(
    prefix="/api/v1/tasks",
    tags=["tasks"]
)

task_repo = TaskRepository()
process_repo = ProcessRepository()

# Endpoints for Tasks
@router.post("/", response_model=schemas.TaskInDB)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    """Create a new task."""
    return task_repo.create(db, task.model_dump())


@router.get("/", response_model=List[schemas.TaskInDB])
def get_tasks(skip: int = 0, limit: int = 100, pending_only: bool = False, db: Session = Depends(get_db),
        ):
    """Get the list of tasks with option to filter for pending ones."""
    if pending_only:
        return task_repo.get_pending_tasks(db)
    return task_repo.get_all(db)[skip: skip + limit]


@router.get("/{task_id}", response_model=schemas.TaskWithProcesses)
def get_task(task_id: int, db: Session = Depends(get_db)):
    """Get details of a specific task including its processes."""
    task = task_repo.get_by_id(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{task_id}", response_model=schemas.TaskInDB)
def update_task(task_id: int, task_update: schemas.TaskUpdate, db: Session = Depends(get_db),
                ):
    """Update an existing task."""
    updated_task = task_repo.update(db, task_id, task_update.model_dump(exclude_unset=True))
    if updated_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated_task


@router.put("/{task_id}/accept", response_model=schemas.TaskInDB)
def accept_task(task_id: int, db: Session = Depends(get_db)):
    """Mark a task as accepted."""
    task = task_repo.accept_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.delete("/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Delete a task."""
    success = task_repo.delete(db, task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"detail": "Task successfully deleted"}


# Endpoints for Processes
@router.post("/api/processes/", response_model=schemas.ProcessInDB, tags=["Processes"])
def create_process(process: schemas.ProcessCreate, db: Session = Depends(get_db),
                   ):
    """Create a new process associated with a task."""
    # Verify that the task exists
    task = task_repo.get_by_id(db, process.task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return process_repo.create(db, process.model_dump())


@router.get("/api/processes/", response_model=List[schemas.ProcessInDB], tags=["Processes"])
def get_processes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
        ):
    """Get the list of all processes."""
    return process_repo.get_all(db)[skip: skip + limit]


@router.get("/processes/{process_id}", response_model=schemas.ProcessInDB, tags=["Processes"])
def get_process(process_id: int, db: Session = Depends(get_db)):
    """Get details of a specific process."""
    process = process_repo.get_by_id(db, process_id)
    if process is None:
        raise HTTPException(status_code=404, detail="Process not found")
    return process


@router.get("/{task_id}/processes", response_model=List[schemas.ProcessInDB], tags=["Processes"])
def get_processes_by_task(task_id: int, db: Session = Depends(get_db)):
    """Get all processes associated with a task."""
    # Verify that the task exists
    task = task_repo.get_by_id(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return process_repo.get_by_task_id(db, task_id)


@router.put("/processes/{process_id}", response_model=schemas.ProcessInDB, tags=["Processes"])
def update_process(process_id: int, process_update: schemas.ProcessUpdate, db: Session = Depends(get_db),
                   ):
    """Update an existing process."""
    updated_process = process_repo.update(db, process_id, process_update.model_dump(exclude_unset=True))
    if updated_process is None:
        raise HTTPException(status_code=404, detail="Process not found")
    return updated_process


@router.delete("/processes/{process_id}", tags=["Processes"])
def delete_process(process_id: int, db: Session = Depends(get_db)):
    """Delete a process."""
    success = process_repo.delete(db, process_id)
    if not success:
        raise HTTPException(status_code=404, detail="Process not found")
    return {"detail": "Process successfully deleted"}
