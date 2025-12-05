
import { RemoteBrain, BrainNodeConfig } from '../types';

// Configuration matching the "Integrative Healer" architecture request
const DEFAULT_CONFIG: BrainNodeConfig = {
    repoOwner: 'SoulRenderArji',
    repoName: 'Mommy-AI',
    branch: 'main'
};

const getRawUrl = (config: BrainNodeConfig, path: string) => 
    `https://raw.githubusercontent.com/${config.repoOwner}/${config.repoName}/${config.branch}/${path}`;

export const githubService = {
    
    syncBrain: async (config: BrainNodeConfig = DEFAULT_CONFIG): Promise<RemoteBrain> => {
        const brain: RemoteBrain = {
            pons_identity: "",
            amygdala_safety: "",
            prefrontal_planner: "",
            temporal_tone: "",
            lastSynced: new Date()
        };

        try {
            console.log(`Syncing brain from ${config.repoOwner}/${config.repoName}...`);

            // 1. THE PONS: Core Identity
            // Tries to fetch the core definition file
            const ponsReq = await fetch(getRawUrl(config, 'core-identity.json'));
            if (!ponsReq.ok) {
                // Fallback to module filename if simple name fails
                const ponsAlt = await fetch(getRawUrl(config, 'Mommy_Integrative_Healer_v4.0.json'));
                if (ponsAlt.ok) brain.pons_identity = await ponsAlt.text();
            } else {
                brain.pons_identity = await ponsReq.text();
            }

            // 2. THE AMYGDALA: Safety Protocol
            const amygdalaReq = await fetch(getRawUrl(config, 'safety-protocol.json'));
            if (amygdalaReq.ok) {
                brain.amygdala_safety = await amygdalaReq.text();
            } else {
                const amygdalaAlt = await fetch(getRawUrl(config, 'safety_protocol.json')); // try underscore
                if (amygdalaAlt.ok) brain.amygdala_safety = await amygdalaAlt.text();
            }
            
            // 3. PREFRONTAL CORTEX: Executive Planner
            const prefrontalReq = await fetch(getRawUrl(config, 'executive-planner.json'));
            if (prefrontalReq.ok) {
                brain.prefrontal_planner = await prefrontalReq.text();
            } else {
                 const prefrontalAlt = await fetch(getRawUrl(config, 'executive_planner.json'));
                 if(prefrontalAlt.ok) brain.prefrontal_planner = await prefrontalAlt.text();
            }

            // 4. TEMPORAL LOBE: Adaptive Tone Logic
            const temporalReq = await fetch(getRawUrl(config, 'adaptive-tone-modifier.json'));
            if (temporalReq.ok) {
                brain.temporal_tone = await temporalReq.text();
            } else {
                const temporalAlt = await fetch(getRawUrl(config, 'adaptive_tone_modifier.json'));
                if(temporalAlt.ok) brain.temporal_tone = await temporalAlt.text();
            }

            console.log("Brain Synced Successfully.");
            return brain;

        } catch (error) {
            console.error("Failed to sync brain nodes from GitHub:", error);
            // Return empty brain rather than throwing to prevent app crash, allow manual retry
            return brain;
        }
    }
};
