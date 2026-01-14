# IRIS Agent

A deterministic, local autonomous agent engine with CLI UI for task execution.

## Overview

IRIS is a task-based autonomous AI agent designed for local, deterministic execution. Unlike chat-based assistants, IRIS operates through a strict READ → PLAN → WRITE workflow with full context tracking and enforcement.

## Features

- **Deterministic Execution**: Strict READ → PLAN → WRITE enforcement
- **Context Management**: Atomic .context system with journal and checkpoints
- **CLI UI**: Enhanced terminal interface with live status and diff views
- **Skill System**: Formal enforcement skills for safe operation
- **Autonomous Operation**: No human confirmation loops

## Installation

```bash
npm install -g iris-agent
# or
git clone <repo>
cd iris-agent
npm install
npm run build
npm link
```

## Usage

### Initialize Project

```bash
cd your-project
iris new "Build a web application"
# Creates .context/ and initializes project
```

### List Tasks

```bash
iris list
```

### Run Task

```bash
iris run <task-id>
# Runs through READ → PLAN → WRITE phases
```

### Attach to Running Task

```bash
iris attach <task-id>
# Live status with autoscroll and diff previews
```

### View Logs

```bash
iris logs <task-id>
```

## Architecture

### .context System

IRIS maintains project state in `.context/`:

- `context.json`: Current project and task state
- `journal.json`: Action history with compaction
- `checkpoints/`: File backups before edits

### Enforcement Rules

1. **READ First**: All files to be edited must be read and checksummed
2. **PLAN Required**: Intended edits must be declared before writing
3. **Scoped Writes**: Only declared ranges can be modified
4. **Verification**: Post-write checks with rollback on failure
5. **Atomic Operations**: All context writes are atomic

### CLI UI

- **Status Line**: Live progress with phase and file info
- **Activity Stream**: Real-time action logging
- **Diff View**: Before/after previews with unified diff
- **Autoscroll**: Smart scrolling with keyboard control

## Configuration

Create `.env` from `.env.example`:

```bash
cp .env.example .env
# Edit settings as needed
```

## Development

```bash
npm run dev    # Watch mode
npm test       # Run tests
npm run build  # Build dist
```

## License

MIT