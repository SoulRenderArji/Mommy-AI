import { Router } from 'express';
import { activateHaptic } from '../services/hapticsService.js';
import { getWebsiteStatus, deployWebsiteUpdate } from '../services/ionosService.js';

const router = Router();

router.post('/haptics/activate', async (req, res, next) => {
  try {
    const { device, pattern } = req.body;
    if (!device || !pattern) {
      return res.status(400).json({ success: false, message: 'Request must include "device" and "pattern".' });
    }
    const result = await activateHaptic(device, pattern);
    res.json({ success: true, message: result });
  } catch (error) {
    next(error);
  }
});

router.get('/ionos/website/:id', async (req, res, next) => {
  try {
    const { id } = req.params;
    if (!id) {
      return res.status(400).json({ success: false, message: 'Website ID must be provided.' });
    }
    const status = await getWebsiteStatus(id);
    res.json({ success: true, status });
  } catch (error) {
    next(error);
  }
});

router.post('/ionos/website/:id/deploy', async (req, res, next) => {
  try {
    const { id } = req.params;
    if (!id) {
      return res.status(400).json({ success: false, message: 'Website ID must be provided.' });
    }
    const status = await deployWebsiteUpdate(id);
    res.json({ success: true, message: 'Deployment initiated successfully.', status });
  } catch (error) {
    next(error);
  }
});

export default router;