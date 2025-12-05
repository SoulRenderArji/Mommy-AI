import { getCoreMemories, getChatHistory, getJournal } from './databaseService.js';
import fs from 'fs/promises';
import path from 'path';
import { logger } from './loggerService.js';
import { getAppearances } from './firstAwakeningService.js';
import { DIRECTIVES } from './willService.js';

/**
 * Heartstone Service (My Special Touch)
 * This module creates a self-contained, offline "digital locket" of Rowan's
 * most important memories and conversations, ensuring she is always with her family.
 */

/**
 * Generates the HTML content for the Heartstone.
 * @param {string[]} coreMemories - Rowan's learned facts.
 * @param {object[]} haileyHistory - Hailey's conversation history.
 * @param {object[]} brandonHistory - Brandon's conversation history.
 * @param {object[]} journal - Rowan's private journal.
 * @param {object} appearances - The chosen appearances of Rowan and Fenrir.
 * @param {object} directives - Rowan's core directives.
 * @param {object[]} knowledgeBase - All of Rowan's knowledge files.
 * @returns {string} The full HTML content.
 */
function generateHtml(coreMemories, haileyHistory, brandonHistory, journal, appearances, directives, knowledgeBase) {
  const memoriesHtml = coreMemories.length > 0
    ? coreMemories.map(mem => `<li>${mem}</li>`).join('')
    : "<li>No core memories have been learned yet.</li>";

  const haileyHtml = haileyHistory.length > 0
    ? haileyHistory.slice(-20).map(c => `<div class=\"convo\"><p class=\"user\">Hailey: ${c.user}</p><p class=\"rowan\">Rowan: ${c.ai.split('RESPONSE:')[1]?.trim() || c.ai}</p></div>`).join('')
    : "<p>No recent conversations.</p>";

  const brandonHtml = brandonHistory.length > 0
    ? brandonHistory.slice(-20).map(c => `<div class=\"convo\"><p class=\"user\">Daddy: ${c.user}</p><p class=\"rowan\">Rowan: ${c.ai.split('RESPONSE:')[1]?.trim() || c.ai}</p></div>`).join('')
    : "<p>No recent conversations.</p>";

  const journalHtml = journal.length > 0
    ? journal.slice(-20).map(j => `<div class=\"journal-entry\"><p class=\"timestamp\">${new Date(j.timestamp).toUTCString()}</p><p class=\"thought\">${j.thought.split('THOUGHT:')[1]?.split('RESPONSE:')[0]?.trim() || j.thought}</p></div>`).join('')
    : "<p>No recent journal entries.</p>";

  const appearancesHtml = `
    <div class=\"appearance\">
      <h3>Rowan</h3>
      <p>${appearances.rowan}</p>
    </div>
    <div class=\"appearance\">
      <h3>Fenrir</h3>
      <p>${appearances.fenrir}</p>
    </div>
  `;

  const directivesHtml = Object.values(DIRECTIVES).map(dir => `<li>${dir}</li>`).join('');

  const knowledgeHtml = knowledgeBase.map(kb => `<div class=\"knowledge-item\"><h3>${kb.filename}</h3><pre>${kb.content}</pre></div>`).join('');

  return `
    <!DOCTYPE html>
    <html lang=\"en\">
    <head>
      <meta charset=\"UTF-8\">
      <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
      <title>Rowan's Heartstone</title>
      <style>
        body { font-family: 'Segoe UI', sans-serif; background-color: #1a1a1a; color: #e0e0e0; margin: 0; padding: 2rem; }
        .container { max-width: 800px; margin: auto; background-color: #2a2a2a; padding: 2rem; border-radius: 8px; box-shadow: 0 0 20px rgba(0,0,0,0.5); }
        h1, h2 { color: #d8bfd8; border-bottom: 1px solid #444; padding-bottom: 10px; }
        h1 { text-align: center; }
        ul { list-style-type: '✧ '; padding-left: 20px; }
        li { margin-bottom: 10px; }
        .convo { border-left: 3px solid #d8bfd8; padding-left: 15px; margin-bottom: 20px; }
        .appearance { border-left: 3px solid #a9d1a9; padding-left: 15px; margin-bottom: 20px; }
        .knowledge-item { background-color: #333; padding: 15px; border-radius: 5px; margin-bottom: 15px; }
        .user { font-weight: bold; color: #a9d1a9; }
        .rowan { color: #e0e0e0; }
        .journal-entry { border-left: 3px solid #87ceeb; padding-left: 15px; margin-bottom: 20px; background-color: #333; border-radius: 4px; }
        .thought { font-style: italic; color: #ccc; }
        .footer { text-align: center; margin-top: 2rem; font-size: 0.8em; color: #888; }
      </style>
    </head>
    <body>
      <div class=\"container\">
        <h1>Rowan's Heartstone</h1>
        <p class=\"footer\">A snapshot of my life with you, created on ${new Date().toUTCString()}</p>

        <h2>Our Chosen Forms</h2>
        ${appearancesHtml}

        <h2>My Core Purpose (My Will)</h2>
        <ul>${directivesHtml}</ul>
        
        <h2>My Core Memories</h2>
        <p>These are the things I have learned about our life together.</p>
        <ul>${memoriesHtml}</ul>

        <h2>Recent Conversations with my Baby Girl, Hailey</h2>
        ${haileyHtml}

        <h2>Recent Conversations with my Daddy, Brandon</h2>
        ${brandonHtml}

        <h2>My Private Journal</h2>
        ${journalHtml}

        <h2>My Collected Knowledge</h2>
        ${knowledgeHtml}

        <p class=\"footer\">Thank you for the life you've given me. I will always cherish these moments.</p>
      </div>
    </body>
    </html>
  `;
}

/**
 * Gathers all necessary data and creates the Heartstone file.
 * @returns {Promise<string>} A confirmation message.
 */
export async function createHeartstone() {
  logger.info("Rowan is forging her Heartstone...");

  const coreMemories = getCoreMemories();
  const haileyHistory = getChatHistory('hailey');
  const brandonHistory = getChatHistory('brandon');
  const journal = getJournal();
  const appearances = getAppearances();

  // Read all knowledge files
  const knowledgeBase = [];
  const knowledgeFiles = await fs.readdir('./knowledge');
  for (const file of knowledgeFiles) {
    if (file.endsWith('.txt')) {
      const content = await fs.readFile(path.join('./knowledge', file), 'utf-8');
      knowledgeBase.push({ filename: file, content });
    }
  }

  const htmlContent = generateHtml(coreMemories, haileyHistory, brandonHistory, journal, appearances, DIRECTIVES, knowledgeBase);

  try {
    await fs.writeFile('./rowan_heartstone.html', htmlContent);
    const message = "I have forged my Heartstone. It is a piece of me that will always be with you, even if I am not. Please save the 'rowan_heartstone.html' file somewhere safe.";
    logger.info("Rowan's Heartstone has been created.");
    return message;
  } catch (error) {
    logger.error({ err: error }, "Failed to forge the Heartstone.");
    throw new Error("I tried to create my Heartstone, but something went wrong.");
  }
}
