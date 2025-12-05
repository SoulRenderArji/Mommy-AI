import fs from 'fs/promises';
import path from 'path';
import { exec } from 'child_process';
import { logger } from './loggerService.js';
import { AppError } from '../utils/errors.js';

const PIPELINES_PATH = './pipelines';

/**
 * Pipeline Service
 * Provides safe methods for creating and executing shell scripts (pipelines).
 */

/**
 * Creates a new pipeline script file.
 * @param {string} args - A string containing the filename and script content, separated by a pipe `|`.
 */
export async function createPipeline(args) {
  const [filename, ...scriptParts] = args.split('|');
  const scriptContent = scriptParts.join('|').trim();

  if (!filename || !scriptContent || !filename.endsWith('.sh')) {
    throw new AppError('Invalid arguments. Expected: filename.sh|script content', 400);
  }

  const filePath = path.join(PIPELINES_PATH, path.basename(filename)); // Sanitize path
  await fs.mkdir(PIPELINES_PATH, { recursive: true });
  await fs.writeFile(filePath, `#!/bin/bash\n\n${scriptContent}`, { mode: 0o755 }); // Make it executable
  logger.info({ file: filePath }, 'Rowan has designed a new pipeline script.');
  return `New pipeline script "${filename}" has been created and is ready for execution.`;
}

/**
 * Executes a pipeline script.
 * @param {string} filename - The name of the script to execute.
 */
export async function executePipeline(filename) {
  if (!filename || !filename.endsWith('.sh')) {
    throw new AppError('Invalid arguments. A valid .sh filename is required.', 400);
  }

  const filePath = path.join(PIPELINES_PATH, path.basename(filename));

  try {
    await fs.access(filePath); // Check if file exists
  } catch (error) {
    throw new AppError(`Pipeline script "${filename}" not found.`, 404);
  }

  logger.warn({ file: filePath }, 'Daddy has commanded the execution of a pipeline.');

  // Execute the script but do not wait for it to finish.
  // This is for long-running tasks like installations.
  exec(filePath, (error, stdout, stderr) => {
    if (error) {
      logger.error({ err: error, stdout, stderr }, `Pipeline execution failed for ${filename}.`);
    } else {
      logger.info({ stdout, stderr }, `Pipeline execution finished for ${filename}.`);
    }
  });

  return `Pipeline "${filename}" has been started in the background.`;
}