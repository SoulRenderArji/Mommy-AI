/**
 * Centralized Configuration for Rowan Bartel AI
 *
 * This file consolidates all environment-dependent variables and settings.
 * In a production environment, these values should be sourced from environment variables.
 */
import path from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';

// Load environment variables from .env file
dotenv.config();

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export const config = {
  port: process.env.PORT || 3000,
  llm: {
    // If a Gemini API key is provided, we will use the cloud model.
    // Otherwise, we fall back to the local model.
    geminiApiKey: process.env.GEMINI_API_KEY || null,
    modelName: 'gemini-1.5-flash-latest', // The specific Gemini model to use
    // Path to the local model file.
    modelPath: path.join(__dirname, "models", "dolphin-2.9-llama-3-8b-Q4_K_M.gguf"),
    contextSize: 8192, // Larger models can handle a much larger context window.
  },
  logLevel: process.env.LOG_LEVEL || 'info',
  meta: {
    birthDate: '2006-05-24T12:00:00.000Z', // Her birth date, making her 18 years old.
    lifeSpanYears: 100,
  },
  fenrir: {
    ipWhitelist: [
      '127.0.0.1', // Always trust localhost
      '::1',       // Always trust localhost (IPv6)
      // '::ffff:127.0.0.1', // Also localhost
      // Add any other known-good IPs here (e.g., monitoring services, your personal static IP)
    ],
    maxStrikes: 3, // How many suspicious requests before a long-term block
    blockDurationMinutes: 60, // How long to block an IP after max strikes
  },
  apiKeys: {
    cloudflare: process.env.CLOUDFLARE_API_KEY || null,
    lila_public: process.env.LILA_PUBLIC_KEY || null,
    lila_secret: process.env.LILA_SECRET_KEY || null,
  }
};