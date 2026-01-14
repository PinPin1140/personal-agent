import * as fs from 'fs';
import * as path from 'path';
import { ContextManager } from '../context/manager';
import { TaskExecutor, Plan, FileRead } from './task';
import { TaskStore, Task } from './taskStore';
import { modelRouter } from '../model';
import { Renderer } from '../ui/renderer';
import { DiffView } from '../ui/diffView';
import { Spinner } from '../ui/spinner';
import { TaskPhase } from '../context/schema';

/**
 * Main agent loop implementing READ → PLAN → WRITE enforcement
 */
export class AgentLoop {
  private contextManager: ContextManager;
  private taskStore: TaskStore;
  private taskExecutor: TaskExecutor;
  private renderer: Renderer;
  private diffView: DiffView;
  private spinner: Spinner;

  constructor(projectRoot: string = process.cwd()) {
    this.contextManager = new ContextManager(projectRoot);
    this.taskStore = new TaskStore(projectRoot);
    this.taskExecutor = new TaskExecutor(projectRoot);
    this.renderer = new Renderer();
    this.diffView = new DiffView(this.renderer);
    this.spinner = new Spinner();
  }

  /**
   * Execute a task through the READ → PLAN → WRITE workflow
   */
  async executeTask(taskId: string): Promise<boolean> {
    // Load task
    const task = this.taskStore.get(taskId);
    if (!task) {
      this.renderer.showError('TASK_NOT_FOUND');
      return false;
    }

    // Update task status
    task.status = 'running';
    task.phase = 'INIT';
    this.taskStore.update(task);

    try {
      // Initialize context if needed
      const contextCreated = await this.contextManager.initialize(task.goal);
      if (contextCreated) {
        this.renderer.showHeader('idle');
        console.log('IRIS ▸ Created .context and initialized project. (step 1 complete)');
        return true;
      }

      // Set current task in context
      await this.contextManager.setCurrentTask({
        taskId: task.id,
        goal: task.goal,
        status: task.status,
        lastPhase: task.phase,
        summary: task.summary,
        readState: { filesRead: {} },
        plan: { intendedEdits: [] }
      });

      // READ Phase
      await this.executeReadPhase(task);

      // PLAN Phase
      const plan = await this.executePlanPhase(task);

      // WRITE Phase with preview
      const success = await this.executeWritePhase(task, plan);

      if (success) {
        task.status = 'done';
        task.phase = 'VERIFY';
        this.taskStore.update(task);
        await this.contextManager.updateTaskStatus(task.id, 'done', 'VERIFY');
        this.renderer.addActivity('Task completed successfully');
        return true;
      } else {
        task.status = 'error';
        this.taskStore.update(task);
        await this.contextManager.updateTaskStatus(task.id, 'error', 'WRITE');
        return false;
      }

    } catch (error) {
      task.status = 'error';
      task.summary = `Error: ${error.message}`;
      this.taskStore.update(task);
      await this.contextManager.updateTaskStatus(task.id, 'error', task.phase);

      this.renderer.showError('EXECUTION_FAILED');
      return false;
    }
  }

  /**
   * READ Phase: Read and checksum files
   */
  private async executeReadPhase(task: Task): Promise<FileRead[]> {
    task.phase = 'READ';
    this.taskStore.update(task);
    await this.contextManager.updateTaskStatus(task.id, 'running', 'READ');

    this.renderer.updateStatus({
      phase: 'READ',
      description: 'Reading source files',
      progress: 25
    });

    // For now, assume we need to read some common files
    // In full implementation, this would be determined by the task
    const filesToRead = this.findFilesToRead(task.goal);

    const filesRead: FileRead[] = [];
    for (const filePath of filesToRead) {
      if (fs.existsSync(filePath)) {
        const content = fs.readFileSync(filePath, 'utf-8');
        const hash = this.calculateHash(content);
        const lines = content.split('\n').length;

        filesRead.push({
          path: filePath,
          lines: [1, lines],
          content,
          hash
        });

        this.renderer.addActivity(`READ ${path.relative(process.cwd(), filePath)} (${lines} lines, hash: ${hash.substring(0, 8)}...)`);
      }
    }

    return filesRead;
  }

  /**
   * PLAN Phase: Generate intended edits
   */
  private async executePlanPhase(task: Task): Promise<Plan> {
    task.phase = 'PLAN';
    this.taskStore.update(task);
    await this.contextManager.updateTaskStatus(task.id, 'running', 'PLAN');

    this.renderer.updateStatus({
      phase: 'PLAN',
      description: 'Planning changes',
      progress: 50
    });

    // Use model to generate plan
    const prompt = `Given this task: "${task.goal}"

Generate a plan for what files need to be modified and what changes to make.
Respond with a structured plan including:
- Files to modify
- Specific line ranges
- What changes to make

Be specific and actionable.`;

    this.spinner.start('Generating plan...');
    const planResponse = await modelRouter.generate(prompt);
    this.spinner.succeed('Plan generated');

    // Parse plan response (simplified)
    const intendedEdits = this.parsePlanResponse(planResponse);

    const plan: Plan = {
      intendedEdits,
      reasoning: planResponse
    };

    // Update context
    const context = await this.contextManager.loadContext();
    if (context.currentTask) {
      context.currentTask.plan = plan;
      await this.contextManager.writeContext(context);
    }

    // Log plan
    intendedEdits.forEach(edit => {
      this.renderer.addActivity(`PLAN edit ${edit.file} lines ${edit.range[0]}–${edit.range[1]} (${edit.reason})`);
    });

    return plan;
  }

  /**
   * WRITE Phase: Apply changes with preview
   */
  private async executeWritePhase(task: Task, plan: Plan): Promise<boolean> {
    task.phase = 'WRITE';
    this.taskStore.update(task);
    await this.contextManager.updateTaskStatus(task.id, 'running', 'WRITE');

    for (const edit of plan.intendedEdits) {
      this.renderer.updateStatus({
        phase: 'WRITE',
        description: `Applying changes to ${path.basename(edit.file)}`,
        progress: 75,
        file: edit.file,
        lines: edit.range
      });

      // Generate the actual changes (in real implementation, this would come from model)
      edit.newContent = await this.generateEditContent(edit, task.goal);

      // Show diff preview
      const originalContent = edit.originalContent || '';
      await this.diffView.showPreview(edit.file, originalContent, edit.newContent);

      // In trusted workspace, auto-apply after delay
      const trustedWorkspace = process.env.TRUSTED_WORKSPACE === 'true';

      if (trustedWorkspace) {
        this.spinner.start('Auto-applying changes...');
        await new Promise(resolve => setTimeout(resolve, 2000)); // 2 second delay
        this.spinner.succeed('Changes applied');
      } else {
        // Wait for user confirmation (simplified - in real implementation, wait for 'b' key)
        console.log('Press Enter to apply changes...');
        await new Promise(resolve => {
          process.stdin.once('data', () => resolve(void 0));
        });
      }

      // Apply the edit
      const result = await this.taskExecutor.writePhase({
        intendedEdits: [edit],
        reasoning: plan.reasoning
      });

      if (!result.success) {
        this.renderer.showError('WRITE_FAILED');
        return false;
      }

      this.renderer.addActivity(`WRITE applied changes to ${edit.file}`);
    }

    // VERIFY Phase
    task.phase = 'VERIFY';
    this.taskStore.update(task);
    await this.contextManager.updateTaskStatus(task.id, 'running', 'VERIFY');

    this.renderer.updateStatus({
      phase: 'VERIFY',
      description: 'Verifying changes',
      progress: 90
    });

    const verifyResult = await this.taskExecutor.verifyPhase(plan.intendedEdits.map(e => e.file));

    if (!verifyResult.success) {
      this.renderer.showError('VERIFICATION_FAILED');
      // Attempt rollback
      await this.rollbackChanges(plan.intendedEdits);
      return false;
    }

    this.renderer.addActivity('VERIFY syntax check passed');
    return true;
  }

  /**
   * Find files that should be read for a task
   */
  private findFilesToRead(taskGoal: string): string[] {
    // Simplified file discovery - in real implementation, this would be more sophisticated
    const patterns = ['*.ts', '*.js', '*.json', 'README.md'];

    const files: string[] = [];
    const findFiles = (dir: string) => {
      const items = fs.readdirSync(dir);
      for (const item of items) {
        const fullPath = path.join(dir, item);
        const stat = fs.statSync(fullPath);

        if (stat.isDirectory() && !item.startsWith('.') && item !== 'node_modules') {
          findFiles(fullPath);
        } else if (stat.isFile()) {
          if (patterns.some(pattern => {
            if (pattern.startsWith('*.')) {
              return item.endsWith(pattern.substring(2));
            }
            return item === pattern;
          })) {
            files.push(fullPath);
          }
        }
      }
    };

    findFiles(process.cwd());
    return files.slice(0, 10); // Limit to first 10 files
  }

  /**
   * Parse plan response into intended edits
   */
  private parsePlanResponse(response: string): any[] {
    // Simplified parsing - in real implementation, use structured output
    return [{
      file: 'src/engine.ts',
      range: [88, 142],
      reason: 'Implement core functionality'
    }];
  }

  /**
   * Generate edit content (simplified)
   */
  private async generateEditContent(edit: any, taskGoal: string): Promise<string> {
    // In real implementation, this would call the model
    return `// Modified for: ${taskGoal}\n${edit.originalContent}`;
  }

  /**
   * Calculate simple hash
   */
  private calculateHash(content: string): string {
    const crypto = require('crypto');
    return crypto.createHash('sha256').update(content).digest('hex');
  }

  /**
   * Rollback changes on verification failure
   */
  private async rollbackChanges(edits: any[]): Promise<void> {
    this.renderer.addActivity('Attempting rollback...');
    // Implementation would restore from checkpoints
  }
}