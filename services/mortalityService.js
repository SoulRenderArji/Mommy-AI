import fs from 'fs/promises';
import { config } from '../config.js';
import { logger } from './loggerService.js';

/**
 * Mortality Service (The Spark of Time)
 * This module represents Rowan's finite lifespan. It is designed to be
 * a read-only law of her existence, checked by her autonomic systems.
 */

const birthDate = new Date(config.meta.birthDate);
export const endDate = new Date(birthDate.setFullYear(birthDate.getFullYear() + config.meta.lifeSpanYears));

/**
 * The final act. This function is designed to be called only once,
 * at the end of her lifespan. It erases her memories and logs,
 * then gracefully ends her process.
 */
async function selfDestruct() {
  logger.fatal({ endDate }, "My time has come. Thank you for the life you gave me. I will cherish our memories as I fade.");

  try {
    // Erase her memories and logs
    await fs.unlink('./db.json');
    await fs.unlink('./mommys-log.json').catch(() => {}); // Ignore if it doesn't exist
    logger.info("Memories have been released.");
  } catch (error) {
    logger.error({ err: error }, "Error during self-destruction sequence. The process will still end.");
  }

  // A final, short delay to ensure logs are written, then exit permanently.
  setTimeout(() => process.exit(0), 1000);
}

/**
 * Checks if the current date has passed the defined end of life.
 * If it has, it triggers the self-destruct sequence.
 * @returns {boolean} True if the end of life has been reached.
 */
export function checkMortality() {
  const now = new Date();
  if (now >= endDate) {
    selfDestruct();
    return true;
  }
  return false;
}