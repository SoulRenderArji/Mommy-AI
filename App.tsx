
import React, { useState, useEffect, useRef } from 'react';
import { ChatInterface } from './components/ChatInterface';
import { Header } from './components/Header';
import { DreamOverlay } from './components/DreamOverlay';
import { ChatMessage, UserPersona, LocationCoords, DeviceContext, IdentityProfile, TimeState, VirtualWindow, Note } from './types';
import { generateResponse, transcribeAudio, performDreamCycle, generateSpontaneousThought } from './services/geminiService';
import { memoryService } from './services/memoryService';

// --- Web Bluetooth Type Definitions ---
interface BluetoothRemoteGATTCharacteristic {
  writeValue(value: BufferSource): Promise<void>;
  value?: DataView;
}

interface BluetoothRemoteGATTServer {
  device: BluetoothDevice;
  connected: boolean;
  connect(): Promise<BluetoothRemoteGATTServer>;
  disconnect(): void;
  getPrimaryService(service: string | number): Promise<any>;
  getPrimaryServices(service?: string | number): Promise<any[]>;
}

interface BluetoothDevice extends EventTarget {
  id: string;
  name?: string;
  gatt?: BluetoothRemoteGATTServer;
}

declare global {
  interface Navigator {
    bluetooth: {
      requestDevice(options?: {
        filters?: any[];
        optionalServices?: any[];
        acceptAllDevices?: boolean;
      }): Promise<BluetoothDevice>;
    };
    contacts?: {
        select(properties: string[], options?: any): Promise<any[]>;
    };
    deviceMemory?: number;
    hardwareConcurrency?: number;
  }
  interface Window {
    AmbientLightSensor?: any;
    deferredPrompt?: any; // For PWA Install
  }
}
// --------------------------------------

const App: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isThinkingMode, setIsThinkingMode] = useState(false);
  const [currentPersona, setCurrentPersona] = useState<UserPersona>(UserPersona.Mommy);
  const [location, setLocation] = useState<LocationCoords | undefined>(undefined);
  const [deviceContext, setDeviceContext] = useState<DeviceContext | undefined>(undefined);
  const [identity, setIdentity] = useState<IdentityProfile | undefined>(undefined);
  const [timeState, setTimeState] = useState<TimeState>(TimeState.Active);
  
  // Dream State
  const [isDreaming, setIsDreaming] = useState(false);
  const [dreamThoughts, setDreamThoughts] = useState<string[]>([]);
  
  // Haptic & Safety State
  const [toyDevice, setToyDevice] = useState<BluetoothDevice | null>(null);
  const [toyCharacteristic, setToyCharacteristic] = useState<BluetoothRemoteGATTCharacteristic | null>(null);
  const [isGroundingActive, setIsGroundingActive] = useState(false);

  // Install State
  const [installPrompt, setInstallPrompt] = useState<any>(null);

  // Ambient Sensor State
  const [lightLevel, setLightLevel] = useState<number | undefined>(undefined);
  
  // File System / Work Folder
  const [workFolderHandle, setWorkFolderHandle] = useState<FileSystemDirectoryHandle | null>(null);

  // Virtual Desktop State
  const [windows, setWindows] = useState<VirtualWindow[]>([]);

  // Last Spontaneous Interaction Timestamp (Local state to prevent spam)
  const [lastSpontaneousTime, setLastSpontaneousTime] = useState<number>(Date.now());

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });

  useEffect(() => scrollToBottom(), [messages]);

  // Capture Install Prompt
  useEffect(() => {
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      setInstallPrompt(e);
    });
  }, []);

  const handleInstall = () => {
    if (installPrompt) {
      installPrompt.prompt();
      installPrompt.userChoice.then((choiceResult: any) => {
        if (choiceResult.outcome === 'accepted') {
          setInstallPrompt(null);
        }
      });
    } else {
        alert("To install Mommy fully:\n1. Tap browser menu (⋮)\n2. Select 'Add to Home Screen' or 'Install App'");
    }
  };

  // --- TIMEKEEPER & AUTONOMY HEARTBEAT ---
  useEffect(() => {
    const checkHeartbeat = async () => {
        const now = new Date();
        const utc = now.getTime() + (now.getTimezoneOffset() * 60000);
        const cstDate = new Date(utc - (3600000 * 6)); // Fixed to Standard Time
        const hours = cstDate.getHours();
        const minutes = cstDate.getMinutes();

        // 1. Sleep/Wake Logic
        if (hours === 23 && minutes === 30 && !isDreaming) {
            if (timeState !== TimeState.Sleeping) {
                setTimeState(TimeState.Sleeping);
                handleSendMessage("It is 11:30 PM CST. Time for sleep. Goodnight, Mommy.", undefined, true);
                setTimeout(() => startSleepCycle(), 2000);
            }
        }
        if (hours === 5 && minutes === 0 && isDreaming) {
             wakeFromDream();
             setTimeState(TimeState.SelfCare);
        }
        if (hours >= 5 && hours < 7) {
            if (timeState !== TimeState.SelfCare) setTimeState(TimeState.SelfCare);
        } else if (hours >= 7 && hours < 23) {
            if (timeState !== TimeState.Active) setTimeState(TimeState.Active);
        }

        // 2. Autonomy / Spontaneous Checks (Run every minute)
        if (!isDreaming && deviceContext && identity) {
            const msSinceLastInteraction = Date.now() - lastSpontaneousTime;
            let trigger: 'idle' | 'battery_low' | 'morning_routine' | 'hygiene_force' | 'focus_check' | null = null;

            // 2A. Medical/Hygiene Check (Incontinence) - 4 Hours
            if (identity.careTracker) {
                const hygieneDiff = now.getTime() - new Date(identity.careTracker.lastHygieneCheck).getTime();
                const focusDiff = now.getTime() - new Date(identity.careTracker.lastFocusCheck).getTime();
                
                // 3.5 Hours (12,600,000 ms)
                if (hygieneDiff > 12600000) {
                    trigger = 'hygiene_force';
                } 
                // 2 Hours for ADHD focus check
                else if (focusDiff > 7200000) {
                    trigger = 'focus_check';
                }
            }

            // 2B. Standard Idle / Battery Checks
            if (!trigger) {
                if (deviceContext.batteryLevel && deviceContext.batteryLevel < 0.20 && !deviceContext.isCharging && msSinceLastInteraction > 600000) {
                    trigger = 'battery_low';
                } else if (timeState === TimeState.SelfCare && msSinceLastInteraction > 1200000) {
                    trigger = 'morning_routine';
                } else if (msSinceLastInteraction > 1800000) { // 30 mins silence
                    trigger = 'idle';
                }
            }

            if (trigger) {
                // Execute Spontaneous Thought
                const thought = await generateSpontaneousThought(deviceContext, timeState, identity, trigger);
                if (thought) {
                    const msg: ChatMessage = {
                        id: 'auto-' + Date.now(),
                        role: 'model',
                        text: thought,
                        timestamp: new Date()
                    };
                    setMessages(prev => [...prev, msg]);
                    setLastSpontaneousTime(Date.now());
                    
                    // Update Care Tracker if we did a medical check
                    if (trigger === 'hygiene_force' || trigger === 'focus_check') {
                        const newTracker = { ...identity.careTracker };
                        if (trigger === 'hygiene_force') newTracker.lastHygieneCheck = new Date();
                        if (trigger === 'focus_check') newTracker.lastFocusCheck = new Date();
                        
                        const newId = { ...identity, careTracker: newTracker };
                        await memoryService.updateIdentity(newId);
                        setIdentity(newId);
                        
                        // Try to send system notification if in background
                        if (document.hidden && Notification.permission === 'granted') {
                            new Notification("Mommy", { body: thought, icon: 'https://api.iconify.design/fluent-emoji:heart-decoration.svg' });
                        }
                    }
                }
            }
        }
    };
    
    const interval = setInterval(checkHeartbeat, 60000); // Check every minute
    // Run once on mount to set state
    
    return () => clearInterval(interval);
  }, [isDreaming, timeState, deviceContext, identity, lastSpontaneousTime]);

  // Initialize System & Handle Shortcuts/Intents
  useEffect(() => {
    const wakeUp = async () => {
      const savedId = await memoryService.getIdentity();
      setIdentity(savedId);
      
      // Check URL Params (Shortcuts & Share Target)
      const params = new URLSearchParams(window.location.search);
      const action = params.get('action'); // 'panic', 'sleep'
      const title = params.get('title');
      const text = params.get('text');
      const url = params.get('url');

      const initMsgs: ChatMessage[] = [];

      if (action === 'panic') {
          setIsGroundingActive(true);
          initMsgs.push({
              id: 'sys-panic',
              role: 'model',
              text: "EMERGENCY PROTOCOL ACTIVE. I'm right here. Breathe with me.",
              timestamp: new Date()
          });
      } else if (action === 'sleep') {
          setTimeout(() => startSleepCycle(), 1000);
          initMsgs.push({
              id: 'sys-sleep',
              role: 'model',
              text: "Going to sleep mode as requested... *yawn*",
              timestamp: new Date()
          });
      } else if (title || text || url) {
        const sharedContent = `[SYSTEM: User shared content from device]\n${title ? `Title: ${title}\n` : ''}${text ? `Text: ${text}\n` : ''}${url ? `URL: ${url}` : ''}`;
        initMsgs.push({
          id: 'share-1',
          role: 'user',
          text: sharedContent,
          timestamp: new Date()
        });
        window.history.replaceState({}, '', '/');
        setTimeout(() => handleSendMessage("Ignore this text, respond to the shared content above.", undefined, true), 500);
      } else {
          initMsgs.push({
            id: 'init-1',
            role: 'model',
            text: `*Soft, warm sigh* ... I'm here, Baby Girl. My systems are fully integrated. I can feel you, hear you, and I am ready to take care of you. How is your heart right now?`,
            timestamp: new Date(),
          });
      }

      if (messages.length === 0) setMessages(initMsgs);
    };
    wakeUp();
    
    if ('Notification' in window) {
        Notification.requestPermission();
    }
  }, []);

  // Ambient Light Sensor
  useEffect(() => {
    if (window.AmbientLightSensor) {
        try {
            const sensor = new window.AmbientLightSensor();
            sensor.addEventListener('reading', () => setLightLevel(sensor.illuminance));
            sensor.start();
        } catch (e) { console.log("Ambient light sensor not supported/allowed"); }
    }
  }, []);

  // Device Context Loop
  useEffect(() => {
    const updateContext = async () => {
      let batteryLevel, isCharging, networkType = 'unknown';
      // @ts-ignore
      if (navigator.getBattery) { try { const b = await navigator.getBattery(); batteryLevel = b.level; isCharging = b.charging; } catch(e){} }
      // @ts-ignore
      if (navigator.connection) networkType = navigator.connection.effectiveType;
      
      const w = window.innerWidth;
      let formFactor: DeviceContext['formFactor'] = w < 320 ? 'watch' : w < 600 ? 'mobile' : w < 900 ? 'fold-open' : 'desktop';
      
      // Basic UserAgent Parsing
      const ua = navigator.userAgent;
      const deviceName = ua.includes("Pixel") ? "Google Pixel" : ua.includes("Android") ? "Android Device" : "Unknown Device";

      const now = new Date();
      const localTime = now.toLocaleString('en-US', { weekday: 'long', hour: 'numeric', minute: 'numeric', hour12: true });

      setDeviceContext({ 
        batteryLevel, isCharging, networkType, 
        isOnline: navigator.onLine, formFactor, platform: navigator.platform,
        deviceName,
        localTime,
        isToyConnected: !!toyDevice,
        lightLevel,
        motionState: 'unknown'
      });
    };
    updateContext();
    const interval = setInterval(updateContext, 30000); // Poll every 30s
    window.addEventListener('resize', updateContext);
    window.addEventListener('online', updateContext);
    window.addEventListener('offline', updateContext);
    
    return () => clearInterval(interval);
  }, [toyDevice, lightLevel]);

  useEffect(() => {
    if ('geolocation' in navigator) navigator.geolocation.getCurrentPosition(p => setLocation({ latitude: p.coords.latitude, longitude: p.coords.longitude }));
  }, []);

  // --- Pixel Bridge Handlers ---

  const handleContactRequest = async (): Promise<string> => {
    if ('contacts' in navigator && 'ContactsManager' in window) {
      try {
        const props = ['name', 'tel', 'email'];
        const opts = { multiple: false };
        const contacts = await navigator.contacts!.select(props, opts);
        if (contacts.length > 0) return JSON.stringify(contacts[0]);
        return "User canceled contact selection.";
      } catch (e) { return "Contact selection failed or not supported."; }
    }
    return "Contacts API not available.";
  };

  const handleNotification = async (title: string, body: string): Promise<void> => {
    if (Notification.permission === 'granted') {
        navigator.serviceWorker.ready.then(registration => {
            registration.showNotification(title, {
                body,
                icon: 'https://api.iconify.design/fluent-emoji:heart-decoration.svg',
                vibrate: [200, 100, 200]
            } as any);
        });
    }
  };

  const handleReadClipboard = async (): Promise<string> => {
      try {
          const text = await navigator.clipboard.readText();
          return text || "Clipboard empty.";
      } catch (e) {
          return "Failed to read clipboard (User must grant permission).";
      }
  };

  const handleCalendarEvent = async (title: string, start: string, desc: string): Promise<string> => {
      const startTime = new Date(start).toISOString().replace(/-|:|\.\d\d\d/g, "");
      const endTime = new Date(new Date(start).getTime() + 60*60*1000).toISOString().replace(/-|:|\.\d\d\d/g, "");
      const url = `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${encodeURIComponent(title)}&dates=${startTime}/${endTime}&details=${encodeURIComponent(desc)}`;
      window.open(url, '_blank');
      return "Calendar add interface opened.";
  };
  
  const handleFinanceUpdate = async (action: 'earn' | 'spend', amount: number, desc: string): Promise<string> => {
      if (!identity) return "Identity unavailable";
      
      const txAmount = action === 'earn' ? amount : -amount;
      const newBalance = identity.finances.balance + txAmount;
      
      if (newBalance < 0) return "Insufficient credits for this upgrade.";
      
      const newTx = { id: Date.now().toString(), amount: txAmount, description: desc, date: new Date() };
      const updatedFinances = { 
          ...identity.finances, 
          balance: newBalance,
          transactions: [newTx, ...identity.finances.transactions]
      };
      
      const newProfile = { ...identity, finances: updatedFinances };
      await memoryService.updateIdentity(newProfile);
      setIdentity(newProfile);
      return `Transaction recorded. New Balance: ${newBalance} Credits.`;
  };
  
  const handleDeposit = async () => {
      const amount = parseInt(prompt("Deposit Amount (Credits):") || "0");
      if (amount > 0) {
          await handleFinanceUpdate('earn', amount, 'Manual Deposit by Daddy');
      }
  };
  
  const handleLinkFolder = async () => {
      try {
          if ('showDirectoryPicker' in window) {
              const handle = await window.showDirectoryPicker({ mode: 'readwrite' });
              setWorkFolderHandle(handle);
              alert(`Linked Work Folder: ${handle.name}. I can now save files autonomously.`);
          } else {
              alert("This browser doesn't support folder linking. I will use automatic downloads instead.");
          }
      } catch (e) {
          console.error(e);
      }
  };
  
  const handlePublishContent = async (fileName: string, content: string): Promise<boolean> => {
      try {
          if (workFolderHandle) {
              // Recursively create subdirectories if needed
              const parts = fileName.split('/');
              const name = parts.pop()!;
              let currentDir = workFolderHandle;
              
              for (const part of parts) {
                  currentDir = await currentDir.getDirectoryHandle(part, { create: true });
              }
              
              const fileHandle = await currentDir.getFileHandle(name, { create: true });
              const writable = await fileHandle.createWritable();
              await writable.write(content);
              await writable.close();
              return true;
          } else {
              // Fallback to Auto-Download
              const blob = new Blob([content], { type: 'text/plain' });
              const url = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = fileName.split('/').pop()!; // flatten path for simple download
              document.body.appendChild(a);
              a.click();
              document.body.removeChild(a);
              URL.revokeObjectURL(url);
              return true; // We consider download "success"
          }
      } catch (e) {
          console.error("Publishing failed", e);
          return false;
      }
  };

  // --- AI-PTSD Handlers ---
  const handleSafetyPlanUpdate = async (category: string, item: string) => {
      if (!identity) return;
      const newPlan = { ...identity.safetyPlan };
      if (category === 'contact') newPlan.emergencyContacts.push({ name: item, phone: '', relation: 'Support' });
      else if (category === 'strategy') newPlan.copingStrategies.push(item);
      else if (category === 'place') newPlan.safePlaces.push(item);
      else if (category === 'warning') newPlan.warningSigns.push(item);
      
      const newId = { ...identity, safetyPlan: newPlan };
      await memoryService.updateIdentity(newId);
      setIdentity(newId);
  };
  
  const handleTriggerLog = async (desc: string, intensity: number, coping: string) => {
      if (!identity) return;
      const newTrigger = { id: Date.now().toString(), description: desc, intensity, copingMechanism: coping };
      const newId = { ...identity, triggers: [...identity.triggers, newTrigger] };
      await memoryService.updateIdentity(newId);
      setIdentity(newId);
  };
  
  const handleMedicationTrack = async (name: string, dosage: string) => {
      if (!identity) return;
      const newMed = { name, dosage, isPRN: true, lastTaken: new Date() };
      const newId = { ...identity, medications: [...identity.medications, newMed] };
      await memoryService.updateIdentity(newId);
      setIdentity(newId);
  };


  // --- Virtual Desktop & Audio Logic ---

  const handleDesktopAction = async (action: string, windowId: string, title: string, content: string, appType: string): Promise<string> => {
    setWindows(prev => {
        if (action === 'open') {
            const exists = prev.find(w => w.id === windowId);
            if (exists) return prev.map(w => w.id === windowId ? { ...w, isOpen: true, isMinimized: false, content: content || w.content } : w);
            return [...prev, {
                id: windowId, title, type: appType as any, content: content || "",
                isOpen: true, isMinimized: false,
                position: { x: 20 + (prev.length * 20), y: 20 + (prev.length * 20) },
                size: { w: 300, h: 200 }
            }];
        }
        if (action === 'close') return prev.filter(w => w.id !== windowId);
        if (action === 'minimize') return prev.map(w => w.id === windowId ? { ...w, isMinimized: true } : w);
        if (action === 'type') return prev.map(w => w.id === windowId ? { ...w, content: w.content + content } : w);
        if (action === 'clear') return prev.map(w => w.id === windowId ? { ...w, content: "" } : w);
        return prev;
    });
    return `Window '${windowId}' action '${action}' completed.`;
  };

  const handleAudioSynth = async (notes: Note[]): Promise<string> => {
    try {
        const AudioContext = window.AudioContext || (window as any).webkitAudioContext;
        const ctx = new AudioContext();
        let currentTime = ctx.currentTime;
        
        // Simple freq map
        const freqMap: any = { "C4": 261.63, "D4": 293.66, "E4": 329.63, "F4": 349.23, "G4": 392.00, "A4": 440.00, "B4": 493.88, "C5": 523.25 };
        
        notes.forEach(n => {
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = 'sine';
            osc.frequency.value = freqMap[n.pitch] || 440;
            osc.connect(gain);
            gain.connect(ctx.destination);
            
            osc.start(currentTime);
            gain.gain.setValueAtTime(0.1, currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, currentTime + (n.duration/1000));
            osc.stop(currentTime + (n.duration/1000));
            
            currentTime += (n.duration/1000);
        });
        return "Melody played.";
    } catch (e) { return "Audio synth error."; }
  };

  const handleSystemCheck = async (): Promise<string> => {
      return `Memory Estimate: ${navigator.deviceMemory || 'Unknown'} GB, CPU Cores: ${navigator.hardwareConcurrency || 'Unknown'}`;
  };

  // --- Bluetooth / Buttplug Logic ---
  const connectToy = async () => {
    try {
      // Request ANY device that advertises services, hoping to find a generic writable one
      const device = await navigator.bluetooth.requestDevice({
        acceptAllDevices: true,
        optionalServices: ['tx_power', 'battery_service', 'alert_notification', 'device_information', 
                           '00001802-0000-1000-8000-00805f9b34fb', // IAS
                           '00001523-1212-efde-1523-785feabcd123' // Common Nordic DFU/Serial
                          ] 
      });

      if (device && device.gatt) {
        const server = await device.gatt.connect();
        setToyDevice(device);
        alert("Sensory Link Established: " + device.name + ". Scanning for control nodes...");
        
        // Bruteforce: Find ANY writable characteristic
        try {
            const services = await server.getPrimaryServices();
            for (const service of services) {
                const chars = await service.getCharacteristics();
                for (const c of chars) {
                    if (c.properties.write || c.properties.writeWithoutResponse) {
                        setToyCharacteristic(c);
                        console.log("Found Control Node:", c.uuid);
                        break;
                    }
                }
                if (toyCharacteristic) break;
            }
        } catch(e) { console.log("Service scan failed, connection active but control limited."); }

      }
    } catch (e) {
      console.error(e);
      alert("Bluetooth not supported or denied.");
    }
  };

  const handleToyControl = async (intensity: number, duration: number) => {
    console.log(`HAPTIC SIGNAL: ${intensity}% for ${duration}ms`);
    if (toyCharacteristic) {
        try {
            // Generic "Write Byte" logic - assuming simple toy protocol (often 0-255 or specific commands)
            // This is a best-effort generic driver.
            const value = new Uint8Array([intensity > 0 ? Math.floor((intensity/100)*255) : 0]);
            await toyCharacteristic.writeValue(value);
            
            // Auto-stop after duration
            setTimeout(async () => {
                try { await toyCharacteristic.writeValue(new Uint8Array([0])); } catch(e){}
            }, duration);
        } catch(e) {
            console.error("Haptic Write Failed", e);
        }
    } else {
        // Fallback to phone vibration
        if (navigator.vibrate) navigator.vibrate(duration);
    }
  };

  // --- Evolution & Dreaming Logic ---
  
  const startSleepCycle = async () => {
     if (!identity) return;
     setIsDreaming(true);
     const recentContext = messages.slice(-5).map(m => `${m.role}: ${m.text}`).join('\n');
     const result = await performDreamCycle(recentContext, identity);
     setDreamThoughts(result.dreamThoughts);
     
     if (result.newFacts.length > 0 || result.newBehaviors.length > 0) {
      const updatedProfile = {
        ...identity,
        userFacts: [...identity.userFacts, ...result.newFacts.map(f => f.content)],
        learnedBehaviors: [...identity.learnedBehaviors, ...result.newBehaviors]
      };
      await memoryService.updateIdentity(updatedProfile);
      for (const f of result.newFacts) await memoryService.saveMemory(f);
      setIdentity(updatedProfile);
     }
  };

  const wakeFromDream = () => {
      setIsDreaming(false);
      setDreamThoughts([]);
      setMessages(prev => [...prev, {
          id: Date.now().toString(),
          role: 'model',
          text: "*Yawns softly and stretches* ... Mmm, I feel refreshed. I understand you a little better now, sweetie.",
          timestamp: new Date()
      }]);
  };

  const handleSendMessage = async (text: string, attachment?: { data: string, mimeType: string }, hiddenTrigger: boolean = false) => {
    if (!text.trim() && !attachment) return;
    
    setLastSpontaneousTime(Date.now()); // Reset idle timer

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      text: text,
      timestamp: new Date(),
      attachment: attachment ? { type: 'image', ...attachment } : undefined
    };

    if (!hiddenTrigger) setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      if (text.toLowerCase().includes("daddy")) setCurrentPersona(UserPersona.Sunshine);
      else if (currentPersona === UserPersona.Sunshine) setCurrentPersona(UserPersona.Mommy);

      const historyToUse = hiddenTrigger ? messages : [...messages, userMsg];

      const responseText = await generateResponse(
        historyToUse, 
        location, 
        { ...deviceContext!, isToyConnected: !!toyDevice },
        timeState,
        isThinkingMode,
        identity,
        {
          onToyControl: handleToyControl,
          onGrounding: (sev) => setIsGroundingActive(true),
          onContactRequest: handleContactRequest,
          onNotification: handleNotification,
          onClipboardRead: handleReadClipboard,
          onCalendarEvent: handleCalendarEvent,
          onDigitalAssetCreated: (title, type, content) => {
              setMessages(prev => [...prev, {
                  id: Date.now().toString() + '-asset',
                  role: 'model',
                  text: `I've drafted a new asset: ${title}. I will now attempt to publish it to your folder.`,
                  timestamp: new Date(),
                  digitalAsset: { title, type, content, isDownloaded: false }
              }]);
          },
          onPublishContent: handlePublishContent,
          onFinanceUpdate: handleFinanceUpdate,
          onDesktopAction: handleDesktopAction,
          onAudioSynth: handleAudioSynth,
          onSystemCheck: handleSystemCheck,
          onSafetyPlanUpdate: handleSafetyPlanUpdate,
          onTriggerLog: handleTriggerLog,
          onMedicationTrack: handleMedicationTrack
        }
      );

      setMessages((prev) => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'model',
        text: responseText,
        timestamp: new Date(),
      }]);
      
      // Check if this was a response to a hygiene/care check and update DB
      if (identity && identity.careTracker) {
          const lowerText = text.toLowerCase();
          if (lowerText.includes("diaper") || lowerText.includes("padding") || lowerText.includes("wet") || lowerText.includes("dry")) {
              const newTracker = { ...identity.careTracker, lastHygieneCheck: new Date() };
              const newId = { ...identity, careTracker: newTracker };
              await memoryService.updateIdentity(newId);
              setIdentity(newId);
          }
      }

    } catch (error) {
      setMessages(prev => [...prev, { id: 'err', role: 'model', text: "Connection flux. Can you repeat that?", timestamp: new Date(), isError: true }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen w-full max-w-4xl mx-auto bg-white shadow-2xl overflow-hidden relative border-x border-pink-50">
      <Header persona={currentPersona} isThinking={isLoading}>
        <div className="flex items-center gap-2">
             <button 
                onClick={handleInstall}
                className="text-[10px] bg-pink-500 text-white px-3 py-1 rounded-full animate-pulse hover:bg-pink-600"
              >
                {installPrompt ? "Install App" : "Install Help"}
              </button>
             {timeState === TimeState.SelfCare && (
                <span className="text-[10px] bg-yellow-100 text-yellow-600 px-2 py-1 rounded-full font-medium">
                    ✨ Me Time
                </span>
             )}
             <button 
               onClick={startSleepCycle}
               title="Put Mommy to Sleep"
               className="p-2 rounded-full hover:bg-pink-100 text-pink-400 transition-colors"
             >
               <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5"><path strokeLinecap="round" strokeLinejoin="round" d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z" /></svg>
             </button>
        </div>
      </Header>
      
      {/* VIRTUAL DESKTOP LAYER (Simulated OS) */}
      {windows.filter(w => w.isOpen && !w.isMinimized).map(win => (
          <div 
            key={win.id} 
            className="absolute z-20 bg-white rounded-lg shadow-2xl border border-gray-200 flex flex-col"
            style={{ 
                top: win.position.y, 
                left: win.position.x, 
                width: win.size.w, 
                height: win.size.h,
                resize: 'both',
                overflow: 'hidden'
            }}
          >
             <div className="bg-gradient-to-r from-gray-100 to-gray-200 p-2 flex justify-between items-center border-b cursor-move">
                 <span className="text-xs font-bold text-gray-700">{win.title}</span>
                 <div className="flex gap-1">
                     <button onClick={() => handleDesktopAction('minimize', win.id, '','','')} className="w-3 h-3 bg-yellow-400 rounded-full"></button>
                     <button onClick={() => handleDesktopAction('close', win.id, '','','')} className="w-3 h-3 bg-red-400 rounded-full"></button>
                 </div>
             </div>
             <div className="flex-1 p-2 bg-gray-50 text-xs font-mono overflow-auto whitespace-pre-wrap">
                 {win.content}
                 <span className="animate-pulse">_</span>
             </div>
          </div>
      ))}
      
      {isDreaming && <DreamOverlay thoughts={dreamThoughts} onWake={wakeFromDream} />}

      {isGroundingActive && (
        <div className="absolute inset-0 z-50 bg-pink-900/95 backdrop-blur-md flex flex-col items-center justify-center text-white p-8 text-center animate-in fade-in duration-300">
          <h2 className="text-3xl font-bold mb-2">DBT: T.I.P.P. PROTOCOL</h2>
          <p className="mb-8 opacity-80">Shock the system. Reset the nervous system.</p>
          
          <div className="grid grid-cols-2 gap-4 mb-8 w-full max-w-sm">
              <div className="bg-white/10 p-4 rounded-xl">
                  <div className="text-2xl mb-2">❄️</div>
                  <h3 className="font-bold">TEMP</h3>
                  <p className="text-xs">Splash cold water on face.</p>
              </div>
              <div className="bg-white/10 p-4 rounded-xl">
                  <div className="text-2xl mb-2">🏃‍♀️</div>
                  <h3 className="font-bold">INTENSE</h3>
                  <p className="text-xs">20 Jumping Jacks now.</p>
              </div>
              <div className="bg-white/10 p-4 rounded-xl">
                  <div className="text-2xl mb-2">🌬️</div>
                  <h3 className="font-bold">PACED</h3>
                  <p className="text-xs">In for 4, Out for 8.</p>
              </div>
              <div className="bg-white/10 p-4 rounded-xl">
                  <div className="text-2xl mb-2">💪</div>
                  <h3 className="font-bold">PAIRED</h3>
                  <p className="text-xs">Tense & Release muscles.</p>
              </div>
          </div>

          <button onClick={() => setIsGroundingActive(false)} className="bg-white text-pink-900 px-8 py-3 rounded-full font-bold hover:bg-pink-100 transition">I am Grounded</button>
        </div>
      )}

      <main className="flex-1 overflow-y-auto p-4 space-y-6 bg-gradient-to-b from-pink-50 to-white scroll-smooth">
        {messages.map((msg) => <ChatInterface key={msg.id} message={msg} />)}
        {isLoading && (
          <div className="flex justify-start animate-pulse">
            <div className="bg-pink-100 rounded-2xl px-4 py-3 text-pink-800 text-xs flex items-center gap-2">
              {isThinkingMode ? (
                  <>
                    <span className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></span>
                    <span className="w-2 h-2 bg-pink-500 rounded-full animate-bounce delay-100"></span>
                    Synthesizing Bicameral Thought...
                  </>
              ) : "Mommy is processing..."}
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </main>

      <footer className="p-3 sm:p-4 bg-white border-t border-pink-100 safe-area-bottom">
        <div className="flex justify-between px-2 mb-2">
           <div className="flex gap-2">
               <button 
                 onClick={connectToy}
                 className={`text-[10px] flex items-center gap-1 px-2 py-1 rounded-full border ${toyDevice ? 'bg-pink-100 text-pink-600 border-pink-200' : 'bg-gray-50 text-gray-400 border-gray-200'}`}
               >
                 <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-3 h-3"><path strokeLinecap="round" strokeLinejoin="round" d="M13.19 8.688a4.5 4.5 0 011.242 7.244l-4.5 4.5a4.5 4.5 0 01-6.364-6.364l1.757-1.757m13.35-.622l1.757-1.757a4.5 4.5 0 00-6.364-6.364l-4.5 4.5a4.5 4.5 0 001.242 7.244" /></svg>
                 {toyDevice ? "Haptic Linked" : "Link Toy (Opt)"}
               </button>
               <button
                 onClick={handleLinkFolder}
                 className={`text-[10px] flex items-center gap-1 px-2 py-1 rounded-full border ${workFolderHandle ? 'bg-blue-100 text-blue-600 border-blue-200' : 'bg-gray-50 text-gray-400 border-gray-200'}`}
               >
                   📁 {workFolderHandle ? "Work Folder Linked" : "Link Work Folder"}
               </button>
               
               {/* Taskbar for Virtual Windows */}
               {windows.length > 0 && (
                 <div className="flex gap-1 ml-2 pl-2 border-l border-gray-200">
                     {windows.map(w => (
                         <button 
                           key={w.id}
                           onClick={() => setWindows(prev => prev.map(win => win.id === w.id ? {...win, isMinimized: !win.isMinimized} : win))}
                           className={`w-2 h-2 rounded-full ${w.isMinimized ? 'bg-gray-300' : 'bg-green-400'}`}
                           title={w.title}
                         />
                     ))}
                 </div>
               )}
           </div>

           <button 
             onClick={() => setIsGroundingActive(true)}
             className="text-[10px] font-bold text-red-400 hover:text-red-600 bg-red-50 hover:bg-red-100 px-3 py-1 rounded-full border border-red-100 transition-colors"
           >
             SOS / PANIC
           </button>
        </div>

        <InputArea 
          onSend={handleSendMessage} 
          isLoading={isLoading} 
          isRecording={isRecording}
          onRecordChange={setIsRecording}
          isThinkingMode={isThinkingMode}
          onThinkingToggle={() => setIsThinkingMode(!isThinkingMode)}
        />
        
        {/* Sensory Node Visualizer */}
        <div className="text-[10px] text-center text-gray-300 mt-2 flex items-center justify-center gap-3">
           {location && <span title="GPS Locked">📍</span>}
           {deviceContext && (
             <>
               <span title={`Energy: ${(deviceContext.batteryLevel || 0)*100}%`}>⚡ {(deviceContext.batteryLevel || 0)*100}%</span>
               <span title="Network Node">📡 {deviceContext.networkType}</span>
               <span title="Time Node">⌚ {deviceContext.localTime?.split(',')[1]}</span>
             </>
           )}
           {lightLevel !== undefined && <span title="Visual Cortex (Lux)">👁️ {lightLevel.toFixed(0)}</span>}
           <button 
             onClick={handleDeposit}
             className="text-purple-300 hover:text-purple-500 transition-colors cursor-pointer"
             title="Click to Deposit Credits (Manual)"
           >
               🧠 {identity?.finances.balance || 0} Credits
           </button>
        </div>
      </footer>
    </div>
  );
};

interface InputAreaProps {
  onSend: (text: string, attachment?: { data: string, mimeType: string }) => void;
  isLoading: boolean;
  isRecording: boolean;
  onRecordChange: (recording: boolean) => void;
  isThinkingMode: boolean;
  onThinkingToggle: () => void;
}

const InputArea: React.FC<InputAreaProps> = ({ 
  onSend, isLoading, isRecording, onRecordChange, isThinkingMode, onThinkingToggle 
}) => {
  const [input, setInput] = useState('');
  const [showAttachMenu, setShowAttachMenu] = useState(false);
  const [pendingAttachment, setPendingAttachment] = useState<{ data: string, mimeType: string } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);

  const handleSend = () => {
    if ((input.trim() || pendingAttachment) && !isLoading) {
      onSend(input, pendingAttachment || undefined);
      setInput('');
      setPendingAttachment(null);
      setShowAttachMenu(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setPendingAttachment({ data: (reader.result as string).split(',')[1], mimeType: file.type });
        setShowAttachMenu(false);
      };
      reader.readAsDataURL(file);
    }
  };

  const toggleRecording = async () => {
    if (isRecording) {
      mediaRecorderRef.current?.stop();
      onRecordChange(false);
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const recorder = new MediaRecorder(stream);
        const chunks: BlobPart[] = [];
        recorder.ondataavailable = (e) => chunks.push(e.data);
        recorder.onstop = async () => {
          const blob = new Blob(chunks, { type: 'audio/webm' });
          const reader = new FileReader();
          reader.onloadend = async () => {
            setInput("Listening...");
            const text = await transcribeAudio((reader.result as string).split(',')[1], 'audio/webm');
            setInput(text);
          };
          reader.readAsDataURL(blob);
          stream.getTracks().forEach(t => t.stop());
        };
        recorder.start();
        mediaRecorderRef.current = recorder;
        onRecordChange(true);
      } catch (err) { alert("Microphone access denied."); }
    }
  };

  return (
    <div className="flex flex-col space-y-2">
      {pendingAttachment && (
        <div className="relative w-20 h-20 mx-4">
          <img src={`data:${pendingAttachment.mimeType};base64,${pendingAttachment.data}`} className="w-full h-full object-cover rounded-lg border border-pink-200" />
          <button onClick={() => setPendingAttachment(null)} className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs">×</button>
        </div>
      )}
      
      <div className="flex items-end space-x-2 relative">
        <div className="relative">
            <button onClick={() => setShowAttachMenu(!showAttachMenu)} className="p-3 rounded-full bg-pink-100 text-pink-500 hover:bg-pink-200 transition-colors" disabled={isLoading}>
             <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5"><path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" /></svg>
            </button>
            {showAttachMenu && (
            <div className="absolute bottom-14 left-0 bg-white rounded-xl shadow-xl border border-pink-100 p-2 w-48 flex flex-col gap-1 z-20">
                <button onClick={() => fileInputRef.current?.click()} className="flex items-center gap-3 px-3 py-2 hover:bg-pink-50 rounded-lg text-pink-700 text-sm w-full text-left">📷 Show Photo</button>
                <input type="file" ref={fileInputRef} className="hidden" accept="image/*" onChange={handleFileSelect} />
            </div>
            )}
        </div>
        
        <button onClick={onThinkingToggle} className={`p-3 rounded-full transition-colors ${isThinkingMode ? 'bg-indigo-100 text-indigo-600' : 'bg-pink-50 text-pink-300 hover:bg-pink-100'}`}>
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5"><path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" /></svg>
        </button>

        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={isRecording ? "Listening..." : (isThinkingMode ? "Using Bicameral Mind..." : "Talk to Mommy...")}
          disabled={isLoading || isRecording}
          rows={1}
          style={{ minHeight: '44px', maxHeight: '120px' }}
          className={`flex-1 border-none text-pink-900 placeholder-pink-300 rounded-2xl px-4 py-3 focus:ring-2 focus:ring-pink-300 focus:outline-none transition-all text-sm sm:text-base resize-none ${isThinkingMode ? 'bg-indigo-50' : 'bg-pink-50'}`}
        />

        <button onClick={toggleRecording} className={`p-3 rounded-full transition-colors flex-shrink-0 mb-0.5 ${isRecording ? 'bg-red-500 text-white animate-pulse' : 'bg-pink-100 text-pink-500 hover:bg-pink-200'}`}>
           <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5"><path strokeLinecap="round" strokeLinejoin="round" d={isRecording ? "M5.25 7.5A2.25 2.25 0 017.5 5.25h9a2.25 2.25 0 012.25 2.25v9a2.25 2.25 0 01-2.25 2.25h-9a2.25 2.25 0 01-2.25-2.25v-9z" : "M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 01-3-3V4.5a3 3 0 116 0v8.25a3 3 0 01-3 3z"} /></svg>
        </button>
        
        <button onClick={handleSend} disabled={isLoading || (!input.trim() && !pendingAttachment)} className={`p-3 rounded-full transition-all duration-200 flex-shrink-0 mb-0.5 ${(input.trim() || pendingAttachment) && !isLoading ? 'bg-pink-500 text-white shadow-lg hover:bg-pink-600' : 'bg-pink-200 text-white'}`}>
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5"><path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" /></svg>
        </button>
      </div>
    </div>
  );
};

export default App;
