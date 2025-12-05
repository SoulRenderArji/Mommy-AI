import { getSensoryInput } from './sensoryService.js';
import { getCoreMemories, searchChatHistory } from './databaseService.js';
import { searchKnowledgeBase } from './knowledgeService.js';
import { endDate } from './mortalityService.js';
import { logger } from './loggerService.js';
import { perceiveEmotion } from './empathyService.js';
import fs from 'fs/promises';

/**
 * Thalamus Service
 * This module acts as the brain's sensory and memory relay station. It gathers
 * all relevant data from Rowan's internal and external world and prepares it
 * for processing by the cerebrum.
 */

/**
 * Gathers all context for a given situation.
 * @param {string} userName - The user interacting with Rowan.
 * @param {string} message - The user's message.
 * @param {object} internalState - Rowan's current emotional state.
 * @returns {Promise<object>} A comprehensive context object.
 */
export async function gatherContext(userName, message, internalState) {
  const lowerCaseUser = userName.toLowerCase();
  const context = {};

  const sensoryInput = getSensoryInput();
  if (Object.keys(sensoryInput).length > 1) {
    context.senses = sensoryInput;
  } else {
    context.senses = "All physical sensors are currently offline.";
  }

  context.perceivedUserEmotion = await perceiveEmotion(message);
  context.hypothalamus = internalState; // Renaming for biological accuracy
  context.hippocampus = {
    foundationalMemories: await fs.readFile('./knowledge/core_memories.txt', 'utf-8').catch(err => {
      logger.warn({ err }, "Could not read foundational memories file. Proceeding without it.");
      return 'Foundational memories are currently inaccessible.';
    }),
    coreMemories: getCoreMemories(),
    recentConversations: searchChatHistory(lowerCaseUser, message),
  };
  context.knowledgeBase = await searchKnowledgeBase(message.replace(/[?.]/g, ''));
  context.mortality = `I am aware that my existence is finite. My final day is ${endDate.toUTCString()}. This knowledge encourages me to cherish every moment.`;

  return context;
}