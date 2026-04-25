import React from 'react';
import ComplaintDossier from './ComplaintDossier';

function MessageBubble({ message }) {
  const isUser = message.role === 'user';
  const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  const isSummary = !isUser && message.content && message.content.includes('**Complaint Review & Summary**');

  // Simple formatter for bold text and newlines
  const formatContent = (text) => {
    if (!text) return '';
    
    // Split by bold markers
    const parts = text.split(/(\*\*.*?\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i} className="font-bold">{part.slice(2, -2)}</strong>;
      }
      return part;
    });
  };

  if (isSummary) {
    // Split message into summary and follow-up text
    const parts = message.content.split(/\n\n(?=Please review|If you need to change)/);
    const summaryContent = parts[0];
    const followUpText = parts.slice(1).join('\n\n');

    return (
      <div className="flex justify-start mb-6 w-full animate-in fade-in slide-in-from-bottom-2 duration-500">
        <div className="max-w-[95%] w-full">
          <ComplaintDossier content={summaryContent} />
          {followUpText && (
            <div className="mt-2 ml-2 bg-white text-gray-700 rounded-2xl rounded-tl-none px-4 py-3 shadow-sm border border-gray-100 text-sm">
              {formatContent(followUpText)}
            </div>
          )}
          <div className="text-[10px] mt-1 ml-4 text-gray-400 font-medium uppercase tracking-wider">
            Case Handler Agent • {timestamp}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4 group`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-3 transition-all ${
          isUser
            ? 'bg-gradient-to-br from-blue-600 to-blue-700 text-white rounded-br-none shadow-md hover:shadow-lg'
            : 'bg-white text-gray-800 rounded-bl-none shadow-sm border border-gray-100 hover:border-blue-100'
        }`}
      >
        <div className="text-sm leading-relaxed whitespace-pre-wrap">
          {formatContent(message.content)}
        </div>
        <div
          className={`text-[10px] mt-1.5 font-medium opacity-60 ${
            isUser ? 'text-right' : 'text-left'
          }`}
        >
          {timestamp}
        </div>
      </div>
    </div>
  );
}

export default MessageBubble;

