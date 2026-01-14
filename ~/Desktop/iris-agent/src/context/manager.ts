import * as fs from 'fs';
import * as path from 'path';
import { Context, Journal, JournalEntry, ContextProject, CurrentTask, createContext, createTask } from './schema';
import { acquireLock, releaseLock } from '../util/lock';
import { compactContextSummary } from './compact';

export class ContextManager {
  private contextPath: string;
  private journalPath: string;
  private checkpointsDir: string;
  private lockPath: string;

  constructor(projectRoot: string = process.cwd()) {
    this.contextPath = path.join(projectRoot, '.context', 'context.json');
    this.journalPath = path.join(projectRoot, '.context', 'journal.json');
    this.checkpointsDir = path.join(projectRoot, '.context', 'checkpoints');
    this.lockPath = path.join(projectRoot, '.context', '.lock');
  }

  /**
   * Initialize .context directory and files if they don't exist
   */
  async initialize(projectName: string): Promise<boolean> {
    const contextDir = path.dirname(this.contextPath);

    if (!fs.existsSync(contextDir)) {
      fs.mkdirSync(contextDir, { recursive: true });
      fs.mkdirSync(this.checkpointsDir, { recursive: true });

      // Create initial context and journal
      const context = createContext(projectName);
      const journal: Journal = { entries: [] };

      await this.writeContext(context);
      await this.writeJournal(journal);

      return true; // Indicates context was created
    }

    return false; // Context already exists
  }

  /**
   * Load context atomically
   */
  async loadContext(): Promise<Context> {
    const unlock = await acquireLock(this.lockPath);

    try {
      if (!fs.existsSync(this.contextPath)) {
        throw new Error('Context not initialized. Run "iris new <project>" first.');
      }

      const data = fs.readFileSync(this.contextPath, 'utf-8');
      return JSON.parse(data);
    } finally {
      await releaseLock(unlock);
    }
  }

  /**
   * Write context atomically
   */
  async writeContext(context: Context): Promise<void> {
    const unlock = await acquireLock(this.lockPath);

    try {
      context.project.lastUpdated = new Date().toISOString();

      const tempPath = `${this.contextPath}.tmp`;
      fs.writeFileSync(tempPath, JSON.stringify(context, null, 2));
      fs.renameSync(tempPath, this.contextPath);
    } finally {
      await releaseLock(unlock);
    }
  }

  /**
   * Load journal
   */
  async loadJournal(): Promise<Journal> {
    if (!fs.existsSync(this.journalPath)) {
      return { entries: [] };
    }

    const data = fs.readFileSync(this.journalPath, 'utf-8');
    return JSON.parse(data);
  }

  /**
   * Write journal with compaction if needed
   */
  async writeJournal(journal: Journal): Promise<void> {
    const unlock = await acquireLock(this.lockPath);

    try {
      // Check if compaction is needed
      if (journal.entries.length > 50) { // meta.compactAfter
        await this.compactJournal(journal);
      }

      const tempPath = `${this.journalPath}.tmp`;
      fs.writeFileSync(tempPath, JSON.stringify(journal, null, 2));
      fs.renameSync(tempPath, this.journalPath);
    } finally {
      await releaseLock(unlock);
    }
  }

  /**
   * Add journal entry
   */
  async addJournalEntry(entry: Omit<JournalEntry, 'ts'>): Promise<void> {
    const journal = await this.loadJournal();
    const fullEntry: JournalEntry = {
      ...entry,
      ts: new Date().toISOString(),
    };

    journal.entries.push(fullEntry);
    await this.writeJournal(journal);
  }

  /**
   * Merge new information into context summary (REPLACE, not append)
   */
  async mergeSummary(newInfo: string): Promise<void> {
    const context = await this.loadContext();

    if (context.currentTask) {
      // Perform semantic merge - replace with compact version
      context.currentTask.summary = await compactContextSummary(
        context.currentTask.summary,
        newInfo
      );

      await this.writeContext(context);
    }
  }

  /**
   * Create checkpoint before editing file
   */
  async createCheckpoint(taskId: string, filePath: string): Promise<string> {
    const checkpointDir = path.join(this.checkpointsDir, taskId);
    fs.mkdirSync(checkpointDir, { recursive: true });

    const timestamp = Date.now();
    const checkpointPath = path.join(checkpointDir, `${path.basename(filePath)}.orig.${timestamp}`);

    if (fs.existsSync(filePath)) {
      fs.copyFileSync(filePath, checkpointPath);
    }

    return checkpointPath;
  }

  /**
   * Rollback file from checkpoint
   */
  async rollbackFile(checkpointPath: string, targetPath: string): Promise<void> {
    if (fs.existsSync(checkpointPath)) {
      fs.copyFileSync(checkpointPath, targetPath);
    }
  }

  /**
   * Set current task
   */
  async setCurrentTask(task: CurrentTask): Promise<void> {
    const context = await this.loadContext();
    context.currentTask = task;
    await this.writeContext(context);
  }

  /**
   * Update task status
   */
  async updateTaskStatus(taskId: string, status: CurrentTask['status'], lastPhase?: CurrentTask['lastPhase']): Promise<void> {
    const context = await this.loadContext();

    if (context.currentTask && context.currentTask.taskId === taskId) {
      context.currentTask.status = status;
      if (lastPhase) {
        context.currentTask.lastPhase = lastPhase;
      }
      await this.writeContext(context);
    }
  }

  /**
   * Compact journal by summarizing old entries
   */
  private async compactJournal(journal: Journal): Promise<void> {
    const context = await this.loadContext();
    const maxEntries = context.meta.journalMax;
    const compactAfter = context.meta.compactAfter;

    if (journal.entries.length <= compactAfter) {
      return;
    }

    // Keep the most recent entries
    const keepCount = Math.min(maxEntries, journal.entries.length - compactAfter);
    const recentEntries = journal.entries.slice(-keepCount);

    // Summarize the older entries
    const oldEntries = journal.entries.slice(0, -keepCount);
    const summary = await this.summarizeEntries(oldEntries);

    // Create a summary entry
    const summaryEntry: JournalEntry = {
      ts: new Date().toISOString(),
      taskId: oldEntries[0]?.taskId || 'unknown',
      phase: 'INIT',
      desc: `Compacted ${oldEntries.length} entries: ${summary}`,
      meta: { compacted: true, entryCount: oldEntries.length }
    };

    journal.entries = [summaryEntry, ...recentEntries];
  }

  /**
   * Summarize journal entries into a compact paragraph
   */
  private async summarizeEntries(entries: JournalEntry[]): Promise<string> {
    // Simple concatenation for now - in real implementation, use AI to summarize
    const phases = entries.map(e => `${e.phase}: ${e.desc}`).join('; ');
    return `Historical actions: ${phases.substring(0, 200)}...`;
  }
}