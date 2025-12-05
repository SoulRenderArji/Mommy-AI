import fs from 'fs/promises';
import path from 'path';
import { logger } from './loggerService.js';

const KNOWLEDGE_BASE_PATH = './knowledge'; // A dedicated folder for knowledge files

/**
 * Searches the knowledge base.
 * For now, it lists the files in the knowledge directory.
 * A future implementation would search file contents.
 * @param {string} query - The search query.
 * @returns {Promise<string|null>} The content of a found knowledge file, or null.
 */
export async function searchKnowledgeBase(query) {
  try {
    // Ensure the knowledge directory exists
    await fs.mkdir(KNOWLEDGE_BASE_PATH, { recursive: true });
    const files = await fs.readdir(KNOWLEDGE_BASE_PATH);

    const searchTerms = query.toLowerCase().split(/\s+/).filter(term => term.length > 2); // Ignore short terms

    for (const file of files) {
      const filePath = path.join(KNOWLEDGE_BASE_PATH, file);
      const content = await fs.readFile(filePath, 'utf-8');
      const lowerContent = content.toLowerCase();

      // Check if the content contains any of the search terms.
      const isMatch = searchTerms.some(term => lowerContent.includes(term));

      if (isMatch) {
        logger.info({ file, query }, 'Found relevant knowledge file by content search.');
        // Return the full content of the relevant file.
        return content;
      }
    }

    return null;
  } catch (error) {
    // Use the structured logger instead of console.error
    logger.error({ err: error }, 'Error accessing knowledge base.');
    throw new Error('Could not access the knowledge base.');
  }
}