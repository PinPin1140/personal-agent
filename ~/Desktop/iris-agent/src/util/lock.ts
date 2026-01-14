import * as fs from 'fs';
import * as path from 'path';

/**
 * Simple file-based locking mechanism
 */
export async function acquireLock(lockPath: string): Promise<() => Promise<void>> {
  const lockFile = `${lockPath}.lock`;

  // Simple spin lock - in production, use proper locking
  while (fs.existsSync(lockFile)) {
    await new Promise(resolve => setTimeout(resolve, 10));
  }

  // Create lock file with PID
  fs.writeFileSync(lockFile, process.pid.toString());

  return async () => {
    try {
      fs.unlinkSync(lockFile);
    } catch (e) {
      // Lock file may have been cleaned up already
    }
  };
}

export async function releaseLock(unlock: () => Promise<void>): Promise<void> {
  await unlock();
}