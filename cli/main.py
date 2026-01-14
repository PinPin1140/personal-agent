"""CLI entrypoint for the personal agent."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.memory import TaskRepository
from agent.engine import AgentEngine
from agent.models import DummyProvider
from agent.task import TaskStatus


def main():
    parser = argparse.ArgumentParser(
        prog="agent",
        description="Personal autonomous AI agent - task-based core"
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    subparsers.add_parser("help", help="Show this help message")

    add_parser = subparsers.add_parser("add", help="Add a new task")
    add_parser.add_argument("goal", help="Task goal (use quotes)")

    subparsers.add_parser("list", help="List all tasks")

    run_parser = subparsers.add_parser("run", help="Run next task")
    run_parser.add_argument("--task", type=int, help="Specific task ID to run")

    resume_parser = subparsers.add_parser("resume", help="Resume a paused task")
    resume_parser.add_argument("task_id", type=int, help="Task ID to resume")

    pause_parser = subparsers.add_parser("pause", help="Pause a task")
    pause_parser.add_argument("task_id", type=int, help="Task ID to pause")

    subparsers.add_parser("status", help="Show agent status")

    logs_parser = subparsers.add_parser("logs", help="Show task logs")
    logs_parser.add_argument("task_id", type=int, help="Task ID to show logs for")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    repo = TaskRepository()
    provider = DummyProvider()
    engine = AgentEngine(repo, provider)

    if args.command == "add":
        task = repo.create(args.goal)
        print(f"Task {task.id} added: {task.goal}")

    elif args.command == "list":
        tasks = repo.list_all()
        if not tasks:
            print("No tasks")
            return 0

        print("Tasks:")
        for task in tasks:
            status_icon = {
                TaskStatus.PENDING: "[ ]",
                TaskStatus.RUNNING: "[*]",
                TaskStatus.PAUSED: "[P]",
                TaskStatus.DONE: "[X]",
                TaskStatus.ERROR: "[!]"
            }.get(task.status, "[?]")
            print(f"  {status_icon} {task.id}: {task.goal} ({task.status.value})")

    elif args.command == "run":
        task = engine.run_single_task(args.task)
        if task:
            print(f"Task {task.id} finished with status: {task.status.value}")

    elif args.command == "resume":
        task = engine.resume_task(args.task_id)
        if task:
            print(f"Task {task.id} resumed and finished with status: {task.status.value}")

    elif args.command == "pause":
        engine.pause_task(args.task_id)

    elif args.command == "status":
        tasks = repo.list_all()
        if not tasks:
            print("No tasks")
            return 0

        status_counts = {}
        for task in tasks:
            status_counts[task.status.value] = status_counts.get(task.status.value, 0) + 1

        print("Agent Status:")
        for status, count in sorted(status_counts.items()):
            print(f"  {status}: {count}")

    elif args.command == "logs":
        task = repo.get(args.task_id)
        if not task:
            print(f"Task {args.task_id} not found")
            return 1

        print(f"Task {task.id}: {task.goal}")
        print(f"Status: {task.status.value}")
        print(f"Steps: {len(task.steps)}")
        print()

        if not task.steps:
            print("No steps recorded")
            return 0

        print("Execution log:")
        for step in task.steps:
            print(f"\n[Step {step['step_id']}] {step['timestamp']}")
            print(f"  Action: {step['action']}")
            if step.get('result'):
                print(f"  Result: {step['result']}")
            if step.get('error'):
                print(f"  Error: {step['error']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
