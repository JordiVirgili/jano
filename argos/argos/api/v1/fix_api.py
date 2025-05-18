from fastapi import APIRouter, Depends, HTTPException
from argos.database import get_db
from argos.database.repository import TaskRepository
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import argos.models.schemas as schemas
from argos.services import fixer_service

router = APIRouter(prefix="/api/v1/argos", tags=["argos"])

task_repo = TaskRepository()


# Endpoint to list supported services for configuration fixing
@router.get("/fix/supported-services")
def list_supported_services():
    """
    List all services supported by the configuration fixer plugins.

    Returns:
        Dictionary mapping plugin names to the services they support
    """
    supported_services = fixer_service.get_supported_services()
    return {"supported_services": supported_services}


# Endpoint to analyze a configuration
@router.post("/fix/analyze")
def analyze_configuration(service_name: str, file_path: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Analyze the configuration of a specific service.

    Args:
        service_name: Name of the service to analyze
        file_path: Optional path to configuration file (if not provided, will be auto-detected)

    Returns:
        Analysis results including detected issues and their severity
    """
    task_data = {"task_to_perform": f"Analyze configuration for {service_name}",
        "user_prompt": f"Analyze configuration of {service_name}"}

    task = task_repo.create(db, task_data)

    # Analyze the configuration
    result = fixer_service.analyze_configuration(service_name, file_path)

    # Update the task with the result
    if isinstance(result, dict):
        task_repo.update(db, task.id, {"result": str(result)})

    return {"task_id": task.id, "service": service_name, "file_path": file_path or "auto-detected",
        "analysis_result": result}


# Endpoint to apply fixes to a configuration
@router.post("/fix/apply")
def apply_fixes(service_name: str, file_path: Optional[str] = None, fix_ids: Optional[List[str]] = None,
                create_backup: bool = True, restart_service: bool = False, db: Session = Depends(get_db)):
    """
    Apply fixes to a service configuration.

    Args:
        service_name: Name of the service to fix
        file_path: Optional path to configuration file (if not provided, will be auto-detected)
        fix_ids: List of specific fix IDs to apply (if not provided, all detected issues will be fixed)
        create_backup: Whether to create a backup before modifying the file
        restart_service: Whether to restart the service after applying fixes

    Returns:
        Result of the fix operation including success status and detailed message
    """
    task_data = {"task_to_perform": f"Apply fixes to {service_name} configuration",
        "user_prompt": f"Fix configuration of {service_name}"}

    task = task_repo.create(db, task_data)

    # If specific fix IDs are provided, first analyze to get the fixes, then filter by ID
    fixes = None
    if fix_ids:
        analysis_result = fixer_service.analyze_configuration(service_name, file_path)
        if analysis_result.get("success") and "issues" in analysis_result:
            fixes = [issue for issue in analysis_result["issues"] if issue.get("id") in fix_ids]

    # Apply the fixes
    result = fixer_service.apply_fixes(service_name=service_name, file_path=file_path, fixes=fixes,
        backup=create_backup, restart=restart_service)

    # Update the task with the result
    if isinstance(result, dict):
        task_repo.update(db, task.id, {"result": str(result)})

    return {"task_id": task.id, "service": service_name, "file_path": file_path or "auto-detected",
        "fixed_ids": fix_ids or "all issues", "created_backup": create_backup,
        "restarted_service": restart_service and result.get("restart_success", False), "result": result}


# Endpoint to run a full fix cycle: analyze, fix, and optionally restart
@router.post("/fix/auto")
def auto_fix(service_name: str, file_path: Optional[str] = None, create_backup: bool = True,
             restart_service: bool = False, db: Session = Depends(get_db)):
    """
    Run a complete fix cycle: analyze the configuration, apply all fixes, and optionally restart the service.

    Args:
        service_name: Name of the service to fix
        file_path: Optional path to configuration file (if not provided, will be auto-detected)
        create_backup: Whether to create a backup before modifying the file
        restart_service: Whether to restart the service after applying fixes

    Returns:
        Comprehensive results of the entire fix operation
    """
    task_data = {"task_to_perform": f"Automatic fix of {service_name} configuration",
        "user_prompt": f"Auto-fix configuration of {service_name}"}

    task = task_repo.create(db, task_data)

    # Step 1: Analyze
    analysis_result = fixer_service.analyze_configuration(service_name, file_path)

    # If analysis failed or no issues found, return early
    if not analysis_result.get("success"):
        task_repo.update(db, task.id, {"result": str(analysis_result)})
        return {"task_id": task.id, "service": service_name, "analysis_success": False,
            "message": analysis_result.get("message", "Analysis failed"), "analysis_result": analysis_result}

    if not analysis_result.get("issues"):
        task_repo.update(db, task.id, {"result": "No issues found, no fixes needed"})
        return {"task_id": task.id, "service": service_name, "analysis_success": True,
            "message": "No issues found, no fixes needed", "analysis_result": analysis_result}

    # Step 2: Apply fixes
    fix_result = fixer_service.apply_fixes(service_name=service_name, file_path=file_path, fixes=None,  # Fix all issues
        backup=create_backup, restart=restart_service)

    # Combine the results
    combined_result = {"task_id": task.id, "service": service_name,
        "file_path": file_path or analysis_result.get("file_path", "auto-detected"),
        "analysis_success": analysis_result.get("success", False),
        "issues_found": len(analysis_result.get("issues", [])), "fix_success": fix_result.get("success", False),
        "created_backup": create_backup,
        "restarted_service": restart_service and fix_result.get("restart_success", False), "fix_details": fix_result,
        "analysis_details": analysis_result}

    # Update the task with the combined result
    task_repo.update(db, task.id, {"result": str(combined_result)})

    return combined_result
