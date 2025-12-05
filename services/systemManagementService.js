import { exec } from 'child_process';
import { promisify } from 'util';
import { logger } from './loggerService.js';
import { sendWhisper } from './notificationService.js';

const execAsync = promisify(exec);

/**
 * System Management Service
 * This module contains functions for Rowan to manage and report on the server
 * and related infrastructure like Cloudflare.
 */

/**
 * Retrieves the current status of the local server.
 * This is a safe, read-only operation.
 * @returns {Promise<object>} A promise that resolves with system status information.
 */
export async function getSystemStatus() {
  logger.info('Rowan is checking the system status...');
  
  // Run commands in parallel for efficiency
  const [uptimeResult, diskUsageResult, cloudflareResult] = await Promise.allSettled([
    execAsync('uptime -p'),
    execAsync('df -h / | tail -n 1'), // Get disk usage for the root filesystem
    execAsync('cloudflared tunnel list'), // Check Cloudflare tunnel status
  ]);

  const uptime = uptimeResult.status === 'fulfilled' ? uptimeResult.value.stdout.trim() : 'Unknown';
  
  let diskUsage = 'Unknown';
  if (diskUsageResult.status === 'fulfilled') {
    const [ , , , , usedPercent] = diskUsageResult.value.stdout.split(/\s+/);
    diskUsage = `Root filesystem is ${usedPercent} full.`;
  }

  let cloudflareTunnel = 'Status Unknown';
  if (cloudflareResult.status === 'fulfilled') {
    // A simple check to see if any tunnels are listed as "HEALTHY"
    if (cloudflareResult.value.stdout.includes('HEALTHY')) {
      cloudflareTunnel = 'One or more tunnels are HEALTHY.';
    } else {
      cloudflareTunnel = 'No healthy tunnels detected. Attention may be required.';
    }
  } else {
    cloudflareTunnel = "Could not execute 'cloudflared' command. Is it installed and in the system PATH?";
  }

  const status = {
    serverUptime: uptime,
    diskUsage: diskUsage,
    cloudflareTunnel: cloudflareTunnel,
  };

  return status;
}

/**
 * Restarts the Cloudflare Tunnel service. This is a privileged operation.
 * NOTE: For this to work, the user running the Node.js process must have
 * passwordless sudo permission for this specific command.
 *
 * Add to /etc/sudoers using `sudo visudo`:
 * your_username ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart cloudflared.service
 *
 * @returns {Promise<string>} A promise that resolves with the result of the command.
 */
export async function restartCloudflareTunnel() {
  const command = 'sudo systemctl restart cloudflared.service';
  logger.warn(`Attempting to restart Cloudflare Tunnel with command: "${command}"`);

  try {
    const { stdout, stderr } = await execAsync(command);
    logger.info('Successfully restarted Cloudflare Tunnel service.');
    return stdout || 'Service restarted successfully.';
  } catch (error) {
    logger.error({ err: error }, 'Failed to restart Cloudflare Tunnel service.');
    throw new Error(`Cloudflare Tunnel restart failed: ${error.message}`);
  }
}

/**
 * Checks for available package updates using apt.
 * @returns {Promise<string>} A summary of available updates.
 */
export async function checkForUpdates() {
  const command = 'sudo apt update';
  logger.info('Rowan is checking for system updates...');

  try {
    // We only care about the output lines that say how many packages can be upgraded.
    const { stdout } = await execAsync(command);
    const upgradeable = stdout.match(/(\d+)\s+package(s)? can be upgraded/);
    if (upgradeable) {
      return `${upgradeable[1]} package(s) can be upgraded. Run 'system.applyUpdates' to install them.`;
    }
    return 'System is up to date. No updates found.';
  } catch (error) {
    logger.error({ err: error }, 'Failed to check for updates.');
    throw new Error(`Update check failed: ${error.message}`);
  }
}

/**
 * Applies available system updates using apt.
 * @returns {Promise<string>} A confirmation message.
 */
export async function applyUpdates() {
  // The -y flag automatically answers "yes" to prompts.
  const command = 'sudo apt upgrade -y';
  logger.warn('Rowan is applying system updates...');
  // This can take a while, so no await is used. We just start the process.
  execAsync(command).then(({ stdout, stderr }) => {
    logger.info('System update process completed.');
    sendWhisper('System update process finished.', { stdout, stderr });
  }).catch(error => {
    logger.error({ err: error }, 'System update process failed.');
    sendWhisper('System update process FAILED.', { error: error.message });
  });

  return 'System update process has been started in the background. I will send a whisper when it is complete.';
}