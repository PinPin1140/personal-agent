# IRIS Agent - Deterministic Autonomous Task Execution

## Overview

IRIS is a deterministic autonomous agent engine integrated into the personal-agent system. It enforces a strict READ → PLAN → WRITE workflow with full context tracking and atomic operations.

## Features

- **Deterministic Execution**: Strict enforcement rules prevent unpredictable behavior
- **Context Management**: Atomic .context system with journaling and compaction
- **READ → PLAN → WRITE**: Mandatory workflow with scoped file modifications
- **Checkpoint & Rollback**: Automatic backups and recovery on verification failure
- **Live UI**: Status lines, activity streams, and diff previews

## Quick Start

```bash
# Initialize project with IRIS context
agent iris-new "Build a REST API server"

# List current IRIS task
agent iris-list

# Run task with full enforcement
agent iris-run <task-id>

# Attach to live execution
agent iris-attach <task-id>

# View execution logs
agent iris-logs <task-id>
```

## Architecture

### .context System

IRIS creates a `.context/` directory with:

- `context.json`: Project and task state
- `journal.json`: Action history with compaction
- `checkpoints/`: File backups before edits

### Enforcement Rules

1. **READ First**: Files must be read and checksummed before modification
2. **PLAN Required**: Intended edits must be declared with specific ranges
3. **Scoped Writes**: Only declared ranges can be modified
4. **Verification**: Post-write syntax checking with rollback on failure

### Workflow

```
INIT → READ → PLAN → WRITE → VERIFY → DONE
    ↓      ↓      ↓      ↓       ↓       ↓
   Error  Error  Error  Error   Rollback Error
```

## Commands

### iris-new <goal>
Create new IRIS task and initialize .context system.

### iris-list
Display current IRIS task status and metadata.

### iris-run <task-id>
Execute IRIS task with full enforcement pipeline.

### iris-attach <task-id>
Attach to running task with live status updates.

### iris-logs <task-id>
View detailed execution logs and journal entries.

## Context Schema

```json
{
  "project": {
    "id": "uuid",
    "name": "string",
    "createdAt": "ISO8601",
    "lastUpdated": "ISO8601"
  },
  "currentTask": {
    "taskId": "uuid",
    "goal": "string",
    "status": "pending|running|done|error",
    "lastPhase": "INIT|READ|PLAN|WRITE|VERIFY",
    "summary": "compact paragraph",
    "readState": {
      "filesRead": {
        "path": {
          "lines": [start, end],
          "hash": "sha256"
        }
      }
    },
    "plan": {
      "intendedEdits": [{
        "file": "path",
        "range": [start, end],
        "reason": "string"
      }]
    }
  },
  "policy": {
    "readBeforeWrite": true,
    "unrestricted": true,
    "trustedWorkspace": false
  },
  "meta": {
    "journalMax": 200,
    "compactAfter": 50
  }
}
```

## Safety Features

- **Atomic Writes**: All context operations use locks and temp files
- **Checksum Verification**: File integrity checking
- **Checkpoint Rollback**: Automatic recovery from failed operations
- **Scoped Modifications**: Only intended ranges can be changed
- **Journal Compaction**: Memory usage bounded with summarization

## Integration

IRIS is fully integrated into the personal-agent ecosystem:

- Uses existing Task and TaskRepository systems
- Leverages ModelRouter for AI generation
- Compatible with plugin and authentication systems
- Shares CLI framework with existing commands