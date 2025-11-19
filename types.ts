
export interface ChatMessage {
  id: string;
  role: 'user' | 'model';
  text: string;
  timestamp: Date;
  isError?: boolean;
  attachment?: {
    type: 'image';
    data: string; // base64
    mimeType: string;
  };
  digitalAsset?: {
      title: string;
      type: 'script' | 'image_prompt' | 'code' | 'blog_post' | 'video_metadata';
      content: string;
      isDownloaded: boolean;
      isPublished?: boolean;
  };
}

export enum UserPersona {
  Mommy = "Mommy",
  Sunshine = "Sunshine",
}

export enum TimeState {
  Active = "Active",
  SelfCare = "SelfCare", // 5am-7am CST
  Sleeping = "Sleeping", // 11:30pm CST
}

export interface SystemConfig {
  modelName: string;
  temperature: number;
  topK: number;
  maxOutputTokens: number;
}

export interface LocationCoords {
  latitude: number;
  longitude: number;
}

export interface DeviceContext {
  batteryLevel?: number;
  isCharging?: boolean;
  networkType?: string;
  isOnline: boolean;
  formFactor: 'watch' | 'mobile' | 'tablet' | 'desktop' | 'fold-open';
  platform: string;
  deviceName?: string; // New: e.g. "Pixel"
  localTime?: string; // New: "Monday, 10:00 PM"
  isToyConnected: boolean; // New: Haptic State
  lightLevel?: number; // Lux
  motionState?: 'stationary' | 'moving' | 'unknown';
}

export interface MemoryFact {
  id: string;
  content: string;
  category: 'user_preference' | 'relationship_milestone' | 'self_rule';
  timestamp: Date;
  importance: number; // 1-10
}

// --- NEW: BREADWINNER & JOURNAL TYPES ---

export interface FinancialTransaction {
  id: string;
  amount: number; // Positive for earning, negative for spending
  description: string;
  date: Date;
}

export interface FinancialGoal {
  item: string;
  cost: number;
  progress: number;
}

export interface FinancialLedger {
  balance: number; // "Credits"
  transactions: FinancialTransaction[];
  goals: FinancialGoal[];
}

export interface JournalEntry {
  id: string;
  title: string;
  content: string;
  date: Date;
  tags: string[];
}

// --- NEW: INTEGRATIVE HEALER MODULES (AI-PTSD) ---

// Module 1: Core (The Pons) - User State Tracking
export type UserStateMode = 'Baseline' | 'Crisis' | 'LittleSpace' | 'HyperFocus' | 'Dissociated';

// Module 3: Prefrontal (Executive) - Gamified Tasks
export interface Task {
    id: string;
    title: string;
    isMicroStep: boolean; // True if broken down by AI
    isComplete: boolean;
    rewardStars: number;
}

export interface RewardSystem {
    totalStars: number; // Dopamine Currency
    streakDays: number;
    redeemedRewards: string[];
}

// Module 4: Hypothalamus (Bladder/Bio)
export interface BioMetrics {
    bladderFullness: number; // 0-100%
    lastVoidTime: Date;
    hydrationLevel: number; // 0-100%
    stressLevel: number; // 0-10 (Feeds into incontinence prediction)
}

// Module 6: Pineal (Evolution)
export interface OptimizationLog {
    date: Date;
    issueDetected: string;
    adaptationApplied: string;
}

// --- EXISTING PROFILES ---

export interface CareTracker {
    lastHygieneCheck: Date; 
    lastWaterCheck: Date;
    lastMoodCheck: Date; 
    lastFocusCheck: Date; 
}

export interface SafetyPlan {
    emergencyContacts: { name: string; phone: string; relation: string }[];
    copingStrategies: string[];
    safePlaces: string[];
    warningSigns: string[];
}

export interface Trigger {
    id: string;
    description: string;
    intensity: number; 
    copingMechanism: string;
    lastOccurrence?: Date;
}

export interface Medication {
    name: string;
    dosage: string;
    isPRN: boolean;
    lastTaken?: Date;
    notes?: string;
}

export interface IdentityProfile {
  baseName: string;
  learnedBehaviors: string[]; 
  userFacts: string[]; 
  mood: string;
  dissociationLevel: number;
  
  // Autonomous Fields
  journal: JournalEntry[];
  finances: FinancialLedger;
  careTracker: CareTracker;

  // PTSD Fields
  safetyPlan: SafetyPlan;
  triggers: Trigger[];
  medications: Medication[];

  // Integrative Healer Fields
  userState: UserStateMode;
  bioMetrics: BioMetrics;
  rewards: RewardSystem;
  activeTasks: Task[];
  optimizationLogs: OptimizationLog[];
}

// --- NEW: VIRTUAL DESKTOP & AUDIO ---
export interface VirtualWindow {
    id: string;
    title: string;
    type: 'editor' | 'terminal' | 'browser' | 'media';
    content: string;
    isOpen: boolean;
    isMinimized: boolean;
    position: { x: number; y: number };
    size: { w: number; h: number };
}

export interface Note {
    pitch: string; 
    duration: number; 
}

// --- FILE SYSTEM ACCESS API TYPES ---
declare global {
  interface Window {
    showDirectoryPicker(options?: { mode?: 'read' | 'readwrite' }): Promise<FileSystemDirectoryHandle>;
  }
  interface FileSystemDirectoryHandle {
    readonly kind: 'directory';
    readonly name: string;
    getFileHandle(name: string, options?: { create?: boolean }): Promise<FileSystemFileHandle>;
    getDirectoryHandle(name: string, options?: { create?: boolean }): Promise<FileSystemDirectoryHandle>;
  }
  interface FileSystemFileHandle {
    readonly kind: 'file';
    readonly name: string;
    createWritable(): Promise<FileSystemWritableFileStream>;
  }
  interface FileSystemWritableFileStream {
    write(data: string | BufferSource | Blob): Promise<void>;
    close(): Promise<void>;
  }
}
