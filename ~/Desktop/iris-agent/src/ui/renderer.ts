import * as readline from 'readline';
import chalk from 'chalk';

export interface StatusLine {
  phase: string;
  description: string;
  progress?: number;
  file?: string;
  lines?: [number, number];
}

export class Renderer {
  private autoscroll: boolean = true;
  private lastStatusLine: string = '';
  private activityLines: string[] = [];
  private maxActivityLines: number = 50;

  constructor() {
    // Set up stdin for keyboard input if TTY
    if (process.stdin.isTTY) {
      process.stdin.setRawMode(true);
      process.stdin.on('data', (key: Buffer) => {
        this.handleKeypress(key);
      });
    }
  }

  /**
   * Update status line (in-place, no newline)
   */
  updateStatus(status: StatusLine): void {
    const progress = status.progress !== undefined ? ` ▌${'█'.repeat(Math.floor(status.progress / 10))}${'▰'.repeat(10 - Math.floor(status.progress / 10))} ${status.progress}%` : '';
    const fileInfo = status.file ? ` ▸ ${status.file}` : '';
    const lineInfo = status.lines ? ` lines ${status.lines[0]}–${status.lines[1]}` : '';

    const statusLine = `\x1b[1mIRIS ▸ ${status.phase}${fileInfo}${lineInfo}${progress}\x1b[0m`;

    // Clear previous line and write new one
    process.stdout.write('\r\x1b[K' + statusLine);
    this.lastStatusLine = statusLine;
  }

  /**
   * Add activity line
   */
  addActivity(line: string): void {
    const activityLine = `→ ${line}`;
    this.activityLines.push(activityLine);

    // Keep only recent lines
    if (this.activityLines.length > this.maxActivityLines) {
      this.activityLines = this.activityLines.slice(-this.maxActivityLines);
    }

    if (this.autoscroll) {
      this.renderActivityLine(activityLine);
    }
  }

  /**
   * Render activity line to stdout
   */
  private renderActivityLine(line: string): void {
    // Move to new line, print activity, then restore status line
    process.stdout.write('\n' + line + '\n');
    process.stdout.write(this.lastStatusLine);
  }

  /**
   * Clear screen and show header
   */
  showHeader(action: string): void {
    console.clear();
    console.log(chalk.bold(`IRIS ▸ ${action}`));
  }

  /**
   * Show error and exit
   */
  showError(error: string): void {
    console.log(chalk.red.bold(`ERR_${error}`));
    process.exit(1);
  }

  /**
   * Handle keypress for autoscroll control
   */
  private handleKeypress(key: Buffer): void {
    const keyStr = key.toString();

    if (keyStr === 'b' || keyStr === ' ') {
      // Toggle autoscroll ON and jump to bottom
      this.autoscroll = true;
      this.jumpToBottom();
      this.addActivity('Autoscroll enabled - jumped to bottom');
    } else if (keyStr === 'u') {
      // Disable autoscroll
      this.autoscroll = false;
      this.addActivity('Autoscroll disabled - user reading mode');
    } else if (key[0] === 27 || key[0] === 91) { // Arrow keys, etc.
      // Any navigation key disables autoscroll
      this.autoscroll = false;
    }
  }

  /**
   * Jump to bottom of activity feed
   */
  private jumpToBottom(): void {
    // Clear screen and reprint all activity lines + status
    console.clear();
    this.activityLines.forEach(line => console.log(line));
    process.stdout.write(this.lastStatusLine);
  }

  /**
   * Cleanup on exit
   */
  cleanup(): void {
    if (process.stdin.isTTY) {
      process.stdin.setRawMode(false);
    }
    process.stdout.write('\n');
  }
}