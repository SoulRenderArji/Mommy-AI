
import React from 'react';
import { ChatMessage } from '../types';

interface MessageBubbleProps {
  message: ChatMessage;
  isUser: boolean;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message, isUser }) => {
  const handleDownload = () => {
      if (!message.digitalAsset) return;
      const blob = new Blob([message.digitalAsset.content], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${message.digitalAsset.title.replace(/\s+/g, '_')}.${message.digitalAsset.type === 'code' ? 'ts' : 'txt'}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
  };

  return (
    <div
      className={`
        relative px-4 py-3 text-sm leading-relaxed shadow-sm
        ${
          isUser
            ? 'bg-pink-500 text-white rounded-2xl rounded-br-none'
            : 'bg-white text-pink-900 border border-pink-100 rounded-2xl rounded-bl-none'
        }
        ${message.isError ? 'border-red-300 bg-red-50 text-red-800' : ''}
      `}
    >
      {message.attachment && message.attachment.type === 'image' && (
        <div className="mb-3 -mx-1">
          <img 
            src={`data:${message.attachment.mimeType};base64,${message.attachment.data}`} 
            alt="Shared content" 
            className="rounded-lg max-h-48 w-auto object-cover border border-white/20"
          />
        </div>
      )}
      
      {message.digitalAsset && (
          <div className="mb-3 bg-purple-50 border border-purple-100 rounded-lg p-3">
              <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-purple-700 uppercase tracking-wide">{message.digitalAsset.type} ARTIFACT</span>
                  <span className="text-xs text-purple-400">Created by Mommy</span>
              </div>
              <h3 className="font-semibold text-purple-900 mb-2">{message.digitalAsset.title}</h3>
              <button 
                onClick={handleDownload}
                className="w-full bg-purple-600 hover:bg-purple-700 text-white text-xs py-2 rounded-md transition-colors flex items-center justify-center gap-2"
              >
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4"><path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M12 12.75l3 3m0 0l3-3m-3 3v-7.5" /></svg>
                  Download Asset
              </button>
          </div>
      )}

      <p className="whitespace-pre-wrap">{message.text}</p>
      <span
        className={`text-[10px] absolute bottom-1 ${
          isUser ? 'text-pink-200 right-3' : 'text-pink-300 right-3'
        }`}
      >
        {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
      </span>
    </div>
  );
};
