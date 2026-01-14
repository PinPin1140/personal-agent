import { TaskStore } from '../core/taskStore';
import { ContextManager } from '../context/manager';

export class NewCommand {
  async execute(goal: string): Promise<void> {
    const contextManager = new ContextManager();
    const taskStore = new TaskStore();

    try {
      // Initialize context if needed
      const contextCreated = await contextManager.initialize(goal);

      if (contextCreated) {
        console.log('IRIS ▸ Created .context and initialized project. (step 1 complete)');
        return;
      }

      // Create new task
      const task = taskStore.create(goal);
      console.log(`IRIS ▸ Created task ${task.id}: ${task.goal}`);

      // Set as current task in context
      await contextManager.setCurrentTask({
        taskId: task.id,
        goal: task.goal,
        status: task.status,
        lastPhase: task.phase,
        summary: task.summary,
        readState: { filesRead: {} },
        plan: { intendedEdits: [] }
      });

    } catch (error) {
      console.error('Failed to create task:', error);
      process.exit(1);
    }
  }
}