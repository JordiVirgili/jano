from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List, Optional
from eris.core import PluginManager
from eris.database import get_db
from eris.database.repository import TaskRepository, ProcessRepository
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1/eris", tags=["eris"])

# Initialize plugin manager
plugin_manager = PluginManager()
plugin_manager.discover_plugins()

# Initialize repositories
task_repo = TaskRepository()
process_repo = ProcessRepository()


@router.get("/plugins")
def list_plugins():
    """List all available attack plugins."""
    plugins = plugin_manager.list_plugins()
    return {"plugins": plugins}


@router.post("/attack/{plugin_name}")
def execute_attack(plugin_name: str, target: str, options: Optional[Dict[str, Any]] = None,
        db: Session = Depends(get_db)):
    """
    Execute an attack using the specified plugin.

    Args:
        plugin_name: Name of the attack plugin to use
        target: Target to attack (hostname, IP, etc.)
        options: Optional parameters for the attack
    """
    # Create a task for this attack
    task_data = {"task_to_perform": f"Security assessment using {plugin_name}",
        "user_prompt": f"Execute {plugin_name} attack against {target}"}

    task = task_repo.create(db, task_data)

    # Get the plugin
    plugin = plugin_manager.get_plugin(plugin_name)
    if not plugin:
        task_repo.update(db, task.id, {"result": f"Error: Plugin '{plugin_name}' not found"})
        raise HTTPException(status_code=404, detail=f"Plugin '{plugin_name}' not found")

    # Create a process for this plugin execution
    process_data = {"plugin_name": plugin_name, "configuration": {"target": target, "options": options},
        "task_id": task.id}

    process = process_repo.create(db, process_data)

    try:
        # Execute the attack
        result = plugin.execute_attack(target, options)

        # Update the task with the result
        task_repo.update(db, task.id, {"result": str(result)})

        return {"task_id": task.id, "process_id": process.id, "plugin": plugin_name, "target": target, "result": result}
    except Exception as e:
        error_message = f"Error executing attack: {str(e)}"
        task_repo.update(db, task.id, {"result": error_message})
        raise HTTPException(status_code=500, detail=error_message)