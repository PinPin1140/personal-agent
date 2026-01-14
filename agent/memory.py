"""Persistence layer for tasks and memory using atomic JSON writes."""
import json
import os
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

from .task import Task, TaskStatus


class MemoryStore:
    """Thread-safe JSON file storage with atomic writes."""

    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self._data: Dict[str, Any] = {}
        self._load()

    def _load(self):
        """Load data from file, initialize if missing."""
        if self.filepath.exists():
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._data = {}
        else:
            self._data = {}
            self._save()

    def _save(self):
        """Atomically write data to file."""
        temp_path = self.filepath.with_suffix(".tmp")
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
            temp_path.replace(self.filepath)
        except (IOError, OSError):
            if temp_path.exists():
                temp_path.unlink()
            raise

    def get(self, key: str, default: Any = None) -> Any:
        """Get value by key."""
        return self._data.get(key, default)

    def set(self, key: str, value: Any):
        """Set value by key and persist."""
        self._data[key] = value
        self._save()

    def delete(self, key: str):
        """Remove key from storage."""
        if key in self._data:
            del self._data[key]
            self._save()

    def all(self) -> Dict[str, Any]:
        """Return all data."""
        return self._data.copy()


class TaskRepository:
    """Repository for task persistence and retrieval."""

    def __init__(self, filepath: str = "data/tasks.json"):
        self.store = MemoryStore(filepath)
        self._tasks: Dict[int, Task] = {}
        self._next_id = 1
        self._load_tasks()

    def _load_tasks(self):
        """Load all tasks from storage."""
        tasks_data = self.store.get("tasks", {})
        for task_id_str, task_data in tasks_data.items():
            try:
                task = Task.from_dict(task_data)
                self._tasks[task.id] = task
            except (KeyError, TypeError):
                continue

        max_id = self.store.get("next_id", 1)
        self._next_id = max(1, max_id)

    def _save_tasks(self):
        """Persist all tasks to storage."""
        tasks_data = {
            str(task_id): task.to_dict()
            for task_id, task in self._tasks.items()
        }
        self.store.set("tasks", tasks_data)
        self.store.set("next_id", self._next_id)

    def create(self, goal: str) -> Task:
        """Create new task with auto-incremented ID."""
        task_id = self._next_id
        self._next_id += 1

        task = Task(
            id=task_id,
            goal=goal,
            status=TaskStatus.PENDING,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        self._tasks[task_id] = task
        self._save_tasks()
        return task

    def get(self, task_id: int) -> Optional[Task]:
        """Retrieve task by ID."""
        return self._tasks.get(task_id)

    def list_all(self) -> List[Task]:
        """List all tasks, sorted by ID."""
        return sorted(self._tasks.values(), key=lambda t: t.id)

    def update(self, task: Task):
        """Update existing task in storage."""
        if task.id in self._tasks:
            self._tasks[task.id] = task
            self._save_tasks()

    def delete(self, task_id: int) -> bool:
        """Delete task by ID, return True if deleted."""
        if task_id in self._tasks:
            del self._tasks[task_id]
            self._save_tasks()
            return True
        return False
