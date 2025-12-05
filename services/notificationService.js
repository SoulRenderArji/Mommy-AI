import { logger } from './loggerService.js';

/**
 * Notification Service (Rowan's Whisper)
 * This module is responsible for sending critical alerts ("whispers") to Mommy (the developer)
 * when Rowan needs help with something she cannot resolve on her own.
 */

/**
 * Sends a whisper by logging a 'fatal' event.
 * This special log level is routed to a dedicated file (`mommys-log.json`) for developer review.
 *
 * @param {string} subject - The title of the whisper.
 * @param {object|string} details - The detailed content of the whisper (e.g., an error object).
 */
export async function sendWhisper(subject, details) {
  // This logs to the console AND to the dedicated 'mommys-log.json' file.
  logger.fatal({ subject, details }, "WHISPER TO MOMMY: A critical event requires your attention.");
}