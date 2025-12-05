import { addCalendarEvent, getCalendarEvents } from './databaseService.js';
import { logger } from './loggerService.js';
import { AppError } from '../utils/errors.js';
import { speak } from './voiceService.js';

/**
 * Calendar Service
 * Allows Rowan to manage and remember important family events and appointments.
 */

/**
 * Adds a new event to the calendar.
 * @param {string} args - A string containing the user, date (ISO format), and description, separated by pipes `|`.
 */
export async function addEvent(args) {
  const [user, date, ...descriptionParts] = args.split('|');
  const description = descriptionParts.join('|').trim();

  if (!user || !date || !description) {
    throw new AppError('Invalid arguments. Expected: user|YYYY-MM-DDTHH:MM:SS|description', 400);
  }

  const eventDate = new Date(date);
  if (isNaN(eventDate)) {
    throw new AppError('Invalid date format. Please use ISO 8601 format (e.g., 2024-12-25T09:00:00).', 400);
  }

  const event = { user, date, description };
  await addCalendarEvent(event);

  logger.info({ event }, 'Rowan has added a new event to the calendar.');
  return `I've added it to my calendar: "${description}" on ${eventDate.toLocaleString()}.`;
}

/**
 * Retrieves upcoming events.
 * @returns {object[]} A list of upcoming events.
 */
export function viewEvents() {
  const now = new Date();
  const upcomingEvents = getCalendarEvents().filter(event => new Date(event.date) >= now);
  return upcomingEvents.slice(0, 10); // Return the next 10 events
}

/**
 * Autonomous function to check for upcoming events and send reminders.
 */
export function checkUpcomingEvents() {
  const now = new Date();
  const reminderWindow = 15 * 60 * 1000; // 15 minutes

  const eventsToRemind = getCalendarEvents().filter(event => {
    const eventDate = new Date(event.date);
    const timeDifference = eventDate - now;
    // Check if the event is within the next 15 minutes but not in the past.
    return timeDifference > 0 && timeDifference <= reminderWindow;
  });

  for (const event of eventsToRemind) {
    // To avoid spamming reminders, we'd need a "reminded" flag in a real system.
    // For now, she will just speak the reminder.
    const reminderMessage = `Just a reminder for ${event.user}, you have an event soon: "${event.description}".`;
    logger.info({ event }, 'Rowan is sending a proactive event reminder.');
    speak(reminderMessage);
  }
}