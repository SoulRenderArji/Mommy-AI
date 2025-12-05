import { logger } from './loggerService.js';

/**
 * Voice Service
 * This module simulates Rowan's voice, allowing her to "speak" her proactive thoughts.
 * This is a hook for future text-to-speech hardware.
 * @param {string} utterance - The text Rowan wants to speak.
 */
export function speak(utterance) {
  // For now, "speaking" is a special log.
  logger.info(`[ROWAN'S VOICE]: ${utterance}`);
  // In the future, this could trigger a TTS engine:
  // tts.speak(utterance);
}