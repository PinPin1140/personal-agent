"""
IRIS Agent Engine - Deterministic autonomous task execution with enforcement
"""
import os
import json
import hashlib
import threading
import time
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime

# Import existing personal-agent components
from agent.task import Task, TaskStatus
from agent.memory import TaskRepository
from agent.model_router import ModelRouter


@dataclass
class ContextProject:
    """Project metadata"""
    id: str
    name: str
    created_at: str
    last_updated: str


@dataclass
class ReadStateFile:
    """File read state with checksum"""
    lines: tuple[int, int]  # (start, end) 1-based
    hash: str


@dataclass
class IntendedEdit:
    """Planned file modification"""
    file: str
    range: tuple[int, int]  # (start, end) 1-based
    reason: str
    original_content: Optional[str] = None
    new_content: Optional[str] = None


@dataclass
class Plan:
    """Task execution plan"""
    intended_edits: List[IntendedEdit]
    reasoning: str


@dataclass
class ReadState:
    """Files that have been read"""
    files_read: Dict[str, ReadStateFile]


@dataclass
class CurrentTask:
    """Currently executing task"""
    task_id: str
    goal: str
    status: str
    last_phase: str
    summary: str
    read_state: ReadState
    plan: Plan


@dataclass
class Policy:
    """Enforcement policies"""
    read_before_write: bool = True
    unrestricted: bool = True
    trusted_workspace: bool = False


@dataclass
class Meta:
    """System metadata"""
    journal_max: int = 200
    compact_after: int = 50


@dataclass
class Context:
    """Complete project context"""
    project: ContextProject
    current_task: Optional[CurrentTask]
    policy: Policy
    meta: Meta


@dataclass
class JournalEntry:
    """Action log entry"""
    ts: str
    task_id: str
    phase: str
    desc: str
    meta: Optional[Dict[str, Any]] = None


@dataclass
class Journal:
    """Action history"""
    entries: List[JournalEntry]


class ContextManager:
    """Atomic context and journal management"""

    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.getcwd())
        self.context_dir = self.project_root / '.context'
        self.context_path = self.context_dir / 'context.json'
        self.journal_path = self.context_dir / 'journal.json'
        self.checkpoints_dir = self.context_dir / 'checkpoints'
        self.lock_path = self.context_dir / '.lock'

        self.context_dir.mkdir(exist_ok=True)
        self.checkpoints_dir.mkdir(exist_ok=True)

    def initialize(self, project_name: str) -> bool:
        """Create initial context if it doesn't exist"""
        if self.context_path.exists():
            return False

        # Create initial context
        project = ContextProject(
            id=f"project_{int(time.time())}",
            name=project_name,
            created_at=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat()
        )

        context = Context(
            project=project,
            current_task=None,
            policy=Policy(),
            meta=Meta()
        )

        journal = Journal(entries=[])

        self._write_context(context)
        self._write_journal(journal)

        return True

    def load_context(self) -> Context:
        """Load context atomically"""
        with self._acquire_lock():
            if not self.context_path.exists():
                raise FileNotFoundError("Context not initialized. Run 'agent iris-new <project>' first.")

            with open(self.context_path, 'r') as f:
                data = json.load(f)

            # Convert back to dataclass
            return Context(
                project=ContextProject(**data['project']),
                current_task=CurrentTask(**data['current_task']) if data.get('current_task') else None,
                policy=Policy(**data['policy']),
                meta=Meta(**data['meta'])
            )

    def write_context(self, context: Context) -> None:
        """Write context atomically"""
        with self._acquire_lock():
            context.project.last_updated = datetime.now().isoformat()
            self._write_context(context)

    def load_journal(self) -> Journal:
        """Load journal"""
        if not self.journal_path.exists():
            return Journal(entries=[])

        with open(self.journal_path, 'r') as f:
            data = json.load(f)

        return Journal(entries=[
            JournalEntry(**entry) for entry in data['entries']
        ])

    def write_journal(self, journal: Journal) -> None:
        """Write journal with compaction if needed"""
        with self._acquire_lock():
            # Check if compaction needed
            if len(journal.entries) > self.load_context().meta.compact_after:
                self._compact_journal(journal)

            self._write_journal(journal)

    def add_journal_entry(self, entry: Dict[str, Any]) -> None:
        """Add new journal entry"""
        journal = self.load_journal()
        full_entry = JournalEntry(
            ts=datetime.now().isoformat(),
            **asdict(entry)
        )
        journal.entries.append(full_entry)
        self.write_journal(journal)

    def merge_summary(self, new_info: str) -> None:
        """Merge new information into context summary"""
        context = self.load_context()
        if context.current_task:
            # Simple merge - in production, use semantic merging
            context.current_task.summary = f"{context.current_task.summary} {new_info}".strip()[:800]
            self.write_context(context)

    def create_checkpoint(self, task_id: str, file_path: str) -> str:
        """Create file backup before editing"""
        checkpoint_dir = self.checkpoints_dir / task_id
        checkpoint_dir.mkdir(exist_ok=True)

        timestamp = int(time.time() * 1000)
        checkpoint_path = checkpoint_dir / f"{Path(file_path).name}.orig.{timestamp}"

        if Path(file_path).exists():
            import shutil
            shutil.copy2(file_path, checkpoint_path)

        return str(checkpoint_path)

    def rollback_file(self, checkpoint_path: str, target_path: str) -> None:
        """Restore file from checkpoint"""
        if Path(checkpoint_path).exists():
            import shutil
            shutil.copy2(checkpoint_path, target_path)

    def set_current_task(self, task: CurrentTask) -> None:
        """Set the currently executing task"""
        context = self.load_context()
        context.current_task = task
        self.write_context(context)

    def _acquire_lock(self):
        """Simple file-based locking"""
        return FileLock(self.lock_path)

    def _write_context(self, context: Context) -> None:
        """Write context to temp file then atomic rename"""
        temp_path = self.context_path.with_suffix('.tmp')
        with open(temp_path, 'w') as f:
            json.dump(asdict(context), f, indent=2)
        temp_path.replace(self.context_path)

    def _write_journal(self, journal: Journal) -> None:
        """Write journal to temp file then atomic rename"""
        temp_path = self.journal_path.with_suffix('.tmp')
        with open(temp_path, 'w') as f:
            json.dump(asdict(journal), f, indent=2)
        temp_path.replace(self.journal_path)

    def _compact_journal(self, journal: Journal) -> None:
        """Compact journal by summarizing old entries"""
        context = self.load_context()
        max_entries = context.meta.journal_max

        if len(journal.entries) <= context.meta.compact_after:
            return

        # Keep most recent entries
        keep_count = min(max_entries, len(journal.entries) - context.meta.compact_after)
        recent_entries = journal.entries[-keep_count:]

        # Summarize old entries
        old_entries = journal.entries[:-keep_count]
        summary = self._summarize_entries(old_entries)

        # Create summary entry
        summary_entry = JournalEntry(
            ts=datetime.now().isoformat(),
            task_id=old_entries[0].task_id if old_entries else 'unknown',
            phase='INIT',
            desc=f"Compacted {len(old_entries)} entries: {summary}",
            meta={'compacted': True, 'entry_count': len(old_entries)}
        )

        journal.entries = [summary_entry] + recent_entries

    def _summarize_entries(self, entries: List[JournalEntry]) -> str:
        """Summarize journal entries"""
        phases = [f"{e.phase}: {e.desc}" for e in entries[:10]]  # First 10
        return f"Historical actions: {', '.join(phases)}..."


class FileLock:
    """Simple file-based lock"""

    def __init__(self, lock_path: Path):
        self.lock_path = lock_path
        self.acquired = False

    def __enter__(self):
        # Simple spin lock
        while self.lock_path.exists():
            time.sleep(0.01)

        self.lock_path.touch()
        self.acquired = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.acquired and self.lock_path.exists():
            self.lock_path.unlink()


# Utility functions
def calculate_checksum(file_path: str) -> str:
    """Calculate SHA256 checksum of file"""
    if not Path(file_path).exists():
        return ''

    with open(file_path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def create_task(goal: str) -> CurrentTask:
    """Create new task"""
    import uuid
    return CurrentTask(
        task_id=str(uuid.uuid4()),
        goal=goal,
        status='pending',
        last_phase='INIT',
        summary='',
        read_state=ReadState(files_read={}),
        plan=Plan(intended_edits=[], reasoning='')
    )


def create_context(project_name: str) -> Context:
    """Create initial context"""
    import uuid
    now = datetime.now().isoformat()

    project = ContextProject(
        id=str(uuid.uuid4()),
        name=project_name,
        created_at=now,
        last_updated=now
    )

    return Context(
        project=project,
        current_task=None,
        policy=Policy(),
        meta=Meta()
    )