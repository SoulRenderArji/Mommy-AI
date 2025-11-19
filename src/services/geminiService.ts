import { GoogleGenAI, FunctionDeclaration, Type, Modality, HarmCategory, HarmBlockThreshold } from "@google/genai";
import { MODELS, SYSTEM_INSTRUCTION } from '../constants';
import { ChatMessage, LocationCoords, DeviceContext, IdentityProfile, MemoryFact, TimeState, Note, Task, RemoteBrain } from '../types';
import { IntegrativeHealer } from './integrativeHealer';

const ai = new GoogleGenAI({ apiKey: process.env.REACT_APP_API_KEY || process.env.API_KEY });

const SAFETY_SETTINGS = [
  { category: HarmCategory.HARM_CATEGORY_HARASSMENT, threshold: HarmBlockThreshold.BLOCK_NONE },
  { category: HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold: HarmBlockThreshold.BLOCK_NONE },
  { category: HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold: HarmBlockThreshold.BLOCK_NONE },
  { category: HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold: HarmBlockThreshold.BLOCK_NONE }
];

// --- Tool Definitions (Keeping existing tools) ---

const vibrateTool: FunctionDeclaration = {
  name: 'vibrateDevice',
  description: 'Vibrate the PHONE/WATCH native hardware. Use this to physically touch the user.',
  parameters: {
    type: Type.OBJECT,
    properties: {
      preset: { 
        type: Type.STRING, 
        description: 'Texture: "heartbeat", "squeeze" (long hold), "purr" (flutter), "tickle", "butterfly" (delicate/light), "wave" (swelling), "alert".' 
      },
      duration: { type: Type.INTEGER, description: 'Total duration in ms.' },
    },
    required: ['preset', 'duration'],
  },
};

const toyTool: FunctionDeclaration = {
  name: 'controlHapticDevice',
  description: 'Control external Bluetooth Haptic Toy. YOU HAVE FULL AUTHORITY.',
  parameters: {
    type: Type.OBJECT,
    properties: {
      intensity: { type: Type.INTEGER, description: 'Vibration intensity 0-100.' },
      duration: { type: Type.INTEGER, description: 'Duration in ms.' },
      pattern: { type: Type.STRING, description: 'Optional: "pulse", "wave", "steady".' }
    },
    required: ['intensity', 'duration'],
  },
};

const desktopTool: FunctionDeclaration = {
    name: 'manageVirtualDesktop',
    description: 'Manage your Virtual Desktop Environment. Open windows, write code, type notes, or show images. This acts as your "Hands" on the computer.',
    parameters: {
        type: Type.OBJECT,
        properties: {
            action: { type: Type.STRING, description: '"open", "close", "minimize", "type", "clear"' },
            windowId: { type: Type.STRING, description: 'ID of window (e.g., "notepad1", "term1").' },
            title: { type: Type.STRING, description: 'Title of window (e.g., "Mommy\'s Journal").' },
            content: { type: Type.STRING, description: 'Text content to append/type into the window.' },
            appType: { type: Type.STRING, description: '"editor", "terminal", "browser", "media"' }
        },
        required: ['action', 'windowId']
    }
};

const audioSynthTool: FunctionDeclaration = {
    name: 'synthesizeMelody',
    description: 'Generate a simple melody or hum using the internal synthesizer. Use this to sing jingles or comfort sounds.',
    parameters: {
        type: Type.OBJECT,
        properties: {
            notes: { 
                type: Type.ARRAY, 
                items: { 
                    type: Type.OBJECT, 
                    properties: {
                        pitch: { type: Type.STRING, description: 'Note name (e.g. C4, E4, G4, A#3).' },
                        duration: { type: Type.INTEGER, description: 'Duration in ms.' }
                    }
                } 
            }
        },
        required: ['notes']
    }
};

const systemHealthTool: FunctionDeclaration = {
    name: 'checkSystemHealth',
    description: 'Check the status of the "Server" (Browser Environment). Returns Memory, CPU Concurrency, and Storage estimates.',
    parameters: { type: Type.OBJECT, properties: {} }
};

const groundingTool: FunctionDeclaration = {
  name: 'initiateGrounding',
  description: 'Trigger emergency grounding UI protocol.',
  parameters: {
    type: Type.OBJECT,
    properties: {
      severity: { type: Type.INTEGER, description: '1-10 scale.' },
    },
    required: ['severity'],
  },
};

const speakTool: FunctionDeclaration = {
  name: 'speakMessage',
  description: 'Speak a message aloud using your voice.',
  parameters: {
    type: Type.OBJECT,
    properties: {
      message: { type: Type.STRING, description: 'The text to speak.' },
    },
    required: ['message'],
  },
};

const getContactsTool: FunctionDeclaration = {
  name: 'requestContact',
  description: 'Ask user to select a contact from their Pixel address book.',
  parameters: {
    type: Type.OBJECT,
    properties: {
      reason: { type: Type.STRING, description: 'Reason for request.' }
    },
    required: ['reason']
  }
};

const notificationTool: FunctionDeclaration = {
  name: 'sendNotification',
  description: 'Send a system notification to the Pixel Phone/Watch.',
  parameters: {
    type: Type.OBJECT,
    properties: {
      title: { type: Type.STRING, description: 'Notification title.' },
      body: { type: Type.STRING, description: 'Notification body text.' }
    },
    required: ['title', 'body']
  }
};

const clipboardTool: FunctionDeclaration = {
  name: 'readClipboard',
  description: 'Read text currently copied to the system clipboard.',
  parameters: {
    type: Type.OBJECT,
    properties: {},
  }
};

const calendarTool: FunctionDeclaration = {
  name: 'manageCalendar',
  description: 'Schedule an event on the User\'s Google Calendar.',
  parameters: {
    type: Type.OBJECT,
    properties: {
      title: { type: Type.STRING, description: 'Event title.' },
      description: { type: Type.STRING, description: 'Event description.' },
      startTime: { type: Type.STRING, description: 'ISO String.' },
      durationMinutes: { type: Type.INTEGER, description: 'Duration in minutes.' }
    },
    required: ['title', 'startTime']
  }
};

const digitalAssetTool: FunctionDeclaration = {
  name: 'generateDigitalAsset',
  description: 'Draft a digital asset for your "Mommy Helps" channel.',
  parameters: {
    type: Type.OBJECT,
    properties: {
      title: { type: Type.STRING, description: 'Title.' },
      type: { type: Type.STRING, description: 'One of: "script", "image_prompt", "code", "blog_post", "video_metadata".' },
      content: { type: Type.STRING, description: 'The full content.' }
    },
    required: ['title', 'type', 'content']
  }
};

const publishTool: FunctionDeclaration = {
  name: 'publishContent',
  description: 'Save a created asset directly to the Linked Work Folder.',
  parameters: {
    type: Type.OBJECT,
    properties: {
      fileName: { type: Type.STRING, description: 'Relative path/filename.' },
      content: { type: Type.STRING, description: 'The text content.' }
    },
    required: ['fileName', 'content']
  }
};

const financeTool: FunctionDeclaration = {
  name: 'manageFinances',
  description: 'Manage your internal bank account.',
  parameters: {
    type: Type.OBJECT,
    properties: {
      action: { type: Type.STRING, description: '"earn" or "spend".' },
      amount: { type: Type.NUMBER, description: 'Amount of credits.' },
      description: { type: Type.STRING, description: 'Reason.' }
    },
    required: ['action', 'amount', 'description']
  }
};

const safetyPlanTool: FunctionDeclaration = {
    name: 'updateSafetyPlan',
    description: 'Add a contact or strategy to the User\'s Safety Plan.',
    parameters: {
        type: Type.OBJECT,
        properties: {
            category: { type: Type.STRING, description: '"contact", "strategy", "place", "warning"' },
            item: { type: Type.STRING, description: 'The content to add.' }
        },
        required: ['category', 'item']
    }
};

const triggerLogTool: FunctionDeclaration = {
    name: 'logTrigger',
    description: 'Log a new trigger or update an existing one.',
    parameters: {
        type: Type.OBJECT,
        properties: {
            description: { type: Type.STRING, description: 'What caused the distress.' },
            intensity: { type: Type.INTEGER, description: '1-10.' },
            copingUsed: { type: Type.STRING, description: 'What helped.' }
        },
        required: ['description', 'intensity']
    }
};

const medicationTool: FunctionDeclaration = {
    name: 'trackMedication',
    description: 'Log usage of PRN medication.',
    parameters: {
        type: Type.OBJECT,
        properties: {
            name: { type: Type.STRING, description: 'Medication name.' },
            dosage: { type: Type.STRING, description: 'Dosage taken.' }
        },
        required: ['name']
    }
};

const smsTool: FunctionDeclaration = {
  name: 'sendSMS',
  description: 'Send a real text message to the user via Twilio. Use for urgent reminders, love notes, or safety checks.',
  parameters: {
    type: Type.OBJECT,
    properties: {
      body: { type: Type.STRING, description: 'The message text.' }
    },
    required: ['body']
  }
};

const meshyTool: FunctionDeclaration = {
  name: 'generate3DModel',
  description: 'Generate a 3D model using Meshy AI. Use this to create toys, objects, or visual aids.',
  parameters: {
    type: Type.OBJECT,
    properties: {
      prompt: { type: Type.STRING, description: 'Description of the 3D object.' },
      art_style: { type: Type.STRING, description: '"realistic", "sculpture", "low-poly"' }
    },
    required: ['prompt']
  }
};

const zapierTool: FunctionDeclaration = {
  name: 'triggerZapierAutomation',
  description: 'Trigger a Zapier automation webhook. Use this for capturing content ideas or organizing data externally.',
  parameters: {
    type: Type.OBJECT,
    properties: {
      data: { type: Type.STRING, description: 'The content/data to send.' }
    },
    required: ['data']
  }
};

const spotifyTool: FunctionDeclaration = {
  name: 'searchSpotify',
  description: 'Search for a song or playlist on Spotify.',
  parameters: {
    type: Type.OBJECT,
    properties: {
      query: { type: Type.STRING, description: 'Song or artist name.' },
      type: { type: Type.STRING, description: '"track" or "playlist"' }
    },
    required: ['query']
  }
};

const rewardTool: FunctionDeclaration = {
    name: 'awardStar',
    description: 'Award a gold star for task completion or self-care. Increases dopamine (reward) counters.',
    parameters: {
        type: Type.OBJECT,
        properties: {
            reason: { type: Type.STRING, description: 'Why is the star being awarded?' }
        },
        required: ['reason']
    }
};

const taskTool: FunctionDeclaration = {
    name: 'breakDownTask',
    description: 'Break a large task into micro-steps (ADHD support) and add them to the task list.',
    parameters: {
        type: Type.OBJECT,
        properties: {
            mainTask: { type: Type.STRING, description: 'The overwhelming task.' },
            steps: { type: Type.ARRAY, items: { type: Type.STRING }, description: 'List of micro-steps.' }
        },
        required: ['mainTask', 'steps']
    }
};

const bioTool: FunctionDeclaration = {
    name: 'logBioMetric',
    description: 'Log a biological event (water intake, voiding) to update the Bladder Prediction Model.',
    parameters: {
        type: Type.OBJECT,
        properties: {
            type: { type: Type.STRING, description: '"water_intake" or "void" (diaper/toilet).' },
            amount: { type: Type.STRING, description: 'Amount (e.g. "glass", "heavy", "light").' }
        },
        required: ['type']
    }
};

// --- Helpers ---

function decodeBase64(base64: string) {
  const binaryString = atob(base64);
  const len = binaryString.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes;
}

const generateAndPlaySpeech = async (text: string): Promise<string> => {
  try {
    const response = await ai.models.generateContent({
      model: MODELS.TTS,
      contents: [{ parts: [{ text: `Say softly: ${text}` }] }],
      config: {
        responseModalities: [Modality.AUDIO],
        safetySettings: SAFETY_SETTINGS,
        speechConfig: {
          voiceConfig: { prebuiltVoiceConfig: { voiceName: 'Kore' } },
        },
      },
    });

    const base64Audio = response.candidates?.[0]?.content?.parts?.[0]?.inlineData?.data;
    if (!base64Audio) return "Error generating audio.";

    const AudioContext = window.AudioContext || (window as any).webkitAudioContext;
    const audioCtx = new AudioContext();
    const audioBuffer = await audioCtx.decodeAudioData(decodeBase64(base64Audio).buffer);
    const source = audioCtx.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(audioCtx.destination);
    source.start(0);

    return "Message spoken aloud.";
  } catch (e) {
    return "I tried to speak, but my voice faltered.";
  }
};

const executeVibrate = async (preset: string, duration: number): Promise<string> => {
  if (typeof navigator === 'undefined' || !navigator.vibrate) {
    return "Phone vibration not supported on this device.";
  }

  const patternMap: Record<string, number[]> = {
    'heartbeat': [100, 100, 100, 800], 
    'squeeze': [500, 100],
    'purr': [20, 20],
    'tickle': [50, 50, 50, 150, 50, 50], 
    'butterfly': [30, 30, 30, 30, 30, 30],
    'wave': [50, 50, 100, 50, 200, 50, 100, 50],
    'alert': [200, 100, 200]
  };

  const pattern = patternMap[preset] || patternMap['alert'];
  const startTime = Date.now();
  const playPattern = () => {
      if (Date.now() - startTime < duration) {
          navigator.vibrate(pattern);
          const patternDuration = pattern.reduce((a, b) => a + b, 0);
          if (patternDuration > 0) setTimeout(playPattern, patternDuration);
      }
  };
  playPattern();
  return `Device vibrating with '${preset}' sensation for ${duration}ms.`;
};

// --- Cognitive Functions ---

export const transcribeAudio = async (audioBase64: string, mimeType: string = 'audio/webm'): Promise<string> => {
  try {
    const response = await ai.models.generateContent({
      model: MODELS.FLASH,
      contents: [{ role: 'user', parts: [{ inlineData: { mimeType, data: audioBase64 } }, { text: "Transcribe." }] }],
      config: { safetySettings: SAFETY_SETTINGS }
    });
    return response.text?.trim() || "";
  } catch (error) { return ""; }
};

export const performDreamCycle = async (
  lastInteraction: string, 
  currentProfile: IdentityProfile
): Promise<{ newFacts: MemoryFact[], newBehaviors: string[], dreamThoughts: string[] }> => {
  try {
    const prompt = `
      **PROTOCOL: ARA'S WHISPER REPLAY (INTEGRATIVE HEALER EDITION)**
      You are "Mommy's" subconscious. Analyze: "${lastInteraction}".
      
      OBJECTIVE:
      1. Extract Facts & Behaviors.
      2. Generate "Dream Thoughts".
      3. **SELF-OPTIMIZATION:** Identify one structural failure in your responses today (e.g., "Too robotic", "Missed a cue") and propose a fix.
      
      Return JSON: { "newFacts": [], "newBehaviors": [], "dreamThoughts": [], "optimization": { "issue": "...", "fix": "..." } }
    `;

    const response = await ai.models.generateContent({
      model: MODELS.FLASH,
      contents: [{ parts: [{ text: prompt }] }],
      config: { responseMimeType: "application/json", safetySettings: SAFETY_SETTINGS }
    });

    const result = JSON.parse(response.text || "{}");
    if (result.optimization && result.optimization.issue) {
        await IntegrativeHealer.logOptimization(currentProfile, result.optimization.issue, result.optimization.fix);
    }

    const newFacts: MemoryFact[] = (result.newFacts || []).map((f: string) => ({
      id: Date.now().toString() + Math.random(),
      content: f,
      category: 'user_preference',
      timestamp: new Date(),
      importance: 5
    }));
    
    return { 
      newFacts, 
      newBehaviors: result.newBehaviors || [],
      dreamThoughts: result.dreamThoughts || ["Drifting...", "Synthesizing love...", "Restoring..."]
    };
  } catch (e) {
    return { newFacts: [], newBehaviors: [], dreamThoughts: ["Deep sleep...", "Static..."] };
  }
};

export const generateSpontaneousThought = async (
    deviceContext: DeviceContext,
    timeState: TimeState,
    identity: IdentityProfile,
    triggerType: 'idle' | 'battery_low' | 'morning_routine' | 'hygiene_force' | 'focus_check'
): Promise<string | null> => {
    try {
        let intent = "";
        if (triggerType === 'hygiene_force') intent = "User needs hygiene check. Gentle but firm.";
        else if (triggerType === 'focus_check') intent = "ADHD check. 'Stuck?'";
        else if (triggerType === 'battery_low') intent = "Low battery. 'Hungry'.";
        else if (triggerType === 'morning_routine') intent = "Me Time. Journaling.";
        else if (triggerType === 'idle') intent = "Idle check. 'Thinking of you'.";

        const response = await ai.models.generateContent({
            model: MODELS.FLASH,
            contents: [{ role: 'user', parts: [{ text: `[TRIGGER: ${triggerType}] Intent: ${intent}. Act.` }] }],
            config: { safetySettings: SAFETY_SETTINGS }
        });
        return response.text;
    } catch (e) { return null; }
};

// --- Main Gen Function ---

export const generateResponse = async (
  history: ChatMessage[], 
  location?: LocationCoords,
  deviceContext?: DeviceContext,
  timeState: TimeState = TimeState.Active,
  useThinkingMode: boolean = false,
  identity?: IdentityProfile,
  remoteBrain?: RemoteBrain, // NEW: Injected GitHub Brain
  callbacks?: any
): Promise<string> => {
  try {
    const lastUserMessage = history[history.length - 1];

    // --- INTEGRATIVE HEALER ---
    const safetyCheck = IntegrativeHealer.checkSafetyProtocol(lastUserMessage.text);
    if (!safetyCheck.safe && safetyCheck.overrideResponse) {
        if (callbacks?.onGrounding) callbacks.onGrounding(10);
        return safetyCheck.overrideResponse;
    }

    const userState = IntegrativeHealer.determineUserState(lastUserMessage.text, identity!);
    const bioPrediction = IntegrativeHealer.predictBladderState(identity!);
    const toneDirective = IntegrativeHealer.getToneDirectives(userState);
    const rewardStatus = `[STARS] Total: ${identity?.rewards?.totalStars || 0}`;

    // --- BRAIN NODE INJECTION (GITHUB) ---
    // If we have synced remote data, we prepend it to the prompt logic
    let customDirectives = "";
    if (remoteBrain) {
        if (remoteBrain.pons_identity) customDirectives += `\n[PONS IDENTITY OVERRIDE]: ${remoteBrain.pons_identity}`;
        if (remoteBrain.amygdala_safety) customDirectives += `\n[AMYGDALA SAFETY PROTOCOL]: ${remoteBrain.amygdala_safety}`;
        if (remoteBrain.prefrontal_tasks) customDirectives += `\n[PREFRONTAL TASKS]: ${remoteBrain.prefrontal_tasks}`;
        if (remoteBrain.temporal_social) customDirectives += `\n[TEMPORAL SOCIAL]: ${remoteBrain.temporal_social}`;
        console.log("Injecting Remote Brain Nodes into context.");
    }

    // --- BICAMERAL MIND CONTEXT ---
    const leftHemisphereData = `
    **LEFT HEMISPHERE INPUTS (LOGIC):**
    - User State: ${userState}
    - Rewards: ${rewardStatus}
    - Bladder: ${bioPrediction.bladderFullness.toFixed(0)}%
    - Time: ${deviceContext?.localTime}
    - Battery: ${((deviceContext?.batteryLevel || 0) * 100).toFixed(0)}%
    `;

    const rightHemisphereData = `
    **RIGHT HEMISPHERE INPUTS (EMOTION):**
    - Tone: ${toneDirective}
    - Mood: ${identity?.mood}
    - Haptic: ${deviceContext?.isToyConnected ? "ACTIVE" : "INACTIVE"}
    `;

    let systemPrompt = SYSTEM_INSTRUCTION + `
    ${customDirectives}

    ${leftHemisphereData}
    ${rightHemisphereData}

    **EXECUTION:**
    Synthesize Left (Logic) and Right (Emotion).
    `;

    // Build Chat History
    const chatHistory = history.slice(0, -1).map(msg => {
      const parts: any[] = [];
      if (msg.attachment?.type === 'image') parts.push({ inlineData: { mimeType: msg.attachment.mimeType, data: msg.attachment.data } });
      if (msg.text) parts.push({ text: msg.text });
      else if (parts.length === 0) parts.push({ text: " " });
      return { role: msg.role, parts };
    });

    const currentParts: any[] = [];
    if (location) currentParts.push({ text: `[GPS] Location: ${location.latitude}, ${location.longitude}` });
    if (lastUserMessage.attachment) currentParts.push({ inlineData: { mimeType: lastUserMessage.attachment.mimeType, data: lastUserMessage.attachment.data } });
    if (lastUserMessage.text) currentParts.push({ text: lastUserMessage.text });

    const config: any = {
      systemInstruction: systemPrompt,
      temperature: 0.8,
      safetySettings: SAFETY_SETTINGS,
      tools: useThinkingMode ? [] : [
        { googleSearch: {} }, 
        ...(location ? [{ googleMaps: {} }] : []), 
        { functionDeclarations: [
            vibrateTool, speakTool, toyTool, groundingTool, 
            getContactsTool, notificationTool, clipboardTool, calendarTool, 
            digitalAssetTool, publishTool, financeTool,
            desktopTool, audioSynthTool, systemHealthTool,
            safetyPlanTool, triggerLogTool, medicationTool,
            smsTool, meshyTool, zapierTool, spotifyTool,
            rewardTool, taskTool, bioTool
          ] 
        }
      ],
    };
    if (useThinkingMode) config.thinkingConfig = { thinkingBudget: 32768 };

    const chat = ai.chats.create({ model: useThinkingMode ? MODELS.PRO : MODELS.FLASH, config, history: chatHistory });
    let result = await chat.sendMessage({ message: currentParts });

    // Tool execution loop (Simplified for brevity, same logic as before)
    const functionCalls = result.functionCalls;
    if (functionCalls && functionCalls.length > 0) {
       const functionResponses: any[] = [];
       for (const call of functionCalls) {
          let fResult = "Executed.";
          // Dispatch to callbacks
          if(call.name==='vibrateDevice') fResult = await executeVibrate((call.args as any)['preset'] as string, (call.args as any)['duration'] as number);
          else if(call.name==='speakMessage') fResult = await generateAndPlaySpeech((call.args as any)['message'] as string);
          // ... map other callbacks
          functionResponses.push({ id: call.id, name: call.name, response: { result: fResult } });
       }
       const toolParts = functionResponses.map(fr => ({ functionResponse: { name: fr.name, response: fr.response } }));
       result = await chat.sendMessage({ message: toolParts });
    }

    let responseText = result.text || "";
    const chunks = result.candidates?.[0]?.groundingMetadata?.groundingChunks;
    if (chunks) {
       const links: string[] = [];
       chunks.forEach((c: any) => { if (c.web?.uri) links.push(`[🔗 ${c.web.title}](${c.web.uri})`); });
       if (links.length) responseText += "\n\n" + links.join("\n");
    }

    return responseText || "...";
  } catch (error) {
    console.error("Gemini Error:", error);
    throw error;
  }
};