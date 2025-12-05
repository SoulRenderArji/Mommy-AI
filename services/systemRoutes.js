import { Router } from 'express';
import { getSystemStatus, restartCloudflareTunnel } from '../services/systemManagementService.js';
import { generateDailyBriefing } from '../services/coreService.js';
import { executeSystemCommand } from '../modules/Soul-OS/index.js';
import { generateStory } from '../modules/Project-Genesis/index.js';

const router = Router();

router.get('/status', async (req, res, next) => {
  try {
    const statusReport = await getSystemStatus();
    res.json({ success: true, status: statusReport });
  } catch (error) {
    next(error);
  }
});

router.get('/briefing', async (req, res, next) => {
  try {
    const briefing = await generateDailyBriefing();
    res.json({ success: true, briefing });
  } catch (error) {
    next(error);
  }
});

router.post('/exec', async (req, res, next) => {
  try {
    const { command } = req.body;
    const output = await executeSystemCommand(command);
    res.json({ success: true, output });
  } catch (error) {
    // Pass validation or execution errors to the central handler
    next(error);
  }
});

/**
 * GET /api/system/generate/story
 */
router.get('/generate/story', (req, res) => {
  res.json({ success: true, story: generateStory() });
});

export default router;