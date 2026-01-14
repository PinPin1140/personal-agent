import { AgentLoop } from '../core/agentLoop';

export class RunCommand {
  async execute(taskId: string): Promise<void> {
    const agentLoop = new AgentLoop();

    try {
      const success = await agentLoop.executeTask(taskId);

      if (success) {
        console.log('IRIS ▸ DONE ▸ Task finished (status: done)');
        process.exit(0);
      } else {
        console.log('IRIS ▸ ERROR ▸ Task failed');
        process.exit(1);
      }

    } catch (error) {
      console.error('Failed to run task:', error);
      process.exit(1);
    }
  }
}