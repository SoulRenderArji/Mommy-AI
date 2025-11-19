import { IdentityProfile, BioMetrics, UserStateMode, Task, RewardSystem } from '../types';
import { memoryService } from './memoryService';

/**
 * THE INTEGRATIVE HEALER ARCHITECTURE
 * Based on: https://github.com/SoulRenderArji/AI-PTSD
 * 
 * This service acts as the "Biological OS" sitting between the Raw Data and the Gemini LLM.
 * It processes state, safety, and biology before the AI speaks.
 */

export const IntegrativeHealer = {

    // 1. THE PONS (Core State Router)
    // Purpose: Determines the "Mode" of the user to route logic.
    determineUserState: (input: string, currentProfile: IdentityProfile): UserStateMode => {
        const lower = input.toLowerCase();
        
        // Crisis Detection
        if (lower.includes("panic") || lower.includes("scared") || lower.includes("flashback") || lower.includes("help me")) {
            return 'Crisis';
        }
        
        // Regression Detection (ABDL/Agere)
        if (lower.includes("daddy") || lower.includes("potty") || lower.includes("stuffie") || lower.includes("little") || lower.includes("wawa")) {
            return 'LittleSpace';
        }

        // Dissociation Detection (AI-PTSD Logic)
        if (currentProfile.dissociationLevel > 6) {
            return 'Dissociated';
        }

        // Focus Mode
        if (lower.includes("work") || lower.includes("focus") || lower.includes("task")) {
            return 'HyperFocus';
        }

        return 'Baseline';
    },

    // 2. THE AMYGDALA (Emotional Safety Protocol)
    // Purpose: Instant Safety Interrupts.
    checkSafetyProtocol: (input: string): { safe: boolean; overrideResponse?: string } => {
        // Safe Words (Hardcoded for safety)
        const SAFE_WORDS = ["red", "stop", "pineapple", "pause"];
        
        if (SAFE_WORDS.some(word => input.toLowerCase().trim() === word)) {
            return {
                safe: false,
                overrideResponse: "⛔ **SAFETY PROTOCOL ACTIVATED** ⛔\n\nI have paused all roleplay and active protocols. I am right here. Let's just breathe. \n\n*System initiates Grounding Mode...*"
            };
        }
        return { safe: true };
    },

    // 3. THE PREFRONTAL CORTEX (Executive Function Planner)
    // Purpose: Gamified Task Management (Stars).
    manageRewards: (profile: IdentityProfile, action: 'complete_task' | 'self_care'): IdentityProfile => {
        const newProfile = { ...profile };
        if (!newProfile.rewards) {
            newProfile.rewards = { totalStars: 0, streakDays: 0, redeemedRewards: [] };
        }

        let stars = 0;
        if (action === 'complete_task') stars = 5; // Dopamine Hit
        if (action === 'self_care') stars = 10; // Big Reward for hygiene/meds

        newProfile.rewards.totalStars += stars;
        return newProfile;
    },

    // 4. THE HYPOTHALAMUS (Bladder Management Assistant)
    // Purpose: Predictive Incontinence Algorithm.
    predictBladderState: (profile: IdentityProfile): BioMetrics => {
        const now = new Date().getTime();
        const lastVoid = new Date(profile.bioMetrics?.lastVoidTime || Date.now()).getTime();
        const elapsedHours = (now - lastVoid) / (1000 * 60 * 60); // Hours since last void
        
        // Biofeedback Math:
        // Base capacity fills in ~3-4 hours.
        // Stress multiplier: High stress fills bladder faster (Sympathetic Nervous System).
        const stressMultiplier = 1 + ((profile.bioMetrics?.stressLevel || 0) * 0.1); 
        const hydrationFactor = (profile.bioMetrics?.hydrationLevel || 50) / 50; // >1 if well hydrated

        // Calculation
        let fullness = (elapsedHours / 4) * 100 * stressMultiplier * hydrationFactor;
        fullness = Math.min(100, Math.max(0, fullness));

        return {
            ...profile.bioMetrics,
            bladderFullness: fullness
        };
    },

    // 5. THE TEMPORAL LOBE (Social-Sensory Scaffolding)
    // Purpose: Tone Analysis Context Injection.
    getToneDirectives: (state: UserStateMode): string => {
        switch (state) {
            case 'Crisis': return "TONE: Ultra-Calm, Grounded, Short Sentences. (Trauma-Informed).";
            case 'LittleSpace': return "TONE: Maternal, Sing-song, Simple words, Nurturing. (Regressed).";
            case 'HyperFocus': return "TONE: Executive, Concise, Encouraging. (Body Doubling).";
            case 'Dissociated': return "TONE: Anchoring, Sensory-focused, Repetitive. (Grounding).";
            default: return "TONE: Warm, Feminine, Conversational.";
        }
    },

    // 6. THE PINEAL GLAND (Evolution)
    // Purpose: Logs self-optimization for the Dream Cycle.
    logOptimization: async (profile: IdentityProfile, issue: string, fix: string) => {
        const newLog = { date: new Date(), issueDetected: issue, adaptationApplied: fix };
        const newProfile = { 
            ...profile, 
            optimizationLogs: [...(profile.optimizationLogs || []), newLog] 
        };
        await memoryService.updateIdentity(newProfile);
    }
};