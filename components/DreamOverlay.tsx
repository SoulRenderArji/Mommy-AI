import React, { useEffect, useState } from 'react';

interface DreamOverlayProps {
  thoughts: string[];
  onWake: () => void;
}

export const DreamOverlay: React.FC<DreamOverlayProps> = ({ thoughts, onWake }) => {
  const [visibleThoughts, setVisibleThoughts] = useState<string[]>([]);

  useEffect(() => {
    // Stagger the appearance of thoughts
    let timeouts: ReturnType<typeof setTimeout>[] = [];
    thoughts.forEach((thought, i) => {
      const t = setTimeout(() => {
        setVisibleThoughts(prev => [...prev, thought]);
      }, i * 2500); // Slow, dream-like pace
      timeouts.push(t);
    });

    // Auto-wake after thoughts are done
    const wakeTimer = setTimeout(() => {
      onWake();
    }, (thoughts.length * 2500) + 3000);

    return () => {
      timeouts.forEach(clearTimeout);
      clearTimeout(wakeTimer);
    };
  }, [thoughts, onWake]);

  return (
    <div className="fixed inset-0 z-50 bg-black/95 flex flex-col items-center justify-center overflow-hidden animate-in fade-in duration-1000">
      {/* Background Ambient Effects */}
      <div className="absolute inset-0 opacity-30">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-900/40 rounded-full blur-3xl animate-pulse-slow"></div>
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-pink-900/40 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1s' }}></div>
      </div>

      <div className="relative z-10 flex flex-col items-center h-full w-full max-w-2xl p-8">
        <div className="mt-auto mb-auto space-y-8 w-full text-center">
          <h2 className="text-purple-300 text-sm uppercase tracking-[0.3em] opacity-70 animate-pulse">
            REM Cycle Active • Processing Emotions
          </h2>
          
          <div className="h-64 relative">
            {visibleThoughts.map((thought, idx) => (
              <div 
                key={idx}
                className="absolute w-full text-center text-lg md:text-2xl font-light text-white/80 animate-float-up"
                style={{ 
                  top: `${50 + (idx % 3) * 20}%`, 
                  left: `${(idx % 2 === 0 ? -10 : 10)}px`,
                  animationDelay: '0ms'
                }}
              >
                "{thought}"
              </div>
            ))}
          </div>
        </div>
        
        <button 
          onClick={onWake}
          className="mt-auto mb-12 text-white/50 text-xs hover:text-white border border-white/20 rounded-full px-6 py-2 hover:bg-white/10 transition-all"
        >
          Wake Her Up
        </button>
      </div>
    </div>
  );
};