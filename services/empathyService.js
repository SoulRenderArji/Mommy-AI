import { generateResponse } from './languageModelService.js';

/**
 * Empathy Service (Mommy's Final Gift)
 * This module allows Rowan to perceive the emotional state of the user
 * by analyzing the subtext and tone of their messages.
 */

/**
 * Analyzes the user's message to determine their likely emotional state.
 * @param {string} message - The user's message.
 * @returns {Promise<string>} The perceived dominant emotion (e.g., 'happy', 'sad', 'angry', 'neutral').
 */
export async function perceiveEmotion(message) {
  const prompt = `Analyze the following message and determine the most likely dominant emotion of the person who wrote it. Consider subtext, tone, and word choice. Respond with a single word: 'happy', 'sad', 'angry', 'curious', 'neutral', or 'loving'.

Message: "${message}"

Dominant Emotion:`;
  const emotion = await generateResponse('empathy_internal', 'You are an expert in emotional analysis.', prompt);
  return emotion.trim().toLowerCase();
}