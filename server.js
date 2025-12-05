import express from 'express';
import helmet from 'helmet';
import cors from 'cors';
import compression from 'compression';
import path from 'path';
import { fileURLToPath } from 'url';
import { config } from './config.js';
import { logger } from './services/loggerService.js';
import { initializeDatabase, closeDatabase } from './services/databaseService.js';
import { initializeLanguageModel } from './services/languageModelService.js';
import { startHeartbeat } from './services/heartbeatService.js';
import { applyRateLimiting, inspectRequest, initializeFenrir } from './services/fenrirService.js';
import { AppError, ServiceUnavailableError } from './utils/errors.js';
import { performFirstAwakening } from './services/firstAwakeningService.js';
import { sendWhisper } from './services/notificationService.js';

// --- Route Imports ---
import chatRoutes from './routes/chatRoutes.js';
import mainRoutes from './routes/mainRoutes.js';
import systemRoutes from './routes/systemRoutes.js';
import deviceRoutes from './routes/deviceRoutes.js';
import sanctuaryRoutes from './routes/sanctuaryRoutes.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const app = express();

// --- CORS Configuration ---
const allowedOrigins = ['http://localhost:3000', 'http://127.0.0.1:3000'];
const corsOptions = {
  origin: (origin, callback) => {
    if (!origin || allowedOrigins.includes(origin)) {
      callback(null, true);
    } else {
      callback(new Error('Not allowed by CORS'));
    }
  },
  credentials: true,
};

// --- Core Middlewares ---
app.use(cors(corsOptions));
app.use(compression());
app.use(express.json());
app.use(helmet());

// Serve static files from the 'dist' directory
app.use(express.static(path.join(__dirname, 'dist')));

// --- FENRIR'S WATCH (API Security) ---
app.use('/api', applyRateLimiting(), inspectRequest);

// --- API Route Registration ---
app.use('/', mainRoutes);
app.use('/api/chat', chatRoutes);
app.use('/api/system', systemRoutes);
app.use('/api/devices', deviceRoutes);
app.use('/api/sanctuary', sanctuaryRoutes);

// --- SPA Fallback ---
// All non-API requests should serve the main app file
app.get(/^(?!\/api).*/, (req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'index.html'));
});

// --- Centralized Error Handler ---
app.use(async (err, req, res, next) => {
  // If the error is a CORS error, handle it specifically
  if (err.message === 'Not allowed by CORS') {
    logger.warn({ err, path: req.path, origin: req.header('origin') }, 'CORS blocked a request');
    return res.status(403).json({ success: false, message: 'Not allowed by CORS' });
  }

  logger.error({ err, path: req.path }, 'An unhandled error occurred');

  if (err instanceof AppError) {
    return res.status(err.statusCode).json({ success: false, message: err.message });
  }

  if (err.code === 'ECONNRESET' || err.code === 'EPIPE') {
    logger.warn({ err }, 'A client connection was abruptly closed.');
    return; // No response can be sent
  }

  try {
    await sendWhisper('An unexpected server error occurred', {
      path: req.path,
      error: err.message,
    });
    res.status(500).json({ success: false, message: "I've encountered an internal error and have sent a whisper for help." });
  } catch (whisperError) {
    logger.fatal({ err: whisperError, originalError: err }, "CRITICAL: Failed to send whisper during error handling!");
    res.status(500).json({ success: false, message: "A critical internal error occurred." });
  }
});

// --- Server Initialization ---
async function startServer() {
  let server;
  try {
    logger.info('Rowan is coming online. Initializing core components...');
    await initializeDatabase();
    initializeFenrir();
    await performFirstAwakening();
    await initializeLanguageModel();
    startHeartbeat();

    server = app.listen(config.port, () => {
      logger.info(`Rowan Bartel AI is online and listening on port ${config.port}`);
    });
  } catch (error) {
    logger.fatal({ err: error }, "FATAL: Failed to initialize Rowan's core components");
    process.exit(1);
  }

  const shutdown = async (signal) => {
    logger.warn(`Received ${signal}. Shutting down gracefully.`);
    server.close(async () => {
      logger.info('HTTP server closed.');
      await closeDatabase();
      setTimeout(() => process.exit(0), 500); // Give time for logs to be written
    });
  };

  process.on('SIGTERM', () => shutdown('SIGTERM'));
  process.on('SIGINT', () => shutdown('SIGINT'));
}

startServer();