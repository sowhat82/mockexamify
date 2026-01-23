"""
Background Task Status Tracking
Tracks the status of background AI tasks (explanation generation, AI fix, etc.)
"""
import json
import os
import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

STATUS_FILE = "background_tasks_status.json"
LOCK_FILE = "background_tasks_status.lock"

logger = logging.getLogger(__name__)


def _get_status_file_path() -> str:
    """Get the path to the status file"""
    return os.path.join(os.getcwd(), STATUS_FILE)


def _get_lock_file_path() -> str:
    """Get the path to the lock file"""
    return os.path.join(os.getcwd(), LOCK_FILE)


def _read_status_file() -> Dict[str, Any]:
    """Read the status file"""
    status_file = _get_status_file_path()
    try:
        if os.path.exists(status_file):
            with open(status_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error reading status file: {e}")
    return {"tasks": []}


def _write_status_file(data: Dict[str, Any]):
    """Write the status file with simple retry logic"""
    status_file = _get_status_file_path()
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Write to temp file first, then rename (atomic on most systems)
            temp_file = status_file + ".tmp"
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
            os.replace(temp_file, status_file)
            return
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(0.1)  # Brief wait before retry
            else:
                logger.error(f"Error writing status file: {e}")


def start_task(
    task_id: str,
    task_type: str,
    description: str,
    total_items: int = 0,
    pool_id: str = None,
    pool_name: str = None
) -> None:
    """Register a new background task as started"""
    data = _read_status_file()

    # Remove any existing task with same ID
    data["tasks"] = [t for t in data["tasks"] if t["task_id"] != task_id]

    task = {
        "task_id": task_id,
        "task_type": task_type,
        "description": description,
        "status": "running",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "total_items": total_items,
        "processed_items": 0,
        "fixed_items": 0,
        "error_items": 0,
        "pool_id": pool_id,
        "pool_name": pool_name,
        "current_item": None,
        "error_message": None
    }

    data["tasks"].append(task)
    _write_status_file(data)
    logger.info(f"Task {task_id} started: {description}")


def update_task_progress(
    task_id: str,
    processed: int,
    fixed: int = 0,
    errors: int = 0,
    current_item: str = None
) -> None:
    """Update task progress"""
    data = _read_status_file()

    for task in data["tasks"]:
        if task["task_id"] == task_id:
            task["processed_items"] = processed
            task["fixed_items"] = fixed
            task["error_items"] = errors
            task["current_item"] = current_item
            task["updated_at"] = datetime.now(timezone.utc).isoformat()
            break

    _write_status_file(data)


def complete_task(
    task_id: str,
    processed: int,
    fixed: int,
    errors: int,
    message: str = None
) -> None:
    """Mark a task as completed"""
    data = _read_status_file()

    for task in data["tasks"]:
        if task["task_id"] == task_id:
            task["status"] = "completed"
            task["processed_items"] = processed
            task["fixed_items"] = fixed
            task["error_items"] = errors
            task["completed_at"] = datetime.now(timezone.utc).isoformat()
            task["updated_at"] = datetime.now(timezone.utc).isoformat()
            task["current_item"] = None
            if message:
                task["completion_message"] = message
            break

    _write_status_file(data)
    logger.info(f"Task {task_id} completed: {processed} processed, {fixed} fixed, {errors} errors")


def fail_task(task_id: str, error_message: str) -> None:
    """Mark a task as failed"""
    data = _read_status_file()

    for task in data["tasks"]:
        if task["task_id"] == task_id:
            task["status"] = "failed"
            task["error_message"] = error_message
            task["completed_at"] = datetime.now(timezone.utc).isoformat()
            task["updated_at"] = datetime.now(timezone.utc).isoformat()
            break

    _write_status_file(data)
    logger.error(f"Task {task_id} failed: {error_message}")


def get_all_tasks() -> List[Dict[str, Any]]:
    """Get all tasks"""
    data = _read_status_file()
    return data.get("tasks", [])


def get_running_tasks() -> List[Dict[str, Any]]:
    """Get only running tasks"""
    tasks = get_all_tasks()
    return [t for t in tasks if t.get("status") == "running"]


def get_recent_tasks(limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent tasks (running first, then by updated_at)"""
    tasks = get_all_tasks()

    # Sort: running first, then by updated_at descending
    def sort_key(t):
        is_running = 0 if t.get("status") == "running" else 1
        updated = t.get("updated_at", "")
        return (is_running, -hash(updated))

    tasks.sort(key=lambda t: (
        0 if t.get("status") == "running" else 1,
        t.get("updated_at", "")
    ), reverse=True)

    # For completed/failed tasks, keep only recent ones
    running = [t for t in tasks if t.get("status") == "running"]
    completed = [t for t in tasks if t.get("status") != "running"][:limit - len(running)]

    return running + completed


def cleanup_old_tasks(max_age_hours: int = 24) -> None:
    """Remove completed/failed tasks older than max_age_hours"""
    data = _read_status_file()
    cutoff = datetime.now(timezone.utc).timestamp() - (max_age_hours * 3600)

    def should_keep(task):
        if task.get("status") == "running":
            return True
        completed_at = task.get("completed_at")
        if completed_at:
            try:
                task_time = datetime.fromisoformat(completed_at.replace('Z', '+00:00')).timestamp()
                return task_time > cutoff
            except:
                pass
        return True  # Keep if can't parse

    data["tasks"] = [t for t in data["tasks"] if should_keep(t)]
    _write_status_file(data)


def clear_all_tasks() -> None:
    """Clear all task history"""
    _write_status_file({"tasks": []})
