import { LlamaModel, LlamaContext, LlamaChatSession } from "node-llama-cpp";
import { GoogleGenerativeAI } from "@google/generative-ai";
import { config } from '../config.js';
import { logger } from './loggerService.js';

let localModel;
let googleAI;
const localSessions = {}; // Store a separate session for each user for the local model

/**
 * Initializes the Language Model and creates a chat session.
 * This is the core of the AI's ability to generate speech.
 */
export async function initializeLanguageModel() {
  if (config.llm.geminiApiKey) {
    logger.info("Gemini API key found. Initializing Google AI client...");
    try {
      googleAI = new GoogleGenerativeAI(config.llm.geminiApiKey);
      logger.info("Google AI client initialized successfully. Rowan will use the Gemini model.");
    } catch (error) {
      logger.fatal({ err: error }, "Failed to initialize Google AI Client. Check API Key.");
      process.exit(1);
    }
  } else {
    logger.warn("No Gemini API key found. Falling back to local language model.");
    logger.info("Initializing local language model... This may take a moment.");
    localModel = new LlamaModel({ modelPath: config.llm.modelPath });
    logger.info("Local language model initialized successfully.");
  }
}

/**
 * Generates a response from the AI using the loaded model.
 * It maintains a separate conversation history for each user.
 * @param {string} userName - The user to generate a response for.
 * @param {string} systemPrompt - The persona and instructions for the AI.
 * @param {string} userMessage - The message from the user.
 * @returns {Promise<string>} The AI's generated response.
 */
export async function generateResponse(userName, systemPrompt, userMessage) {
  // Prefer the powerful cloud model if it's available
  if (googleAI) {
    try {
      const model = googleAI.getGenerativeModel({ model: config.llm.modelName, systemInstruction: systemPrompt });
      const result = await model.generateContent(userMessage);
      const response = await result.response;
      const text = response.text();
      logger.debug({ user: userName, response: text }, 'Gemini response received');
      return text;
    } catch (error) {
      logger.error({ err: error }, "Error generating response from Gemini API. Check API key permissions and usage limits.");
      // Fallback to local model could be implemented here if desired
      throw new Error("Failed to generate response from Gemini API.");
    }
  }

  // Fallback to the local model
  if (!localModel) {
    throw new Error("Language model has not been initialized. Please start the server correctly.");
  }

  // Get or create a session for the specific user
  if (!localSessions[userName]) {
    logger.info(`Creating new chat session for ${userName}...`);
    const context = new LlamaContext({ model: localModel, contextSize: config.llm.contextSize });
    localSessions[userName] = new LlamaChatSession({ context });
  }

  const session = localSessions[userName];

  logger.debug({ user: userName, prompt: userMessage }, 'Generating LLM response');
  const response = await session.prompt(userMessage, {
    systemPrompt,
  });

  logger.debug({ user: userName, response }, 'Local LLM response received');
  return response;
}