import { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import ChatWindow from './components/ChatWindow';
import EvidenceUpload from './components/EvidenceUpload';
import ComplaintSummary from './components/ComplaintSummary';
import ContactForm from './components/ContactForm';
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
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [submissionResult, setSubmissionResult] = useState(null);
  
  // State for the Contact Form on the right panel
  const [contactFormData, setContactFormData] = useState({
    name: '',
    phone: '',
    email: '',
    incident_datetime: '',
    location: ''
  });

  // Initialize session on mount
  useEffect(() => {
    const initSession = async () => {
      try {
        const mockPhone = "9876543210";
        const response = await startSession(mockPhone);
        setSessionId(response.session_id);
        setMessages([{ role: 'assistant', content: response.welcome_message }]);
      } catch (err) {
        setError("Failed to initialize session. Please refresh the page.");
        setMessages([{ role: 'assistant', content: "Hello! I'm your NCRP Cybercrime Assistant. Please describe what happened to you." }]);
      }
    };
    initSession();
  }, []);

  // Handle sending a message
  const handleSendMessage = useCallback(async (text) => {
    if (!sessionId || !text.trim()) return;

    setIsLoading(true);
    setError(null);

    const userMessage = { role: 'user', content: text };
    setMessages(prev => [...prev, userMessage]);

    try {
      const response = await sendMessage(sessionId, text);

      setCategoryId(response.category_id || null);
      setFilledSlots(response.filled_slots || {});
      setProgress(response.progress || { filled_count: 0, total_count: 0, percentage: 0, checklist: [] });

      const botMessage = { role: 'assistant', content: response.bot_response };
      setMessages(prev => [...prev, botMessage]);

      if (response.is_complete) {
        setIsComplete(true);
      }

      // If the bot auto-submitted (user said Yes in chat), capture the result
      if (response.complaint_id && response.email_preview) {
        const result = {
          complaint_id:    response.complaint_id,
          tracking_url:    response.tracking_url || `/track/${response.complaint_id}`,
          email_preview:   response.email_preview,
          severity_score:  null,
          assigned_station: null,
        };
        setSubmissionResult(result);
        // Also persist to localStorage
        const complaintData = {
          complaint_id:  response.complaint_id,
          tracking_url:  result.tracking_url,
          email_preview: result.email_preview,
          filled_slots:  response.filled_slots || {},
          saved_at:      new Date().toISOString(),
        };
        localStorage.setItem(`complaint_${response.complaint_id}`, JSON.stringify(complaintData));
        const existingIds = JSON.parse(localStorage.getItem('ncrp_complaint_ids') || '[]');
        existingIds.unshift(response.complaint_id);
        localStorage.setItem('ncrp_complaint_ids', JSON.stringify(existingIds));
      }
    } catch (err) {
      setError("Failed to send message. Please try again.");
      setMessages(prev => [...prev, { role: 'assistant', content: "I encountered an error. Could you please try again?" }]);
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  // Handle submitting complaint — calls API, stores in localStorage, shows result
  const handleSubmitComplaint = useCallback(async () => {
    if (!sessionId) return;

    if (!contactFormData.name || !contactFormData.phone) {
      setError("Please fill out your Name and Phone Number in the Complainant Details form before submitting.");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const response = await submitComplaint(sessionId, contactFormData);

      // Save to localStorage to simulate a database
      const complaintData = {
        ...response.complaint_json,
        complaint_id: response.complaint_id,
        severity_score: response.severity_score,
        tracking_url: response.tracking_url,
        email_preview: response.email_preview,
        saved_at: new Date().toISOString(),
      };
      localStorage.setItem(`complaint_${response.complaint_id}`, JSON.stringify(complaintData));

      // Also keep a list of all complaint IDs
      const existingIds = JSON.parse(localStorage.getItem('ncrp_complaint_ids') || '[]');
      existingIds.unshift(response.complaint_id);
      localStorage.setItem('ncrp_complaint_ids', JSON.stringify(existingIds));

      setSubmissionResult({
        complaint_id: response.complaint_id,
        tracking_url: response.tracking_url || `/track/${response.complaint_id}`,
        email_preview: response.email_preview,
        severity_score: response.severity_score,
        assigned_station: response.assigned_station,
      });

      // Add success message to chat
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `✅ Your complaint has been registered with ID: **${response.complaint_id}**. Check the panel on the right for your tracking link and email acknowledgement.`
      }]);
    } catch (err) {
      console.error('Submit error:', err);
      setError("Failed to submit complaint. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }, [sessionId, contactFormData]);

  // Handle evidence upload
  const handleEvidenceUpload = useCallback(async (file) => {
    if (!sessionId || !file) return;
    try {
      await uploadEvidence(sessionId, file);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Thank you! I've received your evidence file: ${file.name}`
      }]);
    } catch (err) {
      setError("Failed to upload evidence. Please try again.");
    }
  }, [sessionId]);

  const getCategoryColor = (catId) => {
    const colors = {
      'UPI_FRAUD': 'bg-red-100 text-red-800',
      'VISHING': 'bg-orange-100 text-orange-800',
      'PHISHING': 'bg-yellow-100 text-yellow-800',
      'INVESTMENT_SCAM': 'bg-purple-100 text-purple-800',
      'SEXTORTION': 'bg-red-900 text-red-100',
      'JOB_FRAUD': 'bg-yellow-100 text-yellow-900',
      'OTP_SIM_SWAP': 'bg-blue-100 text-blue-800',
      'SOCIAL_MEDIA_FRAUD': 'bg-pink-100 text-pink-800',
      'LOTTERY_SCAM': 'bg-green-100 text-green-800',
      'ONLINE_SHOPPING_FRAUD': 'bg-indigo-100 text-indigo-800',
      'IDENTITY_THEFT': 'bg-gray-200 text-gray-900',
    };
    return colors[catId] || 'bg-gray-100 text-gray-800';
  };

  const getCategoryLabel = (catId) => {
    const labels = {
      'UPI_FRAUD': 'UPI / Bank Fraud',
      'VISHING': 'Vishing (Fake Call)',
      'PHISHING': 'Phishing',
      'INVESTMENT_SCAM': 'Investment Scam',
      'SEXTORTION': 'Sextortion',
      'JOB_FRAUD': 'Job / Task Fraud',
      'OTP_SIM_SWAP': 'OTP / SIM Swap',
      'SOCIAL_MEDIA_FRAUD': 'Social Media / Romance Scam',
      'LOTTERY_SCAM': 'Lottery / Prize Scam',
      'ONLINE_SHOPPING_FRAUD': 'Online Shopping Fraud',
      'IDENTITY_THEFT': 'Identity Theft',
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
          {/* Chat Window */}
          <div className="lg:col-span-2 h-[600px] flex flex-col">
            <ChatWindow
              messages={messages}
              onSendMessage={handleSendMessage}
              isLoading={isLoading}
            />
          </div>

          {/* Side Panel */}
          <div className="lg:col-span-1 space-y-4 overflow-y-auto max-h-[600px] pr-2">
            
            {/* Category Indicator */}
            {categoryId && (
              <div className={`w-full px-4 py-3 rounded-lg flex items-center justify-between border ${getCategoryColor(categoryId).replace('bg-', 'border-').replace('100', '200')} ${getCategoryColor(categoryId)}`}>
                <div>
                  <p className="text-xs uppercase tracking-wider opacity-70 font-bold mb-0.5">Detected Category</p>
                  <p className="text-sm font-semibold">{getCategoryLabel(categoryId)}</p>
                </div>
                <div className="text-2xl opacity-80">
                  {categoryId === 'UPI_FRAUD' ? '💸' : categoryId === 'PHISHING' ? '🎣' : '🚨'}
                </div>
              </div>
            )}

            {/* Contact Form */}
            <ContactForm 
              formData={contactFormData} 
              setFormData={setContactFormData} 
              isComplete={isComplete || !!submissionResult} 
            />

            {/* Evidence Upload */}
            {!isComplete && !submissionResult && (
              <EvidenceUpload onUpload={handleEvidenceUpload} />
            )}

            {/* Complaint Summary + Submit */}
            {isComplete && (
              <ComplaintSummary
                filledSlots={{...contactFormData, ...filledSlots}}
                categoryId={categoryId}
                onSubmit={handleSubmitComplaint}
                isSubmitting={isSubmitting}
                submissionResult={submissionResult}
              />
            )}
          </div>
        </div>
      </main>

      <footer className="py-4 text-center text-gray-500 text-sm">
        <p>National Cybercrime Reporting Portal — Intelligent Assistant</p>
      </footer>
    </div>
  );
}

export default App;
