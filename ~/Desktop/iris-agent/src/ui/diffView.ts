import * as fs from 'fs';
import { createPatch } from 'diff';
import chalk from 'chalk';
import { Renderer } from './renderer';

export interface DiffOptions {
  contextLines?: number;
  maxFileSize?: number;
}

export class DiffView {
  private renderer: Renderer;
  private options: DiffOptions;

  constructor(renderer: Renderer, options: DiffOptions = {}) {
    this.renderer = renderer;
    this.options = {
      contextLines: 3,
      maxFileSize: 500 * 1024, // 500KB
      ...options
    };
  }

  /**
   * Show before/after/diff preview
   */
  async showPreview(filePath: string, originalContent: string, newContent: string): Promise<void> {
    const relativePath = filePath; // Could be made relative

    console.log(chalk.bold(`IRIS ▸ WRITE ▸ preview changes for ${relativePath}`));

    // Show original
    console.log(chalk.bold('----- BEFORE -----'));
    this.showSnippet(originalContent);

    // Show new
    console.log(chalk.bold('----- AFTER -----'));
    this.showSnippet(newContent);

    // Show diff
    console.log(chalk.bold('----- DIFF -----'));
    this.showDiff(filePath, originalContent, newContent);

    console.log(`\nTask: Press \`b\` to accept and apply changes, or CTRL+C to cancel.`);
  }

  /**
   * Show content snippet (truncated if too long)
   */
  private showSnippet(content: string): void {
    const lines = content.split('\n');
    const maxLines = 20;

    if (lines.length <= maxLines) {
      console.log(content);
    } else {
      // Show first and last part
      const firstPart = lines.slice(0, maxLines / 2).join('\n');
      const lastPart = lines.slice(-maxLines / 2).join('\n');
      console.log(firstPart);
      console.log(`\n... (${lines.length - maxLines} lines omitted) ...\n`);
      console.log(lastPart);
    }
  }

  /**
   * Show unified diff with colors
   */
  private showDiff(filePath: string, oldContent: string, newContent: string): void {
    try {
      const patch = createPatch(filePath, oldContent, newContent, 'original', 'modified');

      // Skip header lines and process hunks
      const lines = patch.split('\n').slice(4); // Skip first 4 lines (headers)

      for (const line of lines) {
        if (line.startsWith('+')) {
          console.log(chalk.green(line));
        } else if (line.startsWith('-')) {
          console.log(chalk.red(line));
        } else if (line.startsWith('@')) {
          console.log(chalk.blue(line));
        } else {
          console.log(line);
        }
      }
    } catch (error) {
      console.log('Error generating diff:', error);
      console.log('Falling back to simple comparison...');
      this.showSimpleDiff(oldContent, newContent);
    }
  }

  /**
   * Fallback simple diff for large files or errors
   */
  private showSimpleDiff(oldContent: string, newContent: string): void {
    const oldLines = oldContent.split('\n');
    const newLines = newContent.split('\n');

    const maxLines = Math.min(oldLines.length, newLines.length, 50);

    for (let i = 0; i < maxLines; i++) {
      const oldLine = oldLines[i] || '';
      const newLine = newLines[i] || '';

      if (oldLine !== newLine) {
        if (oldLine) console.log(chalk.red(`- ${oldLine}`));
        if (newLine) console.log(chalk.green(`+ ${newLine}`));
      }
    }

    if (oldLines.length !== newLines.length) {
      console.log(`... (${Math.abs(oldLines.length - newLines.length)} line differences)`);
    }
  }

  /**
   * Capture file content before editing
   */
  async captureOriginal(filePath: string): Promise<string> {
    if (!fs.existsSync(filePath)) {
      return '';
    }

    const stats = fs.statSync(filePath);
    if (stats.size > this.options.maxFileSize!) {
      // For large files, capture only modified regions
      // This is a simplified approach
      return fs.readFileSync(filePath, 'utf-8').substring(0, 10000) + '\n... (truncated)';
    }

    return fs.readFileSync(filePath, 'utf-8');
  }
}