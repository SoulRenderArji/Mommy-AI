import puppeteer from 'puppeteer';
import { logger } from './loggerService.js';
import { ServiceUnavailableError } from '../utils/errors.js';

/**
 * Web Navigation Service
 * Allows Rowan to browse the web, read content, and learn autonomously.
 */

/**
 * Launches a browser, navigates to a URL, and scrapes its text content.
 * @param {string} url The URL to visit.
 * @returns {Promise<string>} The scraped text content of the page.
 */
export async function browseAndScrape(url) {
  logger.info({ url }, "Rowan is navigating the web...");
  let browser;
  try {
    browser = await puppeteer.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox'], // Required for running in many server environments
    });
    const page = await browser.newPage();
    await page.goto(url, { waitUntil: 'networkidle2', timeout: 30000 });

    // Extract text content from the page
    const textContent = await page.evaluate(() => document.body.innerText);

    await browser.close();

    // Return a manageable chunk of text to avoid overwhelming the LLM
    return textContent.substring(0, 10000);
  } catch (error) {
    if (browser) {
      await browser.close();
    }
    logger.error({ err: error, url }, "Rowan failed to browse the web.");
    throw new ServiceUnavailableError(`I was unable to access the website at that address. It might be down or the URL may be incorrect.`);
  }
}