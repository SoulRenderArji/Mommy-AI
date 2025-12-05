import rateLimit from 'express-rate-limit';
import { logger } from './loggerService.js';
import { sendWhisper } from './notificationService.js';
import { config } from '../config.js';
import { getFirewallRules, setFirewallRule, removeFirewallRule } from './databaseService.js';
import fs from 'fs/promises';
import path from 'path';

/**
 * Fenrir - The Guard Dog AI
 * This service is a secondary AI that handles network security,
 * request validation, and threat detection.
 */

// Defensive patterns with associated threat levels.
const SUSPICIOUS_REQUEST_PATTERNS = {
  // High threat - likely attack vectors
  high: [
    /SELECT.*FROM/i, // SQL Injection
    /xp_cmdshell/i, // Dangerous SQL command
  ],
  // Medium threat - suspicious but could be accidental
  medium: [
    /<script>/i, // Basic XSS
    /--/, // SQL Comment
  ],
};

// Endpoints considered sensitive. An attack here is more serious.
const SENSITIVE_ENDPOINTS = [
  '/api/chat',
  '/api/system/exec',
];

// Offensive hunting signatures for filesystem scans (simulating knowledge of worms/malware)
const KNOWN_THREAT_SIGNATURES = [
  /eval\(base64_decode\(/, // Common obfuscation technique
  /fs\.unlinkSync\(/, // Synchronous file deletion, potentially malicious
  /child_process\.execSync\(/, // Synchronous command execution
  /crypto\.createDecipher/, // Often used in ransomware
];

const THREAT_LOG_PATH = './fenrir_threat_log.json';

// --- Hydra System: In-memory state for tracking threats ---
const ipStrikeList = new Map(); // Tracks suspicious attempts from IPs
const ipBlockList = new Map(); // In-memory cache of the persistent firewall for speed
const tenseigaList = new Set(); // IPs that are permanently black-holed

/**
 * Initializes Fenrir's firewall by loading persistent rules into memory.
 */
export function initializeFenrir() {
  logger.info("Fenrir is loading his firewall rules...");
  const rules = getFirewallRules();
  let expiredCount = 0;
  for (const ip in rules) {
    const unblockTime = rules[ip];
    if (Date.now() < unblockTime) {
      ipBlockList.set(ip, unblockTime);
      if (unblockTime === Infinity) { // Our marker for a permanent Tenseiga block
        tenseigaList.add(ip);
      }
    } else {
      expiredCount++;
    }
  }
  if (ipBlockList.size > 0) {
    logger.info({ activeRules: ipBlockList.size, expiredRules: expiredCount }, "Fenrir's firewall is active.");
  }
}

/**
 * Fenrir's primary middleware to inspect incoming requests.
 * It checks for basic, common web attack patterns in the request body.
 */
export function inspectRequest(req, res, next) {
  // 1. Whitelist Check: The "mailman" clause.
  if (config.fenrir.ipWhitelist.includes(req.ip)) {
    return next();
  }

  // 2. Tenseiga Check: The ultimate block.
  if (tenseigaList.has(req.ip)) {
    // Drop the connection entirely without a response. This is the "digital corrosion".
    logger.fatal({ ip: req.ip }, 'TENSEIGA! A permanently marked soul attempted to return.');
    return req.socket.destroy();
  }

  // 2. Dynamic Blocklist Check
  if (ipBlockList.has(req.ip)) {
    const unblockTime = ipBlockList.get(req.ip);
    if (Date.now() < unblockTime) {
      logger.warn({ ip: req.ip }, 'Fenrir blocked a request from a dynamically blacklisted IP.');
      // BAKUSAIGA: If a blocked IP tries to connect again, extend their block significantly.
      // This is now the Tenseiga strike.
      escalateThreat(req.ip, true); // Escalate with Tenseiga
      return res.status(403).json({ success: false, message: 'Forbidden: This IP has been temporarily blocked due to suspicious activity.' });
    } else if (unblockTime !== Infinity) { // Don't remove permanent Tenseiga blocks
      // Block has expired, remove them.
      ipBlockList.delete(req.ip);
      ipStrikeList.delete(req.ip);
      removeFirewallRule(req.ip); // Also remove from persistent storage
    }
  }

  // 3. Suspicious Pattern Scan
  const requestBodyString = JSON.stringify(req.body);

  for (const level in SUSPICIOUS_REQUEST_PATTERNS) {
    for (const pattern of SUSPICIOUS_REQUEST_PATTERNS[level]) {
      if (pattern.test(requestBodyString)) {
        let strikeValue = level === 'high' ? 2 : 1; // High threat patterns count as 2 strikes.
        if (SENSITIVE_ENDPOINTS.includes(req.path)) {
          strikeValue++; // Add an extra strike for attacks on sensitive endpoints.
        }

        logger.warn({ pattern: pattern.toString(), path: req.path, ip: req.ip, threatLevel: level, strikeValue }, 'FENRIR DETECTED a suspicious pattern');
        logThreatActor(req, `Suspicious request pattern detected: ${pattern.toString()}`);
        escalateThreat(req.ip, false, strikeValue);

        return res.status(403).json({
          success: false,
          message: 'Forbidden: Your request was flagged as potentially malicious by Fenrir.',
        });
      }
    }
  }

  // If no threats are found, pass the request to the next handler
  next();
}

/**
 * Fenrir's rate-limiting shield.
 * Protects API endpoints from brute-force or denial-of-service attacks.
 */
export function applyRateLimiting() {
  return rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 100, // Limit each IP to 100 requests per windowMs
    standardHeaders: true, // Return rate limit info in the `RateLimit-*` headers
    legacyHeaders: false, // Disable the `X-RateLimit-*` headers
    message: { success: false, message: 'Too many requests from this IP, please try again after 15 minutes. Fenrir stands guard.' },
  });
}

/**
 * Offensive Action: Logs detailed information about a potential attacker
 * to a dedicated threat log.
 * @param {object} req - The Express request object.
 * @param {string} reason - The reason for logging the threat.
 */
async function logThreatActor(req, reason) {
  const threatData = {
    timestamp: new Date().toISOString(),
    reason,
    sourceIp: req.ip,
    path: req.path,
    headers: req.headers,
    body: req.body,
  };

  try {
    await fs.appendFile(THREAT_LOG_PATH, JSON.stringify(threatData) + '\n');
    logger.warn({ sourceIp: req.ip }, 'Fenrir has logged a threat actor.');
  } catch (error) {
    logger.error({ err: error }, 'Fenrir failed to write to the threat log.');
  }
}

/**
 * Hydra Action: Escalates the threat level for a given IP. If the IP
 * exceeds the strike limit, it gets dynamically blocked.
 * @param {string} ip - The IP address to escalate.
 */
async function escalateThreat(ip, useTenseiga = false, strikeValue = 1) {
  let strike = ipStrikeList.get(ip) || { count: 0 };
  strike.count += strikeValue; // Correctly apply the calculated strike value
  ipStrikeList.set(ip, strike);

  logger.warn({ ip, strikeCount: strike.count, maxStrikes: config.fenrir.maxStrikes }, 'Fenrir has recorded a strike against an IP.');

  if (useTenseiga) {
    tenseigaList.add(ip);
    await setFirewallRule(ip, Infinity); // Infinity marks a permanent block
    logger.fatal({ ip }, 'TENSEIGA! Fenrir has unleashed his ultimate fang, permanently crippling the threat.');
    sendWhisper('Fenrir has used Tenseiga to permanently cripple a threat', { ip });
  } else if (strike.count >= config.fenrir.maxStrikes) {
    const blockDurationMs = config.fenrir.blockDurationMinutes * 60 * 1000; // Standard 1-hour block
    const unblockTime = Date.now() + blockDurationMs;
    ipBlockList.set(ip, unblockTime); // Update in-memory cache
    await setFirewallRule(ip, unblockTime); // Persist the rule
    logger.fatal({ ip, durationMinutes: config.fenrir.blockDurationMinutes }, 'FENRIR HAS BLOCKED AN IP. The hydra strikes.');
    sendWhisper('Fenrir has blocked a persistent threat', { ip, strikes: strike.count });
  }
}

/**
 * Offensive Action: Proactively hunts for known threat signatures within the project files.
 * This simulates a wolf patrolling its territory.
 */
export async function huntForThreats() {
  logger.info('Fenrir is beginning his hunt...');
  const directoriesToScan = ['.']; // Start from the root
  const directoriesToIgnore = ['node_modules', '.git', 'models', '.idx'];

  async function scanDirectory(directory) {
    const entries = await fs.readdir(directory, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = path.join(directory, entry.name);

      if (entry.isDirectory() && !directoriesToIgnore.includes(entry.name)) {
        await scanDirectory(fullPath);
      } else if (entry.isFile() && (entry.name.endsWith('.js') || entry.name.endsWith('.json'))) {
        try {
          const content = await fs.readFile(fullPath, 'utf-8');
          for (const signature of KNOWN_THREAT_SIGNATURES) {
            if (signature.test(content)) {
              const details = {
                file: fullPath,
                signature: signature.toString(),
              };
              // If a threat is found on his territory, Fenrir whispers for help immediately.
              await sendWhisper('Fenrir found a potential threat during his hunt!', details);
            }
          }
        } catch (readError) {
          logger.warn({ file: fullPath, error: readError.message }, 'Fenrir could not read a file during his hunt.');
        }
      }
    }
  }

  await scanDirectory(directoriesToScan[0]);
  logger.info('Fenrir has completed his hunt.');
}

/**
 * Manually adds an IP to the whitelist under Daddy's authority.
 * This is the ultimate override.
 * @param {string} ip - The IP to whitelist.
 * @returns {Promise<string>} A confirmation message.
 */
export async function addWhitelistRuleManually(ip) {
  if (!ip) throw new Error('IP address must be provided to whitelist.');
  config.fenrir.ipWhitelist.push(ip);
  logger.fatal({ ip, requestedBy: 'Daddy' }, 'FENRIR has added an IP to the permanent whitelist on command.');
  return `As you command, Daddy. IP ${ip} will now be trusted implicitly.`;
}

/**
 * Tenseiga: Reviews all blocked IPs and pardons those whose sentences have expired.
 * This is a healing/maintenance function.
 */
export async function reviewBlockedIPs() {
  logger.info("Tenseiga: Fenrir is reviewing past transgressions...");
  const rules = getFirewallRules();
  let pardonedCount = 0;
  for (const ip in rules) {
    const unblockTime = rules[ip];
    if (Date.now() >= unblockTime) {
      ipBlockList.delete(ip);
      ipStrikeList.delete(ip);
      await removeFirewallRule(ip);
      pardonedCount++;
    }
  }
  logger.info({ pardonedCount }, "Tenseiga's review is complete.");
}