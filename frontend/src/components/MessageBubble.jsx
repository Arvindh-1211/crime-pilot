function MessageBubble({ message }) {
  const isUser = message.role === 'user';
  const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-3 ${
          isUser
            ? 'bg-blue-600 text-white rounded-br-none'
            : 'bg-white text-gray-800 rounded-bl-none shadow-sm'
        }`}
      >
        <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
        <div
          className={`text-xs mt-1 text-right ${
            isUser ? 'text-blue-100' : 'text-gray-400'
          }`}
        >
          {timestamp}
        </div>
      </div>
    </div>
  );
}

export default MessageBubble;
