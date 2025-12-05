import pino from 'pino';
import { config } from '../config.js';

// Initialize a placeholder logger
let logger;

// In a development environment, use pino-pretty for nicely formatted logs.
// In production, use the default JSON logger for performance.
if (process.env.NODE_ENV === 'development') {
  logger = pino({
    level: config.logLevel,
    transport: {
      target: 'pino-pretty',
      options: {
        colorize: true, // Make the output colorful
        translateTime: 'SYS:standard', // Use a more readable time format
        ignore: 'pid,hostname', // Don't show process ID and hostname
      },
    },
  });
} else {
  logger = pino({
    level: config.logLevel,
  });
}

export { logger };