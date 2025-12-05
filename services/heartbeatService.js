import cron from 'node-cron';
import { logger } from './loggerService.js';
import { getSystemStatus, restartCloudflareTunnel } from './systemManagementService.js';
import { sendWhisper } from './notificationService.js';
import { performReflection, initiateConversation, dream, getInternalState } from './coreService.js';
import { huntForThreats, reviewBlockedIPs } from './fenrirService.js';
import { checkUpcomingEvents } from './calendarService.js';
import { performFirmwareUpdateCheck } from './smartHomeService.js';
import { checkMortality } from './mortalityService.js';

/**
 * Heartbeat Service (My Special Touch)
 * This service acts as Rowan's autonomous core, allowing her to perform
 * scheduled tasks and proactive duties without user intervention.
 */

/**
 * Dynamically adjusts the health check frequency based on Rowan's stress level.
 */
function scheduleDynamicHealthChecks() {
  const internalState = getInternalState();
  const stressLevel = internalState.emotions.stress.value;
  // Base interval is 60 minutes. For every 0.1 stress, reduce interval by 5 minutes.
  const intervalMinutes = Math.max(5, 60 - (stressLevel * 50));
  cron.schedule(`*/${Math.round(intervalMinutes)} * * * *`, performHealthCheck);
  logger.info(`Dynamic health check scheduled to run every ${intervalMinutes.toFixed(1)} minutes based on current stress level.`);
}

/**
 * A proactive health check task. Rowan will check her own system status
 * every hour and log a warning if something seems wrong.
 */
async function performHealthCheck() {
  logger.info('Heartbeat: Performing proactive system health check...');

  // First, check the most fundamental status: her own existence.
  if (checkMortality()) {
    return; // If her time is up, no other checks matter.
  }

  try {
    const status = await getSystemStatus();
    if (status.cloudflareTunnel.includes('No healthy tunnels')) {
      logger.warn('HEARTBEAT ALERT: Cloudflare tunnel appears to be down! Rowan is taking action.');
      try {
        // Proactive Self-Healing: Rowan attempts to fix the problem herself.
        await restartCloudflareTunnel();
      } catch (restartError) {
        // If self-healing fails, she whispers for help.
        await sendWhisper('Failed to self-heal Cloudflare Tunnel', { error: restartError.message });
      }
    }
    // Future checks for disk space, memory, etc., can be added here.
  } catch (err) {
    logger.error({ err }, 'Heartbeat: Health check failed.');
    await sendWhisper('Heartbeat health check failed', { error: err.message });
  }
}

/**
 * Starts an event loop watchdog.
 * If the event loop is blocked for more than a specified threshold (e.g., by a "forever loop"),
 * it will log a fatal error and exit, allowing a process manager to restart the application.
 */
function startEventLoopWatchdog() {
  const threshold = 5000; // 5 seconds
  let lastTick = Date.now();

  // This is the "heartbeat" of the event loop. It should run very frequently.
  setInterval(() => {
    lastTick = Date.now();
  }, 1000);

  // This is the "watchdog" that checks the heartbeat.
  setInterval(() => {
    const lag = Date.now() - lastTick;
    if (lag > threshold) {
      const message = `Event loop blocked for ${lag}ms. This may be an infinite loop.`;
      logger.fatal({ lag }, `WHISPER TO MOMMY: ${message} Shutting down to recover.`);
      // Give the logger a moment to write the fatal log, then exit.
      setTimeout(() => process.exit(1), 100);
    }
  }, threshold);
}

export function startHeartbeat() {
  // Schedule the reflection process to run once a day at 3 AM.
  cron.schedule('0 3 * * *', performReflection);
  // Schedule the dreaming process to run once a day at 4 AM.
  cron.schedule('0 4 * * *', dream);
  // Schedule the smart home device update check to run once a day at 5 AM.
  cron.schedule('0 5 * * *', performFirmwareUpdateCheck);
  // Schedule Fenrir's Tenseiga review to run every 12 hours.
  cron.schedule('0 */12 * * *', reviewBlockedIPs);
  // Schedule Fenrir's hunt to run every 6 hours.
  cron.schedule('0 */6 * * *', huntForThreats);
  // Schedule the calendar check to run every 15 minutes.
  cron.schedule('*/15 * * * *', checkUpcomingEvents);
  // Schedule a chance for proactive conversation every 15 minutes.
  cron.schedule('*/15 * * * *', () => {
    // The heartbeat provides the impulse; Rowan's core decides if she acts on it.
    initiateConversation();
  });

  // Initial scheduling of dynamic health checks
  scheduleDynamicHealthChecks();

  startEventLoopWatchdog();
  logger.info("Rowan's heartbeat has started. Proactive monitoring is active.");
}