import { Router } from 'express';
import { getGreeting } from '../services/coreService.js';

const router = Router();

/**
 * GET /
 * The main landing page for the AI.
 */
router.get('/', (req, res) => {
  const { user } = req.query;
  const greeting = getGreeting(user);
  res.send(greeting);
});

export default router;