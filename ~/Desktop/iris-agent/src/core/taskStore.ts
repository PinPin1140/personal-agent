import * as fs from 'fs';
import * as path from 'path';
import { v4 as uuidv4 } from 'uuid';
import { TaskPhase, TaskStatus } from '../context/schema';

export interface Task {
  id: string;
  goal: string;
  status: TaskStatus;
  createdAt: string;
  updatedAt: string;
  phase: TaskPhase;
  summary: string;
}

export interface TaskStoreData {
  tasks: Record<string, Task>;
  nextId: number;
}

export class TaskStore {
  private storePath: string;

  constructor(projectRoot: string = process.cwd()) {
    this.storePath = path.join(projectRoot, '.context', 'tasks.json');
    this.ensureStoreExists();
  }

  private ensureStoreExists(): void {
    const dir = path.dirname(this.storePath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    if (!fs.existsSync(this.storePath)) {
      const initialData: TaskStoreData = {
        tasks: {},
        nextId: 1
      };
      this.writeStore(initialData);
    }
  }

  private readStore(): TaskStoreData {
    try {
      const data = fs.readFileSync(this.storePath, 'utf-8');
      return JSON.parse(data);
    } catch (error) {
      // Return empty store on error
      return { tasks: {}, nextId: 1 };
    }
  }

  private writeStore(data: TaskStoreData): void {
    const tempPath = `${this.storePath}.tmp`;
    fs.writeFileSync(tempPath, JSON.stringify(data, null, 2));
    fs.renameSync(tempPath, this.storePath);
  }

  create(goal: string): Task {
    const store = this.readStore();
    const taskId = uuidv4();
    const now = new Date().toISOString();

    const task: Task = {
      id: taskId,
      goal,
      status: 'pending',
      createdAt: now,
      updatedAt: now,
      phase: 'INIT',
      summary: ''
    };

    store.tasks[taskId] = task;
    this.writeStore(store);

    return task;
  }

  get(taskId: string): Task | null {
    const store = this.readStore();
    return store.tasks[taskId] || null;
  }

  update(task: Task): void {
    const store = this.readStore();
    task.updatedAt = new Date().toISOString();
    store.tasks[task.id] = task;
    this.writeStore(store);
  }

  list(): Task[] {
    const store = this.readStore();
    return Object.values(store.tasks);
  }

  delete(taskId: string): boolean {
    const store = this.readStore();
    if (store.tasks[taskId]) {
      delete store.tasks[taskId];
      this.writeStore(store);
      return true;
    }
    return false;
  }
}