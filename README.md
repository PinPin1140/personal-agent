# Personal Agent

A lightweight, production-oriented AI agent core for autonomous task execution.

## What This Is

Personal Agent is a task-based autonomous AI engine designed as a foundational system, not a prototype or demo. It provides:

- **Persistent task management** - Tasks survive program restarts
- **Multiple task support** - Handle multiple concurrent tasks across projects
- **Non-chat interface** - Task-focused workflow, not conversation-based
- **Deterministic execution** - Single-threaded main loop for predictable behavior
- **Extensible architecture** - Plugin system for model providers and tools

This is a CORE ENGINE - meant to be extended, customized, and integrated into your own workflows.

## Why It Exists

Most AI agent tools are either:
- Full-featured GUI applications (vendor lock-in, heavy dependencies)
- Chat-based interfaces (conversational overhead, not task-oriented)
- Prototype codebases (not production-ready)

Personal Agent takes a different approach:
- **CLI-only** - No TUI, GUI, web server, or Electron
- **Minimal dependencies** - Uses Python stdlib wherever possible
- **Fast startup** - Target <200ms startup time
- **Production-oriented** - Atomic writes, proper error handling, no permission spam

## How It Differs from OpenCode & Agent Zero

| Feature | Personal Agent | OpenCode | Agent Zero |
|---------|---------------|----------|------------|
| Interface | CLI | TUI/Web | Web |
| Execution model | Task-based | Chat-based | Task-based |
| Persistence | JSON/SQLite | Built-in | Built-in |
| Dependencies | Minimal (stdlib-heavy) | Substantial | Substantial |
| Extensibility | Plugin system | Fixed | Fixed |
| Platform focus | Linux (no sudo) | Cross-platform | Cross-platform |
| Privacy | Local-only | Hybrid | Hybrid |

**Key differences:**
- Personal Agent is purposefully minimal - a core engine you build upon
- No interactive prompts or permission spam
- Designed for local, headless environments
- Extensible provider architecture for future LLM integrations

## How to Use

### Installation

No installation required. Just run the CLI:

```bash
python cli/main.py
```

Or create an alias for convenience:
```bash
alias agent="python /path/to/personal-agent/cli/main.py"
```

### Basic Commands

#### Add a Task

```bash
agent add "Create a backup script"
```

#### List All Tasks

```bash
agent list
```

Output:
```
Tasks:
  [ ] 1: Create a backup script (pending)
  [X] 2: Clean up logs (done)
  [P] 3: Migrate database (paused)
```

#### Run a Task

Run the next pending task:
```bash
agent run
```

Run a specific task:
```bash
agent run --task 3
```

#### Resume a Paused Task

```bash
agent resume 3
```

#### Pause a Running Task

```bash
agent pause 3
```

#### Check Status

```bash
agent status
```

Output:
```
Agent Status:
  pending: 1
  running: 0
  paused: 1
  done: 2
  error: 0
```

#### View Task Logs

```bash
agent logs 1
```

Output:
```
Task 1: Create a backup script
Status: done
Steps: 3

Execution log:

[Step 1] 2026-01-15T03:20:25
  Action: decision
  Result: Need to create a Python script...

[Step 2] 2026-01-15T03:20:26
  Action: action
  Result: Script created successfully

[Step 3] 2026-01-15T03:20:27
  Action: decision
   Result: done
```

## How Provider Registration Works

The agent supports multiple model providers through a pluggable router system.

### Built-in Providers

- **dummy**: For testing without API keys
- **openai**: Uses OpenAI API (requires `OPENAI_API_KEY` environment variable)

### Automatic Provider Selection

The router automatically selects the default provider:
- OpenAI if `OPENAI_API_KEY` is set
- Dummy provider otherwise

### Extending with New Providers

Create a new provider class implementing `ModelProvider` and register it:

```python
from agent.model_router import ModelRouter

router = ModelRouter()
router.register("my_provider", MyProvider())
response = router.generate("prompt", provider_name="my_provider")
```

## How Task Persistence Works

### Task Storage

Tasks are stored in `data/tasks.json` with the following structure:

```json
{
  "tasks": {
    "1": {
      "id": 1,
      "goal": "Example task",
      "status": "pending",
      "created_at": "2026-01-15T03:20:25",
      "updated_at": "2026-01-15T03:20:25",
      "steps": [],
      "memory": {}
    }
  },
  "next_id": 2
}
```

### Atomic Writes

All writes are atomic using a temporary file pattern:
1. Write to `tasks.json.tmp`
2. Replace `tasks.json` with the temp file
3. If failure occurs, temp file is cleaned up

This prevents corruption even if the process crashes mid-write.

### Task Lifecycle

```
pending → running → done
    ↓         ↓
  paused    error
```

- **pending**: Task created, waiting to run
- **running**: Task is actively executing
- **paused**: Task interrupted, can be resumed
- **done**: Task completed successfully
- **error**: Task failed (see logs for details)

### State After Restart

When you restart the agent:
- All tasks are loaded from disk
- Running tasks remain in running state
- Paused tasks can be resumed
- Task history (steps) is preserved
- No context is lost

## How to Extend

### Add a New Model Provider

Create a new provider class in `agent/models.py`:

```python
class OpenAIProvider(ModelProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key

    def generate(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        # Implementation here
        pass

    @property
    def supports_streaming(self) -> bool:
        return True

    @property
    def auth_type(self) -> AuthType:
        return AuthType.APIKEY
```

Register it in your code:

```python
registry = ProviderRegistry()
registry.register("openai", OpenAIProvider(api_key="..."))
```

### Add a New Tool

Extend `ToolExecutor` in `agent/executor.py`:

```python
def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Tuple[int, str, Optional[str]]:
    if tool_name == "file_read":
        filepath = args.get("filepath")
        # Implementation
        return 0, content, None

    # Existing tools...
```

### Customize the Engine

The `AgentEngine` class is designed to be subclassed:

```python
class CustomEngine(AgentEngine):
    def _is_complete(self, decision: str) -> bool:
        # Custom completion logic
        return "TASK_COMPLETE" in decision

    def _execute_action(self, decision: str, task: Task) -> Dict[str, Any]:
        # Custom action parsing and execution
        pass
```

## Architecture

### Core Components

- **agent/task.py**: Task model with state machine
- **agent/memory.py**: Persistence layer with atomic JSON writes
- **agent/engine.py**: Deterministic main loop for task execution
- **agent/executor.py**: Tool and shell execution
- **agent/models.py**: Model provider plugin system
- **cli/main.py**: CLI entrypoint and command handlers
- **tools/shell.py**: Controlled shell execution utility

### Design Principles

1. **Tasks are first-class** - Everything centers around the Task entity
2. **State after every step** - Progress is saved continuously
3. **Deterministic execution** - No background daemons or async magic
4. **Fail safely** - Shell timeouts, no sudo, proper error handling
5. **Minimal dependencies** - Prefer stdlib over external packages

## Development

### Running Tests

No test framework is included (minimal dependencies). Test manually:

```bash
python cli/main.py add "Test task"
python cli/main.py list
python cli/main.py run --task 1
python cli/main.py logs 1
```

### Adding Features

1. Follow existing patterns in the codebase
2. Keep dependencies minimal
3. Maintain backward compatibility with task storage
4. Ensure atomic writes for persistence
5. Update this README for user-facing changes

## Configuration

Edit `config.yaml` to customize:

```yaml
default_provider: dummy  # or your registered provider
working_dir: .            # Shell execution directory
shell_timeout: 30          # Command timeout (seconds)
max_steps: 10              # Maximum steps per task
```

## Limitations (Current)

- **Dummy provider only** - No real LLM integration yet (designed to be extended)
- **Single-threaded** - No parallel task execution
- **Simple tool support** - Only shell execution implemented
- **No streaming** - Full generation at once
- **Linux focus** - Not tested on other platforms

These are intentional design decisions for v1. They can be extended as needed.

## License

MIT License - do whatever you want with this code.

## Contributing

This is a personal project, but feel free to:
- Fork and modify for your own use
- Extend with new providers and tools
- Report bugs or suggest improvements
