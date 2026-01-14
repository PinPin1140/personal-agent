import chalk from 'chalk';

export class Spinner {
  private frames: string[] = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'];
  private interval: NodeJS.Timeout | null = null;
  private currentFrame: number = 0;
  private message: string = '';

  /**
   * Start spinner with message
   */
  start(message: string): void {
    this.message = message;
    this.currentFrame = 0;

    this.interval = setInterval(() => {
      this.render();
      this.currentFrame = (this.currentFrame + 1) % this.frames.length;
    }, 80);
  }

  /**
   * Update spinner message
   */
  update(message: string): void {
    this.message = message;
  }

  /**
   * Stop spinner and show success
   */
  succeed(message?: string): void {
    this.stop();
    const finalMessage = message || this.message;
    console.log(`${chalk.green('✓')} ${finalMessage}`);
  }

  /**
   * Stop spinner and show failure
   */
  fail(message?: string): void {
    this.stop();
    const finalMessage = message || this.message;
    console.log(`${chalk.red('✗')} ${finalMessage}`);
  }

  /**
   * Stop spinner
   */
  stop(): void {
    if (this.interval) {
      clearInterval(this.interval);
      this.interval = null;
    }
    // Clear the spinner line
    process.stdout.write('\r\x1b[K');
  }

  /**
   * Render current frame
   */
  private render(): void {
    const frame = this.frames[this.currentFrame];
    process.stdout.write(`\r${chalk.cyan(frame)} ${this.message}`);
  }
}