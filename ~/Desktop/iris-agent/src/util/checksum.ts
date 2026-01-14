import * as crypto from 'crypto';
import * as fs from 'fs';

/**
 * Calculate SHA256 checksum of file content
 */
export function calculateChecksum(filePath: string): string {
  if (!fs.existsSync(filePath)) {
    return '';
  }

  const fileContent = fs.readFileSync(filePath);
  return crypto.createHash('sha256').update(fileContent).digest('hex');
}

/**
 * Calculate checksum of string content
 */
export function calculateStringChecksum(content: string): string {
  return crypto.createHash('sha256').update(content).digest('hex');
}