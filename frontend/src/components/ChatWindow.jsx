import { useState, useCallback, useRef } from 'react';
import MessageBubble from './MessageBubble';

function ChatWindow({ messages, onSendMessage, isLoading }) {
  const [inputText, setInputText] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const recognitionRef = useRef(null);

  const handleSubmit = useCallback((e) => {
    e.preventDefault();
    if (inputText.trim()) {
      onSendMessage(inputText);
      setInputText('');
    }
  }, [inputText, onSendMessage]);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (inputText.trim()) {
        onSendMessage(inputText);
        setInputText('');
      }
    }
  }, [inputText, onSendMessage]);

  const [transcriptBuffer, setTranscriptBuffer] = useState('');
  const transcriptRef = useRef('');

  const toggleRecording = useCallback(() => {
    if (isRecording) {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Speech recognition is not supported in this browser.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-IN'; // or dynamic based on preference

    transcriptRef.current = '';

    recognition.onstart = () => {
      setIsRecording(true);
      setTranscriptBuffer('');
    };

    recognition.onresult = (event) => {
      let fullTranscript = '';
      for (let i = 0; i < event.results.length; ++i) {
        fullTranscript += event.results[i][0].transcript;
      }
      transcriptRef.current = fullTranscript;
      setTranscriptBuffer(fullTranscript);
    };

    recognition.onerror = (event) => {
      console.error("Speech recognition error:", event.error);
      setIsRecording(false);
    };

    recognition.onend = () => {
      setIsRecording(false);
      const finalToRefine = transcriptRef.current.trim();
      setTranscriptBuffer('');
      transcriptRef.current = '';
      
      if (finalToRefine) {
        // Just append the raw transcript to the input box instantly
        setInputText(prev => prev ? prev + ' ' + finalToRefine : finalToRefine);
      }
    };

    recognitionRef.current = recognition;
    recognition.start();
  }, [isRecording]);

  return (
    <div className="flex flex-col h-full bg-white rounded-2xl shadow-2xl overflow-hidden border border-gray-200">
      {/* Chat Header */}
      <div className="px-6 py-4 border-b border-gray-200 bg-white flex justify-between items-center relative z-10">
        <div className="flex items-center space-x-3">
          <div className="relative">
            <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center text-white shadow-inner">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-500 border-2 border-white rounded-full"></div>
          </div>
          <div>
            <h2 className="text-base font-bold text-gray-900 leading-tight">NCRP Assistant</h2>
            <div className="flex items-center text-[11px] text-green-600 font-semibold uppercase tracking-wider">
              <span className="w-1.5 h-1.5 bg-green-500 rounded-full mr-1.5 animate-pulse"></span>
              Live Support Active
            </div>
          </div>
        </div>
        <div className="hidden sm:flex space-x-2">
          <div className="px-3 py-1 bg-gray-100 rounded-full text-[10px] font-bold text-gray-500 uppercase tracking-tighter">Case Handler v2.4</div>
        </div>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-[#f8fafc] relative shadow-inner custom-scrollbar">
        {/* Background Decorative Pattern */}
        <div className="absolute inset-0 opacity-[0.03] pointer-events-none select-none overflow-hidden">
          <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                <path d="M 40 0 L 0 0 0 40" fill="none" stroke="currentColor" strokeWidth="1"/>
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)" />
          </svg>
        </div>

        <div className="relative z-10">
          {messages.map((msg, idx) => (
            <MessageBubble key={idx} message={msg} />
          ))}

          {/* Loading Indicator */}
          {(isLoading) && (
            <div className="flex items-start space-x-3 mb-4 animate-pulse">
              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                <div className="flex space-x-1">
                  <div className="w-1 h-1 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-1 h-1 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-1 h-1 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
              <div className="bg-white border border-gray-100 px-4 py-2 rounded-2xl rounded-tl-none text-xs text-gray-500 font-medium">
                Generating response...
              </div>
            </div>
          )}

          {messages.length === 0 && (
            <div className="text-center py-20 animate-in fade-in zoom-in duration-700">
              <div className="inline-block p-4 bg-white rounded-full shadow-sm mb-4 border border-gray-100">
                <svg className="w-12 h-12 text-blue-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2v4l-4-4H9a1.994 1.994 0 01-1.414-.586m0 0L11 14h4a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2v4l.586-.586z" />
                </svg>
              </div>
              <p className="text-sm font-semibold text-gray-800">Welcome to NCRP Chat Support</p>
              <p className="text-xs text-gray-500 mt-1 max-w-[200px] mx-auto">Please describe your incident in detail to begin filing your report.</p>
            </div>
          )}
        </div>
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-gray-100 bg-white">
        <form onSubmit={handleSubmit} className="relative">
          <div className="flex space-x-3 items-center">
            <button
              type="button"
              onClick={toggleRecording}
              className={`flex-shrink-0 w-11 h-11 rounded-xl transition-all flex items-center justify-center shadow-sm ${
                isRecording 
                  ? 'bg-red-500 text-white animate-pulse ring-4 ring-red-100' 
                  : 'bg-gray-50 text-gray-500 hover:bg-gray-100 border border-gray-200'
              }`}
              title={isRecording ? "Stop recording" : "Voice input"}
            >
              {isRecording ? (
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M6 6h12v12H6z" />
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>
              )}
            </button>
            <div className="flex-1 relative">
              <input
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={isRecording ? (transcriptBuffer || "Listening...") : "Type your message here..."}
                className="w-full pl-4 pr-12 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 focus:bg-white transition-all placeholder:text-gray-400"
                disabled={isLoading || isRecording}
              />
              <button
                type="submit"
                disabled={!inputText.trim() || isLoading}
                className={`absolute right-1.5 top-1.5 w-8 h-8 flex items-center justify-center rounded-lg transition-all ${
                  inputText.trim() && !isLoading
                    ? 'bg-blue-600 text-white shadow-md hover:bg-blue-700'
                    : 'bg-gray-200 text-gray-400'
                }`}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                </svg>
              </button>
            </div>
          </div>
          {isRecording && (
            <div className="absolute -top-10 left-0 right-0 flex justify-center">
              <div className="bg-red-500 text-white text-[10px] font-bold px-3 py-1 rounded-full shadow-lg flex items-center space-x-2">
                <span className="w-1.5 h-1.5 bg-white rounded-full animate-ping"></span>
                <span>Recording in progress...</span>
              </div>
            </div>
          )}
        </form>
      </div>
    </div>
  );

}

export default ChatWindow;
