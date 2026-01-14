import * as fs from 'fs';
import * as path from 'path';
import { calculateChecksum } from '../util/checksum';
import { TaskPhase } from '../context/schema';

export interface FileRead {
  path: string;
  lines: [number, number]; // [start, end] 1-based
  content: string;
  hash: string;
}

export interface IntendedEdit {
  file: string;
  range: [number, number]; // [start, end] 1-based
  reason: string;
  originalContent?: string;
  newContent?: string;
}

export interface Plan {
  intendedEdits: IntendedEdit[];
  reasoning: string;
}

export interface ExecutionResult {
  success: boolean;
  output?: string;
  error?: string;
  filesModified?: string[];
}

/**
 * Core task execution engine
 */
export class TaskExecutor {
  private projectRoot: string;

  constructor(projectRoot: string = process.cwd()) {
    this.projectRoot = projectRoot;
  }

  /**
   * READ phase: Read and checksum files to be edited
   */
  async readPhase(plan: Plan): Promise<FileRead[]> {
    const filesRead: FileRead[] = [];

    for (const edit of plan.intendedEdits) {
      const fullPath = path.resolve(this.projectRoot, edit.file);

      if (!fs.existsSync(fullPath)) {
        throw new Error(`File not found: ${edit.file}`);
      }

      const content = fs.readFileSync(fullPath, 'utf-8');
      const hash = calculateChecksum(fullPath);

      // Extract lines for the intended edit range
      const lines = content.split('\n');
      const startLine = Math.max(1, edit.range[0]);
      const endLine = Math.min(lines.length, edit.range[1]);
      const rangeContent = lines.slice(startLine - 1, endLine).join('\n');

      filesRead.push({
        path: edit.file,
        lines: [startLine, endLine],
        content: rangeContent,
        hash
      });

      // Store original content for diff
      edit.originalContent = rangeContent;
    }

    return filesRead;
  }

  /**
   * PLAN phase: Generate intended edits based on task goal
   */
  async planPhase(taskGoal: string, filesRead: FileRead[]): Promise<Plan> {
    // This would typically call the model to generate a plan
    // For now, return a basic plan structure
    const intendedEdits: IntendedEdit[] = filesRead.map(file => ({
      file: file.path,
      range: file.lines,
      reason: `Implement changes for: ${taskGoal}`,
    }));

    return {
      intendedEdits,
      reasoning: `Planning to modify ${filesRead.length} file(s) to achieve: ${taskGoal}`
    };
  }

  /**
   * WRITE phase: Apply the intended edits
   */
  async writePhase(plan: Plan): Promise<ExecutionResult> {
    const filesModified: string[] = [];

    try {
      for (const edit of plan.intendedEdits) {
        if (!edit.newContent) {
          continue; // Skip edits without new content
        }

        const fullPath = path.resolve(this.projectRoot, edit.file);

        // Read current content
        const currentContent = fs.readFileSync(fullPath, 'utf-8');
        const lines = currentContent.split('\n');

        // Apply edit to specified range
        const startLine = edit.range[0] - 1; // Convert to 0-based
        const endLine = edit.range[1];

        const beforeLines = lines.slice(0, startLine);
        const afterLines = lines.slice(endLine);
        const newLines = edit.newContent.split('\n');

        const newContent = [...beforeLines, ...newLines, ...afterLines].join('\n');

        // Write atomically
        const tempPath = `${fullPath}.tmp`;
        fs.writeFileSync(tempPath, newContent);
        fs.renameSync(tempPath, fullPath);

        filesModified.push(edit.file);
      }

      return {
        success: true,
        filesModified
      };
    } catch (error) {
      return {
        success: false,
        error: `Write failed: ${error.message}`,
        filesModified
      };
    }
  }

  /**
   * VERIFY phase: Check that edits are syntactically correct
   */
  async verifyPhase(filesModified: string[]): Promise<ExecutionResult> {
    for (const file of filesModified) {
      const fullPath = path.resolve(this.projectRoot, file);

      // Basic syntax check for TypeScript/JavaScript
      if (file.endsWith('.ts') || file.endsWith('.js')) {
        try {
          // Use Node.js to check syntax
          const { spawn } = require('child_process');
          await new Promise((resolve, reject) => {
            const child = spawn('node', ['--check', fullPath], {
              stdio: 'pipe'
            });
            child.on('close', (code: number) => {
              if (code === 0) {
                resolve(void 0);
              } else {
                reject(new Error(`Syntax check failed for ${file}`));
              }
            });
            child.on('error', reject);
          });
        } catch (error) {
          return {
            success: false,
            error: `Verification failed: ${error.message}`
          };
        }
      }
    }

    return { success: true };
  }
}