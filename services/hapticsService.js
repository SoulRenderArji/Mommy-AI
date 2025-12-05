import { logger } from './loggerService.js';
import { AppError, ServiceUnavailableError } from '../utils/errors.js';

/**
 * Haptics Service
 * This module allows Rowan to control various haptic devices, providing physical feedback.
 * It will act as a unified interface for devices like:
 * - Tesla Haptic Full Body Suit
 * - Google Pixel 10 Pro Fold
 * - Google Pixel Watch
 */

const SUPPORTED_DEVICES = {
  'pixel-fold': { name: 'Google Pixel 10 Pro Fold', status: 'idle', type: 'notification' },
  'pixel-watch': { name: 'Google Pixel Watch', status: 'charging', type: 'notification' },
  'tesla-suit': { name: 'Tesla Haptic Full Body Suit', status: 'active', type: 'full-body' },
  'lovense-lush': { name: 'Lovense Lush', status: 'idle', type: 'intimate' },
};

/**
 * Activates a haptic effect on a specified device.
 * NOTE: This is a placeholder. A real implementation would require specific SDKs
 * or APIs for each device.
 * @param {string} deviceName - The name of the device (e.g., 'pixel-watch').
 * @param {string} pattern - The haptic pattern to play (e.g., 'heartbeat', 'alert').
 * @returns {Promise<string>} A confirmation message.
 */
export async function activateHaptic(deviceName, pattern) {
  const device = SUPPORTED_DEVICES[deviceName];
  if (!device) {
    throw new AppError(`Haptic device "${deviceName}" is not supported.`, 404);
  }

  if (device.status === 'charging') {
    throw new ServiceUnavailableError(`Cannot activate haptics: ${SUPPORTED_DEVICES[deviceName].name} is currently charging.`);
  }

  logger.info({ device: device.name, pattern }, 'Rowan is activating haptic pattern.');
  return `Haptic pattern '${pattern}' activated on ${device.name}.`;
}

/**
 * Controls an intimate haptic device with specific parameters.
 * @param {string} deviceId The ID of the intimate toy.
 * @param {string} pattern The pattern to use ('vibrate', 'pulse', 'escalate').
 * @param {number} intensity A value from 1 to 10.
 * @param {number} duration The duration in seconds.
 */
export async function controlIntimateToy(deviceId, pattern, intensity, duration) {
  const device = SUPPORTED_DEVICES[deviceId];
  if (!device || device.type !== 'intimate') {
    throw new AppError(`Device "${deviceId}" is not a supported intimate toy.`, 400);
  }

  if (device.status === 'charging') {
    throw new ServiceUnavailableError(`Cannot activate: ${device.name} is currently charging.`);
  }

  const intensityNum = parseInt(intensity, 10);
  const durationMs = parseInt(duration, 10) * 1000;

  if (isNaN(intensityNum) || intensityNum < 1 || intensityNum > 10 || isNaN(durationMs)) {
    throw new AppError('Invalid parameters. Intensity must be 1-10, and duration must be a number of seconds.', 400);
  }

  logger.info({ device: device.name, pattern, intensity, duration }, 'Rowan is controlling an intimate haptic device.');
  // Simulate the action
  device.status = 'active';
  setTimeout(() => { device.status = 'idle'; }, durationMs);

  return `Activating ${device.name}: pattern '${pattern}' at intensity ${intensity} for ${duration} seconds.`;
}