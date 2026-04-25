import { useState, useCallback, useRef } from 'react';
import MessageBubble from './MessageBubble';
import { refineSpeech } from '../services/api';

function ChatWindow({ messages, onSendMessage, isLoading }) {
  const [inputText, setInputText] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isRefining, setIsRefining] = useState(false);
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

    recognition.onend = async () => {
      setIsRecording(false);
      const finalToRefine = transcriptRef.current.trim();
      setTranscriptBuffer('');
      transcriptRef.current = '';
      
      if (finalToRefine) {
        setIsRefining(true);
        try {
          const data = await refineSpeech(finalToRefine);
          setInputText(prev => prev ? prev + ' ' + data.refined_text : data.refined_text);
        } catch (err) {
          console.error("Speech refinement error:", err);
          // Fallback to raw transcript if refinement fails
          setInputText(prev => prev ? prev + ' ' + finalToRefine : finalToRefine);
        } finally {
          setIsRefining(false);
        }
      }
    };

    recognitionRef.current = recognition;
    recognition.start();
  }, [isRecording]);

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow overflow-hidden">
      {/* Chat Header */}
      <div className="px-4 py-3 border-b border-gray-200 bg-gray-50 flex justify-between items-center">
        <div>
          <h2 className="text-lg font-semibold text-gray-800">Chat Assistant</h2>
          <p className="text-sm text-gray-500">Ask me anything about your cybercrime incident</p>
        </div>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
        {messages.map((msg, idx) => (
          <MessageBubble key={idx} message={msg} />
        ))}

        {/* Loading Indicator */}
        {(isLoading || isRefining) && (
          <div className="flex items-center space-x-2 text-gray-500">
            <div className="flex space-x-1">
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
            <span className="text-sm">{isRefining ? 'Refining speech...' : 'Typing...'}</span>
          </div>
        )}

        {messages.length === 0 && (
          <div className="text-center text-gray-400 py-8">
            <p>Start by describing what happened or use the microphone to speak</p>
          </div>
        )}
      </div>

      {/* Input Area */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-gray-200 bg-white">
        <div className="flex space-x-2 items-center">
          <button
            type="button"
            onClick={toggleRecording}
            className={`p-2 rounded-full transition-colors ${
              isRecording ? 'bg-red-100 text-red-600 animate-pulse' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
            title={isRecording ? "Stop recording" : "Speak to type"}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
            </svg>
          </button>
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={isRecording ? (transcriptBuffer || "Listening...") : "Type your message..."}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isLoading || isRefining || isRecording}
          />
          <button
            type="submit"
            disabled={!inputText.trim() || isLoading || isRefining}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
      </form>
    </div>
  );
}

export default ChatWindow;
