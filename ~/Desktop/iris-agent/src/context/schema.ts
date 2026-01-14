import { v4 as uuidv4 } from 'uuid';

export interface ContextProject {
  id: string;
  name: string;
  createdAt: string;
  lastUpdated: string;
}

export interface ReadStateFile {
  lines: [number, number]; // [start, end] (1-based)
  hash: string; // sha256
}

export interface IntendedEdit {
  file: string;
  range: [number, number]; // [start, end] (1-based)
  reason: string;
}

export interface Plan {
  intendedEdits: IntendedEdit[];
}

export interface ReadState {
  filesRead: Record<string, ReadStateFile>; // path -> file info
}

export type TaskStatus = 'pending' | 'running' | 'paused' | 'done' | 'error';
export type TaskPhase = 'INIT' | 'READ' | 'PLAN' | 'WRITE' | 'VERIFY';

export interface CurrentTask {
  taskId: string;
  goal: string;
  status: TaskStatus;
  lastPhase: TaskPhase;
  summary: string;
  readState: ReadState;
  plan: Plan;
}

export interface Policy {
  readBeforeWrite: boolean;
  unrestricted: boolean;
  trustedWorkspace: boolean;
}

export interface Meta {
  journalMax: number;
  compactAfter: number;
}

export interface Context {
  project: ContextProject;
  currentTask: CurrentTask | null;
  policy: Policy;
  meta: Meta;
}

export interface JournalEntry {
  ts: string; // ISO8601
  taskId: string;
  phase: TaskPhase;
  desc: string;
  meta?: Record<string, any>;
}

export interface Journal {
  entries: JournalEntry[];
}

// Factory functions
export function createProject(name: string): ContextProject {
  const now = new Date().toISOString();
  return {
    id: uuidv4(),
    name,
    createdAt: now,
    lastUpdated: now,
  };
}

export function createTask(goal: string): CurrentTask {
  return {
    taskId: uuidv4(),
    goal,
    status: 'pending',
    lastPhase: 'INIT',
    summary: '',
    readState: { filesRead: {} },
    plan: { intendedEdits: [] },
  };
}

export function createContext(projectName: string): Context {
  return {
    project: createProject(projectName),
    currentTask: null,
    policy: {
      readBeforeWrite: true,
      unrestricted: true,
      trustedWorkspace: false,
    },
    meta: {
      journalMax: 200,
      compactAfter: 50,
    },
  };
}