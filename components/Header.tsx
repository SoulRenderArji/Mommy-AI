
import React from 'react';
import { UserPersona } from '../types';

interface HeaderProps {
  persona: UserPersona;
  children?: React.ReactNode;
  isThinking?: boolean; // New Prop for visualizing brain activity
}

export const Header: React.FC<HeaderProps> = ({ persona, children, isThinking }) => {
  return (
    <header className="bg-white/80 backdrop-blur-md px-6 py-4 border-b border-pink-100 sticky top-0 z-10 flex justify-between items-center relative overflow-hidden">
      {/* Neural Pulse Effect (Bicameral Visualization) */}
      {isThinking && (
        <div className="absolute inset-0 opacity-20 pointer-events-none">
            {/* Left Hemisphere (Blue/Logic) */}
            <div className="absolute left-0 top-0 w-1/2 h-full bg-blue-400 blur-2xl animate-pulse-fast"></div>
            {/* Right Hemisphere (Pink/Creative) */}
            <div className="absolute right-0 top-0 w-1/2 h-full bg-pink-400 blur-2xl animate-pulse-fast" style={{ animationDelay: '0.5s' }}></div>
        </div>
      )}

      <div className="flex items-center space-x-3 relative z-10">
        <div className="relative">
          <div className={`w-10 h-10 rounded-full bg-gradient-to-br ${isThinking ? 'from-blue-400 to-pink-600 animate-spin-slow' : 'from-pink-400 to-pink-600'} flex items-center justify-center text-white font-bold shadow-md transition-all duration-500`}>
            {persona === UserPersona.Mommy ? 'M' : 'S'}
          </div>
          <div className="absolute bottom-0 right-0 w-3 h-3 bg-green-400 border-2 border-white rounded-full"></div>
        </div>
        <div>
          <h1 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
            {persona === UserPersona.Mommy ? 'Mommy' : 'Sunshine'}
            {isThinking && <span className="text-[10px] text-purple-500 font-mono bg-purple-50 px-1 rounded animate-pulse">NEURAL_SYNC</span>}
          </h1>
          <p className="text-xs text-pink-400 font-medium">
            {isThinking ? 'Synthesizing Logic & Emotion...' : (persona === UserPersona.Mommy ? 'Here for you' : 'Listening...')}
          </p>
        </div>
      </div>
      
      <div className="relative z-10 flex items-center">
        {children}
      </div>
    </header>
  );
};
