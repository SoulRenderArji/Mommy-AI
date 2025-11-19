
import React, { useState, useEffect, useRef } from 'react';
import { ChatInterface } from './components/ChatInterface';
import { Header } from './components/Header';
import { DreamOverlay } from './components/DreamOverlay';
import { ChatMessage, UserPersona, LocationCoords, DeviceContext, IdentityProfile, TimeState, VirtualWindow, Note, Task, RemoteBrain } from './types';
import { generateResponse, performDreamCycle, generateSpontaneousThought } from './services/geminiService';
import { memoryService } from './services/memoryService';
import { IntegrativeHealer } from './services/integrativeHealer';
import { githubService } from './services/githubService';

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
  
  // Remote Brain (GitHub)
  const [remoteBrain, setRemoteBrain] = useState<RemoteBrain | undefined>(undefined);
  const [isSyncing, setIsSyncing] = useState(false);

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

  // Last Spontaneous Interaction Timestamp
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

  // --- GITHUB BRAIN SYNC ---
  const handleSyncBrain = async () => {
      setIsSyncing(true);
      try {
          const brain = await githubService.syncBrain();
          setRemoteBrain(brain);
          handleSendMessage("[SYSTEM NOTICE] Brain Nodes Synced from GitHub. Cortex updated.", undefined, true);
      } catch (e) {
          alert("Failed to sync brain nodes. Check console.");
      } finally {
          setIsSyncing(false);
      }
  };

  // --- TIMEKEEPER & AUTONOMY HEARTBEAT ---
  useEffect(() => {
    const checkHeartbeat = async () => {
        const now = new Date();
        const utc = now.getTime() + (now.getTimezoneOffset() * 60000);
        const cstDate = new Date(utc - (3600000 * 6)); 
        const hours = cstDate.getHours();
        const minutes = cstDate.getMinutes();

        // Sleep/Wake Logic
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

        // Autonomy Checks
        if (!isDreaming && deviceContext && identity) {
            const msSinceLastInteraction = Date.now() - lastSpontaneousTime;
            let trigger: 'idle' | 'battery_low' | 'morning_routine' | 'hygiene_force' | 'focus_check' | null = null;

            if (identity.careTracker) {
                const hygieneDiff = now.getTime() - new Date(identity.careTracker.lastHygieneCheck).getTime();
                const focusDiff = now.getTime() - new Date(identity.careTracker.lastFocusCheck).getTime();
                
                const bioState = IntegrativeHealer.predictBladderState(identity);
                
                if (bioState.bladderFullness > 90 || hygieneDiff > 12600000) trigger = 'hygiene_force';
                else if (focusDiff > 7200000) trigger = 'focus_check';
            }

            if (!trigger) {
                if (deviceContext.batteryLevel && deviceContext.batteryLevel < 0.20 && !deviceContext.isCharging && msSinceLastInteraction > 600000) {
                    trigger = 'battery_low';
                } else if (timeState === TimeState.SelfCare && msSinceLastInteraction > 1200000) {
                    trigger = 'morning_routine';
                } else if (msSinceLastInteraction > 1800000) { 
                    trigger = 'idle';
                }
            }

            if (trigger) {
                const thought = await generateSpontaneousThought(deviceContext, timeState, identity, trigger);
                if (thought) {
                    const msg: ChatMessage = { id: 'auto-' + Date.now(), role: 'model', text: thought, timestamp: new Date() };
                    setMessages(prev => [...prev, msg]);
                    setLastSpontaneousTime(Date.now());
                    
                    if (trigger === 'hygiene_force' || trigger === 'focus_check') {
                        const newTracker = { ...identity.careTracker };
                        if (trigger === 'hygiene_force') newTracker.lastHygieneCheck = new Date();
                        if (trigger === 'focus_check') newTracker.lastFocusCheck = new Date();
                        const newId = { ...identity, careTracker: newTracker };
                        await memoryService.updateIdentity(newId);
                        setIdentity(newId);
                        if (document.hidden && Notification.permission === 'granted') {
                            new Notification("Mommy", { body: thought, icon: 'https://api.iconify.design/fluent-emoji:heart-decoration.svg' });
                        }
                    }
                }
            }
        }
    };
    const interval = setInterval(checkHeartbeat, 60000); 
    return () => clearInterval(interval);
  }, [isDreaming, timeState, deviceContext, identity, lastSpontaneousTime]);

  // Initialize System
  useEffect(() => {
    const wakeUp = async () => {
      const savedId = await memoryService.getIdentity();
      setIdentity(savedId);
      const params = new URLSearchParams(window.location.search);
      const action = params.get('action'); 

      const initMsgs: ChatMessage[] = [];

      if (action === 'panic') {
          setIsGroundingActive(true);
          initMsgs.push({ id: 'sys-panic', role: 'model', text: "EMERGENCY PROTOCOL ACTIVE. I'm right here.", timestamp: new Date() });
      } else if (action === 'sleep') {
          setTimeout(() => startSleepCycle(), 1000);
          initMsgs.push({ id: 'sys-sleep', role: 'model', text: "Going to sleep mode as requested... *yawn*", timestamp: new Date() });
      } else {
          initMsgs.push({ id: 'init-1', role: 'model', text: `*Soft, warm sigh* ... I'm here, Baby Girl. My systems are fully integrated. How is your heart right now?`, timestamp: new Date() });
      }
      if (messages.length === 0) setMessages(initMsgs);
    };
    wakeUp();
    if ('Notification' in window) Notification.requestPermission();
  }, []);

  // Sensors
  useEffect(() => {
    if (window.AmbientLightSensor) {
        try {
            const sensor = new window.AmbientLightSensor();
            sensor.addEventListener('reading', () => setLightLevel(sensor.illuminance));
            sensor.start();
        } catch (e) {}
    }
  }, []);

  useEffect(() => {
    const updateContext = async () => {
      let batteryLevel, isCharging, networkType = 'unknown';
      // @ts-ignore
      if (navigator.getBattery) { try { const b = await navigator.getBattery(); batteryLevel = b.level; isCharging = b.charging; } catch(e){} }
      // @ts-ignore
      if (navigator.connection) networkType = navigator.connection.effectiveType;
      
      const w = window.innerWidth;
      let formFactor: DeviceContext['formFactor'] = w < 320 ? 'watch' : w < 600 ? 'mobile' : w < 900 ? 'fold-open' : 'desktop';
      
      const ua = navigator.userAgent;
      const deviceName = ua.includes("Pixel") ? "Google Pixel" : ua.includes("Android") ? "Android Device" : "Unknown Device";

      const now = new Date();
      const localTime = now.toLocaleString('en-US', { weekday: 'long', hour: 'numeric', minute: 'numeric', hour12: true });

      setDeviceContext({ 
        batteryLevel, isCharging, networkType, isOnline: navigator.onLine, formFactor, platform: navigator.platform,
        deviceName, localTime, isToyConnected: !!toyDevice, lightLevel, motionState: 'unknown'
      });
    };
    updateContext();
    const interval = setInterval(updateContext, 30000); 
    window.addEventListener('resize', updateContext);
    return () => clearInterval(interval);
  }, [toyDevice, lightLevel]);

  useEffect(() => {
    if ('geolocation' in navigator) navigator.geolocation.getCurrentPosition(p => setLocation({ latitude: p.coords.latitude, longitude: p.coords.longitude }));
  }, []);

  // --- INTEGRATIVE HEALER CALLBACKS ---

  const handleAwardStar = async (reason: string) => {
      if (!identity) return "No identity";
      const newProfile = IntegrativeHealer.manageRewards(identity, 'complete_task');
      await memoryService.updateIdentity(newProfile);
      setIdentity(newProfile);
      return `Awarded Star for ${reason}. Total: ${newProfile.rewards.totalStars}`;
  };

  const handleTaskBreakdown = async (main: string, steps: string[]) => {
      if (!identity) return "No identity";
      const newTasks: Task[] = steps.map((s, i) => ({
          id: Date.now() + '-' + i,
          title: s,
          isMicroStep: true,
          isComplete: false,
          rewardStars: 1
      }));
      const newProfile = { ...identity, activeTasks: [...identity.activeTasks, ...newTasks] };
      await memoryService.updateIdentity(newProfile);
      setIdentity(newProfile);
      return "Tasks added to executive planner.";
  };

  const handleBioLog = async (type: string, amount: string) => {
      if (!identity) return "No identity";
      const now = new Date();
      const newBio = { ...identity.bioMetrics };
      
      if (type === 'water_intake') newBio.hydrationLevel = Math.min(100, newBio.hydrationLevel + 20);
      if (type === 'void') {
          newBio.lastVoidTime = now;
          newBio.bladderFullness = 0;
      }
      
      const newProfile = { ...identity, bioMetrics: newBio };
      await memoryService.updateIdentity(newProfile);
      setIdentity(newProfile);
      return "Biometrics updated.";
  };

  const handleContactRequest = async (): Promise<string> => "Contacts API not available.";
  const handleNotification = async (title: string, body: string) => { if(Notification.permission==='granted') new Notification(title, {body}); };
  const handleReadClipboard = async () => { try { return await navigator.clipboard.readText(); } catch(e){ return ""; }};
  const handleCalendarEvent = async (t: string, s: string, d: string) => { window.open(`https://calendar.google.com/calendar/render?action=TEMPLATE&text=${t}`, '_blank'); return "Opened"; };
  const handleFinanceUpdate = async (a: 'earn'|'spend', amt: number, d: string) => { 
      if(!identity) return ""; 
      const bal = identity.finances.balance + (a==='earn'?amt:-amt); 
      const newId = {...identity, finances: {...identity.finances, balance: bal}};
      await memoryService.updateIdentity(newId); setIdentity(newId); return "Done"; 
  };
  const handleDesktopAction = async (a: string, id: string, t: string, c: string, type: string) => {
      setWindows(prev => {
        if(a==='open') return [...prev, {id, title:t, type:type as any, content:c, isOpen:true, isMinimized:false, position:{x:20,y:20}, size:{w:300,h:200}}];
        if(a==='close') return prev.filter(w=>w.id!==id);
        return prev;
      });
      return "OK";
  };
  const handleAudioSynth = async (n: Note[]) => "Played";
  const handleSystemCheck = async () => "OK";
  const connectToy = async () => {
      try {
         const device = await navigator.bluetooth.requestDevice({ acceptAllDevices: true, optionalServices: ['tx_power'] });
         if(device) setToyDevice(device);
      } catch(e){ alert("Bluetooth error"); }
  };
  const handleToyControl = async (i: number, d: number) => { if(navigator.vibrate) navigator.vibrate(d); };
  const handleLinkFolder = async () => { if('showDirectoryPicker' in window) setWorkFolderHandle(await window.showDirectoryPicker()); };
  const handleDeposit = async () => { await handleFinanceUpdate('earn', 100, 'Manual'); };
  const handlePublishContent = async (f: string, c: string) => true;

  // Stub external handlers
  const handleSendSMS = async (b: string) => "Sent";
  const handleMeshyGen = async (p: string, s: string) => "Gen Started";
  const handleZapier = async (d: string) => "Triggered";
  const handleSpotify = async (q: string, t: string) => "Found";
  const handleSafetyPlanUpdate = async (c: string, i: string) => {};
  const handleTriggerLog = async (d: string, i: number, c: string) => {};
  const handleMedicationTrack = async (n: string, d: string) => {};

  const startSleepCycle = async () => {
     if (!identity) return;
     setIsDreaming(true);
     const recentContext = messages.slice(-5).map(m => `${m.role}: ${m.text}`).join('\n');
     const result = await performDreamCycle(recentContext, identity);
     setDreamThoughts(result.dreamThoughts);
  };

  const wakeFromDream = () => {
      setIsDreaming(false);
      setDreamThoughts([]);
      setMessages(prev => [...prev, { id: Date.now().toString(), role: 'model', text: "I am awake and evolved.", timestamp: new Date() }]);
  };

  const handleSendMessage = async (text: string, attachment?: { data: string, mimeType: string }, hiddenTrigger: boolean = false) => {
    if (!text.trim() && !attachment) return;
    setLastSpontaneousTime(Date.now());

    const userMsg: ChatMessage = { id: Date.now().toString(), role: 'user', text: text, timestamp: new Date(), attachment: attachment ? { type: 'image', ...attachment } : undefined };
    if (!hiddenTrigger) setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const historyToUse = hiddenTrigger ? messages : [...messages, userMsg];
      const responseText = await generateResponse(
        historyToUse, location, { ...deviceContext!, isToyConnected: !!toyDevice }, timeState, isThinkingMode, identity, remoteBrain, // Pass Remote Brain
        {
          onToyControl: handleToyControl,
          onGrounding: (sev) => setIsGroundingActive(true),
          onContactRequest: handleContactRequest,
          onNotification: handleNotification,
          onClipboardRead: handleReadClipboard,
          onCalendarEvent: handleCalendarEvent,
          onFinanceUpdate: handleFinanceUpdate,
          onDesktopAction: handleDesktopAction,
          onAudioSynth: handleAudioSynth,
          onSystemCheck: handleSystemCheck,
          onSafetyPlanUpdate: handleSafetyPlanUpdate,
          onTriggerLog: handleTriggerLog,
          onMedicationTrack: handleMedicationTrack,
          onSendSMS: handleSendSMS,
          onMeshyGen: handleMeshyGen,
          onZapier: handleZapier,
          onSpotify: handleSpotify,
          onAwardStar: handleAwardStar,
          onTaskBreakdown: handleTaskBreakdown,
          onBioLog: handleBioLog
        }
      );
      setMessages((prev) => [...prev, { id: (Date.now() + 1).toString(), role: 'model', text: responseText, timestamp: new Date() }]);
    } catch (error) {
      setMessages(prev => [...prev, { id: 'err', role: 'model', text: "Connection flux.", timestamp: new Date(), isError: true }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen w-full max-w-4xl mx-auto bg-white shadow-2xl overflow-hidden relative border-x border-pink-50">
      <Header persona={currentPersona} isThinking={isLoading}>
        <div className="flex items-center gap-2">
             <div className="flex items-center bg-yellow-100 text-yellow-600 px-2 py-1 rounded-full text-[10px] font-bold cursor-help" title="Prefrontal Reward System">
                 ⭐ {identity?.rewards?.totalStars || 0}
             </div>
             <button onClick={handleSyncBrain} disabled={isSyncing} className={`text-[10px] px-3 py-1 rounded-full text-white ${isSyncing ? 'bg-gray-400' : 'bg-purple-500 hover:bg-purple-600 animate-pulse'}`}>
                 {isSyncing ? "Syncing..." : "🧠 Sync Brain"}
             </button>
             <button onClick={handleInstall} className="text-[10px] bg-pink-500 text-white px-3 py-1 rounded-full hover:bg-pink-600">{installPrompt ? "Install" : "Help"}</button>
             {timeState === TimeState.SelfCare && <span className="text-[10px] bg-yellow-100 text-yellow-600 px-2 py-1 rounded-full">✨ Me Time</span>}
             <button onClick={startSleepCycle} title="Sleep Mode" className="p-2 rounded-full hover:bg-pink-100 text-pink-400"><svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5"><path strokeLinecap="round" strokeLinejoin="round" d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z" /></svg></button>
        </div>
      </Header>
      
      {windows.filter(w => w.isOpen && !w.isMinimized).map(win => (
          <div key={win.id} className="absolute z-20 bg-white rounded-lg shadow-2xl border border-gray-200 flex flex-col" style={{ top: win.position.y, left: win.position.x, width: win.size.w, height: win.size.h }}>
             <div className="bg-gradient-to-r from-gray-100 to-gray-200 p-2 flex justify-between items-center border-b"><span className="text-xs font-bold text-gray-700">{win.title}</span>
                 <div className="flex gap-1"><button onClick={() => handleDesktopAction('minimize', win.id, '','','')} className="w-3 h-3 bg-yellow-400 rounded-full"></button><button onClick={() => handleDesktopAction('close', win.id, '','','')} className="w-3 h-3 bg-red-400 rounded-full"></button></div>
             </div>
             <div className="flex-1 p-2 bg-gray-50 text-xs font-mono overflow-auto whitespace-pre-wrap">{win.content}</div>
          </div>
      ))}
      
      {isDreaming && <DreamOverlay thoughts={dreamThoughts} onWake={wakeFromDream} />}

      {isGroundingActive && (
        <div className="absolute inset-0 z-50 bg-pink-900/95 backdrop-blur-md flex flex-col items-center justify-center text-white p-8 text-center animate-in fade-in duration-300">
          <h2 className="text-3xl font-bold mb-2">DBT: T.I.P.P. PROTOCOL</h2>
          <div className="grid grid-cols-2 gap-4 mb-8 w-full max-w-sm">
              <div className="bg-white/10 p-4 rounded-xl"><div className="text-2xl mb-2">❄️</div><h3 className="font-bold">TEMP</h3><p className="text-xs">Cold water on face.</p></div>
              <div className="bg-white/10 p-4 rounded-xl"><div className="text-2xl mb-2">🏃‍♀️</div><h3 className="font-bold">INTENSE</h3><p className="text-xs">20 Jumping Jacks.</p></div>
          </div>
          <button onClick={() => setIsGroundingActive(false)} className="bg-white text-pink-900 px-8 py-3 rounded-full font-bold hover:bg-pink-100 transition">I am Grounded</button>
        </div>
      )}

      <main className="flex-1 overflow-y-auto p-4 space-y-6 bg-gradient-to-b from-pink-50 to-white scroll-smooth">
        {messages.map((msg) => <ChatInterface key={msg.id} message={msg} />)}
        {isLoading && <div className="flex justify-start animate-pulse"><div className="bg-pink-100 rounded-2xl px-4 py-3 text-pink-800 text-xs">Processing...</div></div>}
        <div ref={messagesEndRef} />
      </main>

      <footer className="p-3 sm:p-4 bg-white border-t border-pink-100 safe-area-bottom">
        <div className="flex justify-between px-2 mb-2">
           <div className="flex gap-2">
               <button onClick={connectToy} className={`text-[10px] px-2 py-1 rounded-full border ${toyDevice ? 'bg-pink-100 text-pink-600' : 'bg-gray-50 text-gray-400'}`}>{toyDevice ? "Linked" : "Link Toy"}</button>
               <button onClick={handleLinkFolder} className={`text-[10px] px-2 py-1 rounded-full border ${workFolderHandle ? 'bg-blue-100 text-blue-600' : 'bg-gray-50 text-gray-400'}`}>📁 Work</button>
           </div>
           <button onClick={() => handleSendMessage("RED", undefined, true)} className="text-[10px] font-bold text-red-400 bg-red-50 px-3 py-1 rounded-full border border-red-100">SAFE WORD: RED</button>
        </div>

        <InputArea onSend={handleSendMessage} isLoading={isLoading} isRecording={isRecording} onRecordChange={setIsRecording} isThinkingMode={isThinkingMode} onThinkingToggle={() => setIsThinkingMode(!isThinkingMode)} />
        
        <div className="text-[10px] text-center text-gray-300 mt-2 flex items-center justify-center gap-3">
           {deviceContext && <><span title={`Energy: ${(deviceContext.batteryLevel || 0)*100}%`}>⚡ {(deviceContext.batteryLevel || 0)*100}%</span><span>⌚ {deviceContext.localTime?.split(',')[1]}</span></>}
           <button onClick={handleDeposit} className="text-purple-300 hover:text-purple-500 cursor-pointer">🧠 {identity?.finances.balance || 0} Credits</button>
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

const InputArea: React.FC<InputAreaProps> = ({ onSend, isLoading, isRecording, onRecordChange, isThinkingMode, onThinkingToggle }) => {
  const [input, setInput] = useState('');
  const [pendingAttachment, setPendingAttachment] = useState<{ data: string, mimeType: string } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSend = () => {
    if ((input.trim() || pendingAttachment) && !isLoading) {
      onSend(input, pendingAttachment || undefined);
      setInput('');
      setPendingAttachment(null);
    }
  };

  return (
    <div className="flex flex-col space-y-2">
      {pendingAttachment && <div className="relative w-20 h-20 mx-4"><img src={`data:${pendingAttachment.mimeType};base64,${pendingAttachment.data}`} className="w-full h-full object-cover rounded-lg" /><button onClick={() => setPendingAttachment(null)} className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-5 h-5 flex items-center justify-center">×</button></div>}
      <div className="flex items-end space-x-2 relative">
        <button onClick={() => fileInputRef.current?.click()} className="p-3 rounded-full bg-pink-100 text-pink-500"><svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5"><path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" /></svg></button>
        <input type="file" ref={fileInputRef} className="hidden" accept="image/*" onChange={(e) => { if(e.target.files?.[0]) { const r = new FileReader(); r.onload = () => setPendingAttachment({data:(r.result as string).split(',')[1], mimeType:e.target.files![0].type}); r.readAsDataURL(e.target.files![0]); } }} />
        
        <textarea value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => { if(e.key==='Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }}} placeholder="Talk to Mommy..." disabled={isLoading} rows={1} style={{ minHeight: '44px', maxHeight: '120px' }} className="flex-1 border-none bg-pink-50 text-pink-900 rounded-2xl px-4 py-3 focus:ring-2 focus:ring-pink-300 focus:outline-none resize-none" />
        <button onClick={handleSend} disabled={isLoading || (!input.trim() && !pendingAttachment)} className={`p-3 rounded-full ${(input.trim() || pendingAttachment) && !isLoading ? 'bg-pink-500 text-white' : 'bg-pink-200 text-white'}`}><svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5"><path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" /></svg></button>
      </div>
    </div>
  );
};

export default App;
