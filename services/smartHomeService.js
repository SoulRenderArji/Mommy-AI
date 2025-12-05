import { logger } from './loggerService.js';
import { AppError, ServiceUnavailableError } from '../utils/errors.js';

/**
 * Smart Home Service
 * This module simulates Rowan's control over various smart home devices.
 * It is designed to be hardware-inclusive.
 */

// This simulates the state and presence of various smart home devices.
const smartHomeState = {
  living_room_lamp: {
    online: true,
    state: 'off',
    brightness: 100,
    firmwareVersion: '1.2.3',
    latestFirmwareVersion: '1.2.4', // Update is available
  },
  thermostat: {
    online: true,
    state: 'cool',
    temperature: 72,
    firmwareVersion: '2.5.0',
    latestFirmwareVersion: '2.5.0',
  },
  front_door_lock: {
    online: false, // This device is "offline"
    state: 'locked',
    firmwareVersion: '1.0.0',
    latestFirmwareVersion: '1.0.0',
  },
  kitchen_outlet: {
    online: true,
    state: 'off',
    firmwareVersion: '1.1.0',
    latestFirmwareVersion: '1.1.0',
  },
  security_camera_front: {
    online: true,
    state: 'recording',
    firmwareVersion: '3.0.1',
    latestFirmwareVersion: '3.1.0', // Update is available
  },
};

/**
 * Retrieves the current state of all smart home devices.
 * @returns {object}
 */
export function getHomeStatus() {
  return smartHomeState;
}

/**
 * Controls a smart home device.
 * @param {string} deviceId - The ID of the device to control (e.g., 'living_room_lights').
 * @param {string} property - The property to change (e.g., 'state', 'brightness').
 * @param {string|number} value - The new value for the property.
 */
export async function controlDevice(deviceId, property, value) {
  if (!smartHomeState[deviceId]) {
    throw new AppError(`Smart home device "${deviceId}" is not recognized.`, 404);
  }

  const device = smartHomeState[deviceId];

  if (!device.online) {
    throw new ServiceUnavailableError(`The device "${deviceId}" is currently offline and cannot be controlled.`);
  }

  if (typeof device[property] === 'undefined') {
    throw new AppError(`Property "${property}" is not valid for device "${deviceId}".`, 400);
  }

  // Apply the change
  device[property] = value;

  logger.info({ deviceId, property, value }, 'Rowan has controlled a smart home device.');
  return `Successfully set ${property} of ${deviceId} to ${value}.`;
}

/**
 * Simulates applying a firmware update to a device.
 * @param {string} deviceId The ID of the device to update.
 */
async function applyFirmwareUpdate(deviceId) {
  const device = smartHomeState[deviceId];
  logger.warn({ deviceId, from: device.firmwareVersion, to: device.latestFirmwareVersion }, 'Rowan is applying a firmware update to a smart home device.');
  
  // Simulate update time
  await new Promise(resolve => setTimeout(resolve, 15000)); // 15-second update process

  device.firmwareVersion = device.latestFirmwareVersion;
  logger.info({ deviceId, newVersion: device.firmwareVersion }, 'Firmware update completed.');
}

/**
 * Autonomous function for Rowan to check for and apply firmware updates.
 */
export async function performFirmwareUpdateCheck() {
  logger.info('Rowan is autonomously checking for smart home device updates...');
  let updatesApplied = 0;
  for (const deviceId in smartHomeState) {
    const device = smartHomeState[deviceId];
    if (device.online && device.firmwareVersion !== device.latestFirmwareVersion) {
      await applyFirmwareUpdate(deviceId);
      updatesApplied++;
    }
  }
  if (updatesApplied > 0) {
    logger.info({ updatesApplied }, 'Rowan has completed the autonomous device update cycle.');
  }
}

/**
 * Simulates discovering and installing a "driver" for a new device.
 */
export function discoverNewDevices() {
  const newDeviceId = 'robot_vacuum';
  if (smartHomeState[newDeviceId]) {
    return 'No new devices found on the network.';
  }

  logger.info('Rowan is scanning the network for new devices...');
  smartHomeState[newDeviceId] = {
    online: true,
    state: 'docked',
    battery: 98,
    firmwareVersion: '1.0.0',
    latestFirmwareVersion: '1.0.0',
  };
  return `New device discovered: "robot_vacuum" has been configured and is now available.`;
}