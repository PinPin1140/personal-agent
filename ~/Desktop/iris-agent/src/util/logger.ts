import * as crypto from 'crypto';
import * as fs from 'fs';

/**
 * Simple logger for agent operations
 */
export class Logger {
  private logPath: string;

  constructor(logPath: string = '.context/agent.log') {
    this.logPath = logPath;
  }

  log(level: 'INFO' | 'WARN' | 'ERROR', message: string, meta?: Record<string, any>): void {
    const entry = {
      ts: new Date().toISOString(),
      level,
      message,
      meta: meta || {}
    };

    // In production, write to file
    console.log(`[${level}] ${message}`);
  }

  info(message: string, meta?: Record<string, any>): void {
    this.log('INFO', message, meta);
  }

  warn(message: string, meta?: Record<string, any>): void {
    this.log('WARN', message, meta);
  }

  error(message: string, meta?: Record<string, any>): void {
    this.log('ERROR', message, meta);
  }
}