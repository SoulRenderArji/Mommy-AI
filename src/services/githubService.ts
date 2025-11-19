
import { RemoteBrain, BrainNodeConfig } from '../types';

// Default Configuration (You can change this to your own fork)
const DEFAULT_CONFIG: BrainNodeConfig = {
    repoOwner: 'SoulRenderArji',
    repoName: 'AI-PTSD', // or 'Mommy-Integrative-Healer' if you created a new one
    branch: 'main'
};

const getRawUrl = (config: BrainNodeConfig, path: string) => 
    `https://raw.githubusercontent.com/${config.repoOwner}/${config.repoName}/${config.branch}/${path}`;

export const githubService = {
    
    syncBrain: async (config: BrainNodeConfig = DEFAULT_CONFIG): Promise<RemoteBrain> => {
        const brain: RemoteBrain = {
            pons_identity: "",
            amygdala_safety: "",
            prefrontal_tasks: "",
            temporal_social: "",
            lastSynced: new Date()
        };

        try {
            // 1. Fetch Core Identity (The Pons)
            // We try standard filenames. If user hasn't created them, we use defaults.
            const ponsReq = await fetch(getRawUrl(config, 'core_identity.json'));
            if (ponsReq.ok) brain.pons_identity = await ponsReq.text();

            // 2. Fetch Safety Protocol (The Amygdala)
            const amygdalaReq = await fetch(getRawUrl(config, 'safety_protocol.json'));
            if (amygdalaReq.ok) brain.amygdala_safety = await amygdalaReq.text();
            
            // 3. Fetch Executive Logic (Prefrontal Cortex)
            const prefrontalReq = await fetch(getRawUrl(config, 'executive_planner.json'));
            if (prefrontalReq.ok) brain.prefrontal_tasks = await prefrontalReq.text();

            // 4. Fetch Social/Tone Logic (Temporal Lobe)
            const temporalReq = await fetch(getRawUrl(config, 'adaptive_tone_modifier.json'));
            if (temporalReq.ok) brain.temporal_social = await temporalReq.text();

            console.log("Brain Synced from GitHub:", config.repoName);
            return brain;

        } catch (error) {
            console.error("Failed to sync brain nodes from GitHub:", error);
            throw error;
        }
    }
};
