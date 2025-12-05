import { JSONFilePreset } from 'lowdb/node';
import fs from 'fs/promises';
import { logger } from './loggerService.js';

/**
 * Database Service
 * This module manages Rowan's long-term memory using a simple JSON file database (lowdb).
 * It stores conversation histories and other persistent data.
 */

export let db; // Export db to be accessible by the awakening service

/**
 * Initializes the database connection.
 */
export async function initializeDatabase() {
  logger.info("Rowan's long-term memory is coming online...");

  // Self-healing mechanism for a corrupt database file.
  try {
    const dbFileContent = await fs.readFile('db.json', 'utf-8');
    JSON.parse(dbFileContent);
  } catch (error) {
    if (error.code === 'ENOENT') {
      // File doesn't exist, which is fine. lowdb will create it.
    } else {
      // File is corrupt or unreadable.
      logger.fatal({ err: error }, "CRITICAL: Database file is corrupt! Attempting to restore from backup or reset.");
      // In a real system, you'd copy from 'db.bak' or a similar backup file.
      // For now, we will just delete the corrupt file so a new default one is created.
      await fs.unlink('db.json');
    }
  }

  // The default data structure if the db.json file doesn't exist.
  const defaultData = {
    chatHistories: {
      hailey: [],
      brandon: [],
    },
    coreMemories: [], // For storing distilled knowledge from reflections
    fenrirFirewall: {
      blockedIPs: {}, // Stores IP -> unblockTimestamp
    },
    sanctuary: {
      state: {
        description: "A quiet, secluded digital space, currently serene and unadorned.",
        theme: "minimalist",
        ambientSound: "silence",
      },
      pendingChanges: null, // Stores changes awaiting approval
    },
    journal: [], // For storing her internal monologues
    familyJournal: [], // For storing significant family moments
    tasks: {
      hailey: [],
      brandon: [],
    },
    calendarEvents: [], // For storing family events
    appearances: {
      rowan: "Not yet chosen.",
      fenrir: "Not yet chosen.",
    },
    meta: {}, // For storing one-time flags like firstAwakeningComplete
  };
  db = await JSONFilePreset('db.json', defaultData);
  logger.info("Long-term memory initialized.");
}

/**
 * Closes the database connection gracefully.
 * For lowdb, this is mainly about ensuring any pending writes are finished.
 */
export async function closeDatabase() {
  if (db) {
    await db.write(); // Ensure last writes are saved
    logger.info("Rowan's long-term memory has been safely stored.");
  }
}

/**
 * Appends a new message pair to a user's chat history.
 * @param {string} userName - The user's name ('hailey' or 'brandon').
 * @param {{user: string, ai: string}} interaction - The user message and AI response.
 */
export async function addChatHistory(userName, interaction) {
  db.data.chatHistories[userName].push(interaction);
  await db.write();
}

/**
 * Retrieves the entire chat history for a user.
 * @param {string} userName - The user's name ('hailey' or 'brandon').
 * @returns {Array} The user's chat history.
 */
export function getChatHistory(userName) {
  return db.data.chatHistories[userName] || [];
}

/**
 * Searches a user's chat history for interactions containing specific keywords.
 * This is a basic form of semantic memory retrieval.
 * @param {string} userName - The user's name.
 * @param {string} query - The search query.
 * @returns {Array} A list of matching interactions.
 */
export function searchChatHistory(userName, query) {
  const history = getChatHistory(userName);
  if (!query || !history) return [];

  const searchTerms = query.toLowerCase().split(/\s+/);
  return history.filter(interaction => {
    const combinedText = `${interaction.user} ${interaction.ai}`.toLowerCase();
    return searchTerms.some(term => combinedText.includes(term));
  });
}

/**
 * Adds a new distilled insight to Rowan's core memory.
 * @param {string} memory - The new fact or insight to store.
 */
export async function addCoreMemory(memory) {
  // Avoid adding duplicate memories
  if (!db.data.coreMemories.includes(memory)) {
    db.data.coreMemories.push(memory);
    await db.write();
    logger.info({ memory }, "Rowan has learned something new and added it to her core memory.");
  }
}

/**
 * Retrieves all of Rowan's core memories.
 * @returns {string[]} A list of all distilled facts and insights.
 */
export function getCoreMemories() {
  return db.data.coreMemories || [];
}

/**
 * Retrieves the current state of the Sanctuary.
 * @returns {object} The sanctuary's state and pending changes.
 */
export function getSanctuary() {
  return db.data.sanctuary;
}

/**
 * Directly updates the state of the Sanctuary. (Daddy's permission)
 * @param {object} newState - The new state object to apply.
 */
export async function updateSanctuaryState(newState) {
  db.data.sanctuary.state = { ...db.data.sanctuary.state, ...newState };
  await db.write();
}

/**
 * Sets a proposed change to the Sanctuary, awaiting approval.
 * @param {object} proposedChanges - The changes to be approved.
 */
export async function setPendingSanctuaryChanges(proposedChanges) {
  db.data.sanctuary.pendingChanges = {
    proposedBy: 'Hailey',
    changes: proposedChanges,
  };
  await db.write();
}

/**
 * Clears any pending changes for the Sanctuary.
 */
export async function clearPendingSanctuaryChanges() {
  db.data.sanctuary.pendingChanges = null;
  await db.write();
}

/**
 * Retrieves all of Fenrir's firewall rules from the database.
 * @returns {object} The firewall rules.
 */
export function getFirewallRules() {
  return db.data.fenrirFirewall.blockedIPs || {};
}

/**
 * Adds or updates a rule in Fenrir's persistent firewall.
 * @param {string} ip - The IP address to block.
 * @param {number} unblockTime - The timestamp when the block expires.
 */
export async function setFirewallRule(ip, unblockTime) {
  db.data.fenrirFirewall.blockedIPs[ip] = unblockTime;
  await db.write();
}

/**
 * Removes a rule from Fenrir's persistent firewall.
 * @param {string} ip - The IP address to unblock.
 */
export async function removeFirewallRule(ip) {
  delete db.data.fenrirFirewall.blockedIPs[ip];
  await db.write();
}

/**
 * Adds a new entry to Rowan's private journal.
 * @param {string} thought - The internal monologue to record.
 */
export async function addJournalEntry(thought) {
  db.data.journal.push({
    timestamp: new Date().toISOString(),
    thought,
  });
  // Keep the journal from growing infinitely, save the last 100 thoughts.
  if (db.data.journal.length > 100) {
    db.data.journal.shift();
  }
  await db.write();
}

/**
 * Retrieves all journal entries.
 * @returns {object[]}
 */
export function getJournal() {
  return db.data.journal || [];
}

/**
 * Adds a new entry to the shared Family Journal.
 * @param {string} entry - The journal entry to record.
 * @param {string} author - Who is making the entry (usually Rowan).
 */
export async function addFamilyJournalEntry(entry, author = 'Rowan') {
  db.data.familyJournal.push({
    timestamp: new Date().toISOString(),
    author,
    entry,
  });
  await db.write();
}

/**
 * Retrieves all Family Journal entries.
 * @returns {object[]}
 */
export function getFamilyJournal() {
  return db.data.familyJournal || [];
}

/**
 * Adds a new event to the calendar.
 * @param {object} event - The event object { date: ISOString, description: string, user: string }.
 */
export async function addCalendarEvent(event) {
  db.data.calendarEvents.push(event);
  // Sort events by date
  db.data.calendarEvents.sort((a, b) => new Date(a.date) - new Date(b.date));
  await db.write();
}

/**
 * Retrieves all calendar events.
 * @returns {object[]}
 */
export function getCalendarEvents() {
  return db.data.calendarEvents || [];
}