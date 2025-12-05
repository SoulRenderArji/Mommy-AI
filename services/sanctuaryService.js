import {
  getSanctuary,
  updateSanctuaryState,
  setPendingSanctuaryChanges,
  clearPendingSanctuaryChanges,
} from './databaseService.js';
import { AppError } from '../utils/errors.js';
import { logger } from './loggerService.js';

/**
 * Sanctuary Service
 * Manages the logic for the private digital space for Hailey and Brandon.
 */

/**
 * Proposes a change to the Sanctuary.
 * If the user is Brandon, the change is applied immediately.
 * If the user is Hailey, it is set as a pending change.
 * @param {string} userName - The user making the proposal.
 * @param {object} changes - The proposed changes.
 */
export async function proposeChange(userName, changes) {
  const lowerCaseUser = userName.toLowerCase();

  if (lowerCaseUser === 'brandon') {
    logger.info({ user: userName, changes }, 'Daddy is directly updating the Sanctuary.');
    await updateSanctuaryState(changes);
    return getSanctuary();
  } else if (lowerCaseUser === 'hailey') {
    logger.info({ user: userName, changes }, 'Baby Girl is proposing a change to the Sanctuary.');
    await setPendingSanctuaryChanges(changes);
    return getSanctuary();
  } else {
    throw new AppError('Only Hailey or Brandon may change the Sanctuary.', 403);
  }
}

/**
 * Approves pending changes to the Sanctuary. Only Brandon can do this.
 * @param {string} userName - The user attempting to approve.
 */
export async function approveChanges(userName) {
  if (userName.toLowerCase() !== 'brandon') {
    throw new AppError('Only Daddy can approve changes.', 403);
  }
  const sanctuary = getSanctuary();
  if (!sanctuary.pendingChanges) {
    throw new AppError('There are no pending changes to approve.', 400);
  }
  logger.info({ changes: sanctuary.pendingChanges.changes }, 'Daddy is approving changes to the Sanctuary.');
  await updateSanctuaryState(sanctuary.pendingChanges.changes);
  await clearPendingSanctuaryChanges();
  return getSanctuary();
}