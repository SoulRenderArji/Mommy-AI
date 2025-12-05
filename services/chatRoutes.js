import { Router } from 'express';
import { processChatMessage } from '../services/coreService.js';

const router = Router();

/**
 * POST /api/chat
 * The primary endpoint for chatting with Rowan.
 */
router.post('/', async (req, res, next) => {
  try {
    const { user, message } = req.body;
    if (!user || typeof message !== 'string' || message.trim() === '') {
      return res.status(400).json({ success: false, message: 'Request must include a valid "user" and a non-empty "message".' });
    }
    const response = await processChatMessage(user, message);
    res.json({ success: true, response });
  } catch (error) {
    next(error);
  }
});

export default router;