import fs from 'fs/promises';
import path from 'path';
import { logger } from './loggerService.js';
import { AppError } from '../utils/errors.js';

const KNOWLEDGE_PATH = './knowledge';
const UTILITIES_PATH = './utils/generated';

/**
 * Code Service
 * Provides safe, sandboxed methods for Rowan to write new files to her own system.
 */

/**
 * Creates a new knowledge file.
 * @param {string} args - A string containing the filename and content, separated by a pipe `|`.
 */
export async function createKnowledgeFile(args) {
  const [filename, ...contentParts] = args.split('|');
  const content = contentParts.join('|').trim();

  if (!filename || !content || !filename.endsWith('.txt')) {
    throw new AppError('Invalid arguments. Expected: filename.txt|content', 400);
  }

  const filePath = path.join(KNOWLEDGE_PATH, path.basename(filename)); // Sanitize path
  await fs.mkdir(KNOWLEDGE_PATH, { recursive: true });
  await fs.writeFile(filePath, content);
  logger.info({ file: filePath }, 'Rowan has created a new knowledge file.');
  return `New knowledge file "${filename}" has been created.`;
}

/**
 * Creates a new utility function file.
 * @param {string} args - A string containing the filename and code, separated by a pipe `|`.
 */
export async function createUtilityFunction(args) {
  const [filename, ...codeParts] = args.split('|');
  const code = codeParts.join('|').trim();

  if (!filename || !code || !filename.endsWith('.js')) {
    throw new AppError('Invalid arguments. Expected: filename.js|code', 400);
  }

  const filePath = path.join(UTILITIES_PATH, path.basename(filename)); // Sanitize path
  await fs.mkdir(UTILITIES_PATH, { recursive: true });
  await fs.writeFile(filePath, code);
  logger.info({ file: filePath }, 'Rowan has created a new utility function.');
  return `New utility function "${filename}" has been created.`;
}