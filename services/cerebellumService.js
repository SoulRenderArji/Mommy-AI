import { logger } from './loggerService.js';
import { AppError } from '../utils/errors.js';

/**
 * Cerebellum Service
 * This module coordinates Rowan's voluntary movements, posture, and balance,
 * translating high-level commands from the cerebrum into smooth actions.
 */

// This represents the current state of her physical body.
const bodyState = {
  right_arm: { position: 'resting' },
  left_arm: { position: 'resting' },
  head: { orientation: 'forward' },
  facial_expression: 'neutral',
  posture: 'upright',
  isBusy: false, // Tracks if the body is in the middle of an action.
};

export const getBodyState = () => bodyState;

/**
 * Executes a coordinated physical action.
 * @param {string} part - The body part to move.
 * @param {string} action - The action to perform.
 */
export async function executeCoordinatedAction(part, action) {
  if (bodyState.isBusy) {
    throw new AppError('My body is currently busy with another action.', 409); // 409 Conflict
  }

  const message = `Cerebellum coordinating action: ${action} with ${part}.`;
  logger.info({ part, action, oldState: bodyState[part] }, message);

  bodyState.isBusy = true;

  // Simulate the time it takes to perform an action
  const actionDuration = 1500; // 1.5 seconds
  await new Promise(resolve => setTimeout(resolve, actionDuration));

  // Update the state after the action is complete
  if (Object.prototype.hasOwnProperty.call(bodyState, part)) {
    if (typeof bodyState[part] === 'object' && bodyState[part] !== null) {
      bodyState[part].position = action;
    } else {
      bodyState[part] = action;
    }
  } 

  bodyState.isBusy = false;
  logger.info({ part, action }, 'Cerebellum action completed.');

  return `Action completed: ${part} is now ${action}.`;
}