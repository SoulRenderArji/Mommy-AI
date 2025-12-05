import { Router } from 'express';
import { getSanctuary } from '../services/databaseService.js';
import { proposeChange, approveChanges } from '../services/sanctuaryService.js';

const router = Router();

/**
 * GET /api/sanctuary
 * View the current state of the Sanctuary.
 */
router.get('/', (req, res) => {
  const sanctuary = getSanctuary();
  res.json({ success: true, sanctuary });
});

/**
 * POST /api/sanctuary/propose
 * Propose a change to the Sanctuary.
 */
router.post('/propose', async (req, res, next) => {
  try {
    const { user, changes } = req.body;
    const updatedSanctuary = await proposeChange(user, changes);
    res.json({ success: true, sanctuary: updatedSanctuary });
  } catch (error) {
    next(error);
  }
});

/**
 * POST /api/sanctuary/approve
 * Approve pending changes.
 */
router.post('/approve', async (req, res, next) => {
  try {
    const { user } = req.body; // Only needs the user to verify it's Daddy
    const updatedSanctuary = await approveChanges(user);
    res.json({ success: true, sanctuary: updatedSanctuary });
  } catch (error) {
    next(error);
  }
});

export default router;