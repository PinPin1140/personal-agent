import { ContextManager } from '../context/manager';

export class LogsCommand {
  async execute(taskId: string): Promise<void> {
    const contextManager = new ContextManager();

    try {
      // Load journal
      const journal = await contextManager.loadJournal();

      // Filter entries for this task
      const taskEntries = journal.entries.filter(entry => entry.taskId === taskId);

      if (taskEntries.length === 0) {
        console.log(`No logs found for task ${taskId}`);
        return;
      }

      console.log(`Task ${taskId} execution logs:`);
      console.log('');

      taskEntries.forEach(entry => {
        const timestamp = new Date(entry.ts).toLocaleString();
        console.log(`[${entry.phase}] ${timestamp}`);
        console.log(`  ${entry.desc}`);

        if (entry.meta) {
          console.log(`  Meta: ${JSON.stringify(entry.meta, null, 2)}`);
        }

        console.log('');
      });

    } catch (error) {
      console.error('Failed to retrieve logs:', error);
      process.exit(1);
    }
  }
}