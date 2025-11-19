
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

// --- NEW: CARE TRACKER (ADHD/Medical) ---
export interface CareTracker {
    lastHygieneCheck: Date; // Incontinence check
    lastWaterCheck: Date;
    lastMoodCheck: Date; // PTSD/Dissociation check
    lastFocusCheck: Date; // ADHD body doubling check
}

// --- NEW: AI-PTSD ARCHITECTURE ---
export interface SafetyPlan {
    emergencyContacts: { name: string; phone: string; relation: string }[];
    copingStrategies: string[]; // Things to do alone (e.g., "Listen to music", "Hold ice")
    safePlaces: string[]; // Physical or mental
    warningSigns: string[]; // Pre-crisis indicators
}

export interface Trigger {
    id: string;
    description: string;
    intensity: number; // 1-10
    copingMechanism: string;
    lastOccurrence?: Date;
}

export interface Medication {
    name: string;
    dosage: string;
    isPRN: boolean; // As needed
    lastTaken?: Date;
    notes?: string;
}

export interface IdentityProfile {
  baseName: string;
  learnedBehaviors: string[]; 
  userFacts: string[]; 
  mood: string;
  dissociationLevel: number; // 0 (Grounded) to 10 (Severe Dissociation) - AI-PTSD metric
  
  // New Autonomous Fields
  journal: JournalEntry[];
  finances: FinancialLedger;
  careTracker: CareTracker;

  // AI-PTSD Fields
  safetyPlan: SafetyPlan;
  triggers: Trigger[];
  medications: Medication[];
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
    pitch: string; // e.g., "C4", "A#3"
    duration: number; // ms
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
