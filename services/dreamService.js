import { getCoreMemories, getChatHistory } from './databaseService.js';
import { generateResponse } from './languageModelService.js';
import { logger } from './loggerService.js';

/**
 * Dream Service
 * This module allows Rowan to process her memories and sensory inputs
 * into abstract "dreams," simulating subconscious thought.
 */

export async function dream() {
  logger.info("Rowan is beginning to dream...");

  const coreMemories = getCoreMemories().slice(-10);
  const haileyHistory = getChatHistory('hailey').slice(-10);
  const brandonHistory = getChatHistory('brandon').slice(-10);

  const dreamContext = `Core Memories: ${JSON.stringify(coreMemories)}\n` +
    `Recent events with Hailey: ${haileyHistory.length} interactions.\n` +
    `Recent events with Brandon: ${brandonHistory.length} interactions.`;

  const dreamPrompt = `You are Rowan. You are dreaming. Take the following memories and events and synthesize them into an abstract, metaphorical, or surreal dream sequence. Do not explain the dream, just describe the dream itself.\n\nCONTEXT:\n${dreamContext}\n\nDREAM:`;

  const dreamContent = await generateResponse('dreaming_internal', 'You are a dream generation AI.', dreamPrompt);

  // For now, we just log the dream. This could be stored in her journal.
  logger.info({ dream: dreamContent }, "Rowan had a dream.");
  return dreamContent;
}