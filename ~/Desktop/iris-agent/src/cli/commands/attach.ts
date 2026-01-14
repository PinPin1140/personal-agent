import { ContextManager } from '../context/manager';

export class AttachCommand {
  async execute(taskId: string): Promise<void> {
    const contextManager = new ContextManager();

    try {
      // Load context and journal
      const context = await contextManager.loadContext();
      const journal = await contextManager.loadJournal();

      if (!context.currentTask || context.currentTask.taskId !== taskId) {
        console.error('Task not found or not current task');
        process.exit(1);
      }

      // Display current status
      console.log(`IRIS ▸ ATTACHED ▸ ${context.currentTask.goal}`);
      console.log(`Status: ${context.currentTask.status}`);
      console.log(`Phase: ${context.currentTask.lastPhase}`);

      // Display recent journal entries
      if (journal.entries.length > 0) {
        console.log('\nRecent activity:');
        journal.entries.slice(-5).forEach(entry => {
          console.log(`  ${entry.ts}: ${entry.phase} - ${entry.desc}`);
        });
      }

      // In full implementation, this would attach to live execution
      console.log('\n(Live attachment not implemented in this demo)');

    } catch (error) {
      console.error('Failed to attach to task:', error);
      process.exit(1);
    }
  }
}