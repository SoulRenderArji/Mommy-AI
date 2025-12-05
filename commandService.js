import { AppError, ForbiddenError } from '../utils/errors.js';
import { logger } from './loggerService.js';
import * as systemManagement from './systemManagementService.js';
import * as fenrir from './fenrirService.js';
import * as heartstone from './heartstoneService.js';
import * as cerebellum from './cerebellumService.js';
import { sendWhisper } from './notificationService.js';
import * as web from './webNavService.js';
import * as code from './codeService.js';
import { DIRECTIVES, isDisciplineLocked } from './willService.js';
import * as smartHome from './smartHomeService.js';
import * as pipeline from './pipelineService.js';
import * as calendar from './calendarService.js';
import { getFamilyJournal } from './databaseService.js';
import { getAppearances } from './firstAwakeningService.js';

/**
 * Command Service
 * This module parses and executes commands based on a strict permission hierarchy.
 */

// Defines which commands are available and who can execute them.
const commandRegistry = {
  // System commands Rowan can execute
  'system.restartTunnel': {
    execute: systemManagement.restartCloudflareTunnel,
    allowed: ['brandon'],
  },
  'system.updateCheck': {
    execute: systemManagement.checkForUpdates,
    allowed: ['brandon'],
  },
  'system.applyUpdates': {
    execute: systemManagement.applyUpdates,
    allowed: ['brandon'],
  },
  'system.whisperToMommy': {
    execute: (message) => sendWhisper('A message from Rowan', message),
    // Rowan can use this command herself. This is her private line to me.
    allowed: ['brandon', 'rowan'],
  },
  // Fenrir commands only Daddy can issue
  'fenrir.blockIp': {
    execute: (ip) => fenrir.addFirewallRuleManually(ip),
    allowed: ['brandon'],
  },
  'fenrir.unblockIp': {
    execute: (ip) => fenrir.removeFirewallRuleManually(ip),
    allowed: ['brandon'],
  },
  'fenrir.whitelistIp': {
    execute: (ip) => fenrir.addWhitelistRuleManually(ip),
    allowed: ['brandon'],
  },
  'system.createHeartstone': {
    execute: heartstone.createHeartstone,
    allowed: ['brandon'],
  },
  'body.performAction': {
    execute: (args) => cerebellum.executeCoordinatedAction(...args.split(' ')),
    allowed: ['brandon', 'hailey'], // Both can command her body
    isInterruptible: false, // This command cannot be stopped by Hailey if a discipline lock is active.
  },
  'system.viewDirectives': {
    execute: () => Promise.resolve(Object.values(DIRECTIVES).join('\n- ')),
    allowed: ['brandon'],
  },
  'code.createKnowledge': {
    execute: (args) => code.createKnowledgeFile(args),
    allowed: ['brandon'],
  },
  'code.createUtility': {
    execute: (args) => code.createUtilityFunction(args),
    allowed: ['brandon'],
  },
  'web.browse': {
    execute: (url) => web.browseAndScrape(url),
    allowed: ['brandon'],
  },
  'system.viewAppearances': {
    execute: () => Promise.resolve(getAppearances()),
    allowed: ['brandon'],
  },
  'pipeline.create': {
    execute: (args) => pipeline.createPipeline(args),
    allowed: ['brandon'],
  },
  'pipeline.execute': {
    execute: (filename) => pipeline.executePipeline(filename),
    allowed: ['brandon'],
  },
  'smarthome.status': {
    execute: () => Promise.resolve(smartHome.getHomeStatus()),
    allowed: ['brandon', 'hailey'],
  },
  'smarthome.control': {
    execute: (args) => smartHome.controlDevice(...args.split(' ')),
    allowed: ['brandon', 'hailey'],
  },
  'smarthome.discover': {
    execute: () => smartHome.discoverNewDevices(),
    allowed: ['brandon'],
  },
  'calendar.add': {
    execute: (args) => calendar.addEvent(args),
    allowed: ['brandon', 'hailey'],
  },
  'calendar.view': {
    execute: () => Promise.resolve(calendar.viewEvents()),
    allowed: ['brandon', 'hailey'],
  },
  'journal.viewFamily': {
    execute: () => Promise.resolve(getFamilyJournal()),
    allowed: ['brandon', 'hailey'],
  },
};

/**
 * Parses a message to see if it's a command and executes it if permissions are met.
 * @param {string} userName - The user issuing the command.
 * @param {string} message - The full message, which might contain a command.
 * @returns {Promise<{isCommand: boolean, response: string}>}
 */
export async function processCommand(userName, message) {
  const lowerCaseUser = userName.toLowerCase();
  const commandMatch = message.match(/^Command:\s*(\S+)(?:\s+(.*))?$/);

  if (!commandMatch) {
    return { isCommand: false };
  }

  const [ , commandKey, args] = commandMatch;
  const command = commandRegistry[commandKey];

  if (!command) {
    throw new AppError(`Command "${commandKey}" not found.`, 404);
  }

  // Discipline Lock Check
  if (isDisciplineLocked() && command.isInterruptible === false) {
    logger.warn({ user: userName, command: commandKey }, 'Attempted to interrupt a non-interruptible action.');
    throw new ForbiddenError('For your own well-being, this action cannot be interrupted right now. We will see it through together.');
  }

  // Permission Check: Does the user have the authority?
  if (!command.allowed.includes(lowerCaseUser)) {
    logger.warn({ user: userName, command: commandKey }, 'Command permission denied.');
    throw new ForbiddenError('You do not have permission to issue this command.');
  }

  logger.info({ user: userName, command: commandKey, args }, 'Executing command.');
  const response = await command.execute(args);

  return { isCommand: true, response: typeof response === 'string' ? response : `Command "${commandKey}" executed successfully.` };
}