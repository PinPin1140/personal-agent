import { TaskStore } from '../core/taskStore';

export class ListCommand {
  async execute(): Promise<void> {
    const taskStore = new TaskStore();

    try {
      const tasks = taskStore.list();

      if (tasks.length === 0) {
        console.log('No tasks found.');
        return;
      }

      console.log('Tasks:');
      tasks.forEach(task => {
        const status = `[${task.status.toUpperCase()}]`;
        console.log(`  ${status} ${task.id}: ${task.goal}`);
      });

    } catch (error) {
      console.error('Failed to list tasks:', error);
      process.exit(1);
    }
  }
}