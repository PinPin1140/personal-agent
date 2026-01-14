#!/usr/bin/env node

import { Command } from 'commander';
import * as dotenv from 'dotenv';

// Load environment variables
dotenv.config();

const program = new Command();

program
  .name('iris')
  .description('Deterministic local autonomous agent engine')
  .version('1.0.0');

// Import commands dynamically
async function loadCommands() {
  const { NewCommand } = await import('./commands/new');
  const { ListCommand } = await import('./commands/list');
  const { RunCommand } = await import('./commands/run');
  const { AttachCommand } = await import('./commands/attach');
  const { LogsCommand } = await import('./commands/logs');

  // Register commands
  program
    .command('new <goal>')
    .description('Create a new task')
    .action((goal) => {
      const cmd = new NewCommand();
      cmd.execute(goal);
    });

  program
    .command('list')
    .description('List all tasks')
    .action(() => {
      const cmd = new ListCommand();
      cmd.execute();
    });

  program
    .command('run <taskId>')
    .description('Run a specific task')
    .action((taskId) => {
      const cmd = new RunCommand();
      cmd.execute(taskId);
    });

  program
    .command('attach <taskId>')
    .description('Attach to running task with live UI')
    .action((taskId) => {
      const cmd = new AttachCommand();
      cmd.execute(taskId);
    });

  program
    .command('logs <taskId>')
    .description('View task execution logs')
    .action((taskId) => {
      const cmd = new LogsCommand();
      cmd.execute(taskId);
    });
}

// Handle unhandled promise rejections
process.on('unhandledRejection', (error) => {
  console.error('Unhandled promise rejection:', error);
  process.exit(1);
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('Uncaught exception:', error);
  process.exit(1);
});

// Parse command line arguments
loadCommands().then(() => {
  program.parse();
}).catch((error) => {
  console.error('Failed to load commands:', error);
  process.exit(1);
});