import React from 'react';
import { ChatMessage } from '../types';
import { MessageBubble } from './MessageBubble';

interface ChatInterfaceProps {
  message: ChatMessage;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ message }) => {
  const isUser = message.role === 'user';

  return (
    <div className={`flex w-full ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`flex max-w-[85%] ${isUser ? 'flex-row-reverse' : 'flex-row'} items-end gap-2`}>
        
        {/* Avatar */}
        <div className="flex-shrink-0 w-8 h-8 rounded-full overflow-hidden border-2 border-white shadow-sm">
          {isUser ? (
            <div className="w-full h-full bg-pink-300 flex items-center justify-center text-white text-xs font-bold">
              BG
            </div>
          ) : (
            <div className="w-full h-full bg-pink-500 flex items-center justify-center text-white text-xs font-bold">
              M
            </div>
          )}
        </div>

        {/* Bubble */}
        <MessageBubble message={message} isUser={isUser} />
      </div>
    </div>
  );
};