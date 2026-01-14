"""CLI entrypoint for the personal agent."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.memory import TaskRepository
from agent.engine import AgentEngine
from agent.model_router import ModelRouter
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

    # Auth commands
    auth_parser = subparsers.add_parser("auth", help="Authentication management")
    auth_subparsers = auth_parser.add_subparsers(dest="auth_command")

    auth_login_parser = auth_subparsers.add_parser("login", help="Login to provider")
    auth_login_parser.add_argument("provider", help="Provider name (e.g., openai)")

    auth_status_parser = auth_subparsers.add_parser("status", help="Check auth status")

    auth_logout_parser = auth_subparsers.add_parser("logout", help="Logout from provider")
    auth_logout_parser.add_argument("provider", help="Provider name")

    auth_add_account_parser = auth_subparsers.add_parser("add-account", help="Add account for provider")
    auth_add_account_parser.add_argument("provider", help="Provider name")
    auth_add_account_parser.add_argument("account-id", help="Account identifier")
    auth_add_account_parser.add_argument("--priority", type=int, default=1, help="Account priority (higher first)")

    auth_list_parser = auth_subparsers.add_parser("list", help="List all accounts")

    auth_rotate_parser = auth_subparsers.add_parser("rotate", help="Rotate to next available account")
    auth_rotate_parser.add_argument("provider", help="Provider name")

    # Plugin commands
    plugin_parser = subparsers.add_parser("plugin", help="Plugin management")
    plugin_subparsers = plugin_parser.add_subparsers(dest="plugin_command")

    plugin_install_parser = plugin_subparsers.add_parser("install", help="Install plugin from path or URL")
    plugin_install_parser.add_argument("path", help="Path or URL to plugin")

    plugin_list_parser = plugin_subparsers.add_parser("list", help="List all plugins")

    plugin_remove_parser = plugin_subparsers.add_parser("remove", help="Remove installed plugin")
    plugin_remove_parser.add_argument("name", help="Plugin name")

    plugin_enable_parser = plugin_subparsers.add_parser("enable", help="Enable a plugin")
    plugin_enable_parser.add_argument("name", help="Plugin name")

    plugin_disable_parser = plugin_subparsers.add_parser("disable", help="Disable a plugin")
    plugin_disable_parser.add_argument("name", help="Plugin name")

    # Workers command
    workers_parser = subparsers.add_parser("workers", help="Show worker status")

    # Stream command
    stream_parser = subparsers.add_parser("stream", help="Stream task execution")
    stream_parser.add_argument("task_id", type=int, help="Task ID to stream")

    # IRIS commands
    iris_parser = subparsers.add_parser("iris-new", help="Create new IRIS task with .context")
    iris_parser.add_argument("goal", help="Task goal (use quotes)")

    iris_list_parser = subparsers.add_parser("iris-list", help="List current IRIS task")

    iris_run_parser = subparsers.add_parser("iris-run", help="Run IRIS task with enforcement")
    iris_run_parser.add_argument("task_id", help="IRIS task ID to run")

    iris_attach_parser = subparsers.add_parser("iris-attach", help="Attach to running IRIS task")
    iris_attach_parser.add_argument("task_id", help="IRIS task ID to attach to")

    iris_logs_parser = subparsers.add_parser("iris-logs", help="View IRIS task execution logs")
    iris_logs_parser.add_argument("task_id", help="IRIS task ID to view logs for")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    repo = TaskRepository()
    router = ModelRouter()
    engine = AgentEngine(repo, router)

    if args.command == "auth":
        if args.auth_command == "login":
                print(f"Login to provider: {args.provider}")
                print("OAuth flow not implemented yet. Stub:")
                print("  1. Would show auth URL")
                print("  2. Wait for callback")
                print("  3. Store tokens securely")
        elif args.auth_command == "status":
                provider_name = getattr(args, 'provider', None)
                if provider_name:
                        print(f"Auth status for {provider_name}")
                else:
                        provider = router.get_provider()
                        print(f"Default provider: {router.get_default_provider()}")
                        print(f"Auth type: {provider.auth_type}")
                        print(f"Streaming: {provider.supports_streaming}")
        elif args.auth_command == "logout":
                print(f"Logout from provider: {args.provider}")
                print("Session clearing not implemented yet")
                return 0

        elif args.auth_command == "add-account":
                from agent.auth.accounts import AccountManager
                account_mgr = AccountManager()
                success = account_mgr.add_account(
                        args.provider,
                        getattr(args, 'account-id'),
                        {
                                "type": "oauth_token",
                                "token": "stub_token"
                        },
                        getattr(args, 'priority', 1)
                )
                if success:
                        print(f"Account {getattr(args, 'account-id')} added to {args.provider}")
                else:
                        print("Failed to add account")
                return 0

        elif args.auth_command == "list":
                from agent.auth.accounts import AccountManager
                account_mgr = AccountManager()
                provider_name = getattr(args, 'provider', None)
                accounts = account_mgr.list_accounts(provider_name)

                if not accounts:
                        print(f"No accounts found for provider: {provider_name or 'all'}")
                        return 0

                print(f"Accounts ({len(accounts)}):")
                for account in accounts:
                        cooldown_status = "in cooldown" if account.get("cooldown_until", 0) > time.time() else "available"
                        print(f"  {account['account_id']}: priority={account['priority']}, last_used={account.get('last_used', 'never')}, {cooldown_status}")
                return 0

        elif args.auth_command == "rotate":
                from agent.auth.accounts import AccountManager
                from agent.auth.rotation import AccountRotator
                account_mgr = AccountManager()
                rotator = AccountRotator(account_mgr)

                provider_name = getattr(args, 'provider', None)
                if not provider_name:
                        print("Provider name required for rotate")
                        return 0

                account_id = rotator.select_account(provider_name)

                if not account_id:
                        print("No available accounts for rotation")
                        return 0

                print(f"Rotated to account: {account_id}")
                return 0

    if args.command == "workers":
        workers = engine.get_worker_status()
        print(f"Workers ({len(workers)}):")
        for worker in workers:
                print(f"  Worker {worker['worker_id']}: {worker['status']}")
        return 0

    if args.command == "stream":
        task = repo.get(args.task_id)
        if not task:
                print(f"Task {args.task_id} not found")
                return 1

        print(f"Streaming task {task.id}: {task.goal}")
        print(f"Status: {task.status.value}")
        print(f"\nSteps: {len(task.steps)}")
        print("Execution log:\n")

        for step in task.steps:
                print(f"[{step['action'].upper()}] {step['timestamp']}")
                if step.get('result'):
                        print(f"  Result: {step['result'][:200]}{'...' if len(step.get('result', '')) > 200 else ''}")
                if step.get('error'):
                        print(f"  Error: {step['error']}")
        return 0

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

    # IRIS commands
    elif args.command == "iris-new":
        from agent.iris_cli import IRISNewCommand
        cmd = IRISNewCommand()
        cmd.execute(args.goal)

    elif args.command == "iris-list":
        from agent.iris_cli import IRISListCommand
        cmd = IRISListCommand()
        cmd.execute()

    elif args.command == "iris-run":
        from agent.iris_cli import IRISRunCommand
        cmd = IRISRunCommand()
        cmd.execute(args.task_id)

    elif args.command == "iris-attach":
        from agent.iris_cli import IRISAttachCommand
        cmd = IRISAttachCommand()
        cmd.execute(args.task_id)

    elif args.command == "iris-logs":
        from agent.iris_cli import IRISLogsCommand
        cmd = IRISLogsCommand()
        cmd.execute(args.task_id)

    return 0


if __name__ == "__main__":
    sys.exit(main())
