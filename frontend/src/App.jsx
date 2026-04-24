import { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import ChatWindow from './components/ChatWindow';
import SlotProgress from './components/SlotProgress';
import EvidenceUpload from './components/EvidenceUpload';
import ComplaintSummary from './components/ComplaintSummary';
import { startSession, sendMessage, submitComplaint, uploadEvidence } from './services/api';
import './styles/index.css';

function App() {
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [progress, setProgress] = useState({ filled_count: 0, total_count: 0, percentage: 0, checklist: [] });
  const [categoryId, setCategoryId] = useState(null);
  const [filledSlots, setFilledSlots] = useState({});
  const [isComplete, setIsComplete] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [phoneNumbers, setPhoneNumbers] = useState([]);

  // Initialize session on mount
  useEffect(() => {
    const initSession = async () => {
      try {
        // Use a mock phone number for demo purposes
        const mockPhone = "9876543210";
        const response = await startSession(mockPhone);
        setSessionId(response.session_id);
        setMessages([{ role: 'assistant', content: response.welcome_message }]);
      } catch (err) {
        setError("Failed to initialize session. Please refresh the page.");
        setMessages([{ role: 'assistant', content: "Hello! I'm your NCRP Cybercrime Assistant. Let's get started. What type of cybercrime did you experience?" }]);
      }
    };
    initSession();
  }, []);

  // Handle sending a message
  const handleSendMessage = useCallback(async (text) => {
    if (!sessionId || !text.trim()) return;

    setIsLoading(true);
    setError(null);

    // Add user message to chat
    const userMessage = { role: 'user', content: text };
    setMessages(prev => [...prev, userMessage]);

    try {
      const response = await sendMessage(sessionId, text);

      // Update state from response
      setCategoryId(response.category_id || null);
      setFilledSlots(response.filled_slots || {});
      setProgress(response.progress || { filled_count: 0, total_count: 0, percentage: 0, checklist: [] });

      // Add bot message to chat
      const botMessage = { role: 'assistant', content: response.bot_response };
      setMessages(prev => [...prev, botMessage]);

      if (response.is_complete) {
        setIsComplete(true);
      }
    } catch (err) {
      setError("Failed to send message. Please try again.");
      setMessages(prev => [...prev, { role: 'assistant', content: "I encountered an error processing your message. Could you please rephrase?" }]);
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  // Handle submitting complaint
  const handleSubmitComplaint = useCallback(async () => {
    if (!sessionId || !phoneNumbers[0]) return;

    try {
      const response = await submitComplaint(sessionId, phoneNumbers[0]);

      // Store complaint details
      console.log("Complaint submitted:", response);

      // Update chat with confirmation
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Thank you! Your complaint has been successfully submitted with ID: ${response.complaint_id}`
      }]);
    } catch (err) {
      setError("Failed to submit complaint. Please try again.");
    }
  }, [sessionId, phoneNumbers]);

  // Handle evidence upload
  const handleEvidenceUpload = useCallback(async (file) => {
    if (!sessionId || !file) return;

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('session_id', sessionId);

      const response = await uploadEvidence(sessionId, file);

      // Add upload confirmation to chat
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Thank you! I've received your evidence file: ${file.name}`
      }]);
    } catch (err) {
      setError("Failed to upload evidence. Please try again.");
    }
  }, [sessionId]);

  // Get category badge color based on category ID
  const getCategoryColor = (catId) => {
    const colors = {
      'UPI_FRAUD': 'bg-red-100 text-red-800',
      'VISHING': 'bg-orange-100 text-orange-800',
      'PHISHING': 'bg-yellow-100 text-yellow-800',
      'INVESTMENT_SCAM': 'bg-purple-100 text-purple-800',
      'SEXTORTION': 'bg-red-900 text-red-100'
    };
    return colors[catId] || 'bg-gray-100 text-gray-800';
  };

  // Get category label
  const getCategoryLabel = (catId) => {
    const labels = {
      'UPI_FRAUD': 'UPI Fraud',
      'VISHING': 'Vishing',
      'PHISHING': 'Phishing',
      'INVESTMENT_SCAM': 'Investment Scam',
      'SEXTORTION': 'Sextortion'
    };
    return labels[catId] || catId;
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Header />

      <main className="flex-1 max-w-7xl mx-auto w-full p-4">
        {error && (
          <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Chat Window (2/3 width on desktop) */}
          <div className="lg:col-span-2 h-[600px] flex flex-col">
            <ChatWindow
              messages={messages}
              onSendMessage={handleSendMessage}
              isLoading={isLoading}
            />
          </div>

          {/* Side Panel (1/3 width on desktop) */}
          <div className="lg:col-span-1 space-y-4">
            {/* Slot Progress Card */}
            <div className="bg-white rounded-lg shadow p-4">
              <h3 className="text-lg font-semibold text-gray-800 mb-3">Complaint Details</h3>

              {/* Category Badge */}
              {categoryId && (
                <div className={`inline-block px-3 py-1 rounded-full text-sm font-medium mb-4 ${getCategoryColor(categoryId)}`}>
                  {getCategoryLabel(categoryId)}
                  {progress.percentage > 0 && (
                    <span className="ml-2 text-gray-500 text-xs">
                      ({progress.filled_count}/{progress.total_count} filled)
                    </span>
                  )}
                </div>
              )}

              {/* Progress Bar */}
              {progress.total_count > 0 && (
                <div className="mb-4">
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">Progress</span>
                    <span className="text-gray-800 font-medium">{progress.percentage}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${progress.percentage}%` }}
                    />
                  </div>
                </div>
              )}

              {/* Slot Checklist */}
              <div className="space-y-2">
                <h4 className="text-sm font-medium text-gray-600">Fill these details:</h4>
                {progress.checklist && progress.checklist.map((slot, idx) => (
                  <div key={idx} className={`flex items-start ${slot.filled ? 'opacity-60' : ''}`}>
                    {slot.filled ? (
                      <svg className="w-5 h-5 text-green-500 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    ) : (
                      <svg className="w-5 h-5 text-gray-300 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    )}
                    <span className="text-sm text-gray-700">{slot.label}</span>
                  </div>
                ))}
              </div>

              {/* Hidden phone number for submission */}
              <input
                type="text"
                value={phoneNumbers[0] || "9876543210"}
                onChange={(e) => setPhoneNumbers([e.target.value])}
                className="hidden"
              />
            </div>

            {/* Evidence Upload Card */}
            {!isComplete && (
              <EvidenceUpload onUpload={handleEvidenceUpload} />
            )}

            {/* Complaint Summary Card */}
            {isComplete && (
              <ComplaintSummary
                filledSlots={filledSlots}
                categoryId={categoryId}
                onSubmit={handleSubmitComplaint}
              />
            )}
          </div>
        </div>
      </main>

      <footer className="py-4 text-center text-gray-500 text-sm">
        <p>National Cybercrime Reporting Portal - Intelligent Assistant</p>
      </footer>
    </div>
  );
}

export default App;
