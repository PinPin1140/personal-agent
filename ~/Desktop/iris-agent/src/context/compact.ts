/**
 * Context compaction utilities
 */

/**
 * Merge new information into existing summary by semantic combination
 * Always produces a single compact paragraph, never appends
 */
export async function compactContextSummary(existing: string, newInfo: string): Promise<string> {
  if (!existing.trim()) {
    return newInfo.substring(0, 500); // Limit initial summary
  }

  if (!newInfo.trim()) {
    return existing;
  }

  // Simple semantic merge - combine and deduplicate
  const combined = `${existing} ${newInfo}`.trim();

  // Remove duplicates and redundant phrases
  const sentences = combined.split(/[.!?]+/).filter(s => s.trim().length > 0);
  const uniqueSentences = new Set(sentences.map(s => s.trim()));

  // Take most relevant sentences (prioritize recent info)
  const result = Array.from(uniqueSentences).slice(-3).join('. ') + '.';

  return result.substring(0, 800); // Keep under limit
}