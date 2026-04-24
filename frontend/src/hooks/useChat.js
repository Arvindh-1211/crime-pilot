import { useState, useCallback } from 'react';
import { sendMessage, submitComplaint, uploadEvidence } from '../services/api';

function useChat(initialPhone = '9876543210') {
  const [messages, setMessages] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [progress, setProgress] = useState({ filled_count: 0, total_count: 0, percentage: 0, checklist: [] });
  const [categoryId, setCategoryId] = useState(null);
  const [filledSlots, setFilledSlots] = useState({});
  const [isComplete, setIsComplete] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Initialize session
  const initializeSession = useCallback(async (phone) => {
    try {
      // Simulate API call - in real app would use startSession
      const mockSessionId = 'session-' + Math.random().toString(36).substr(2, 9);
      setSessionId(mockSessionId);
      setMessages([{ role: 'assistant', content: "Namaste! I'm your NCRP Cybercrime Assistant. I'll help you file a complaint for cyber incidents. What type of cybercrime did you experience?" }]);
    } catch (err) {
      setError("Failed to initialize session. Please refresh.");
    }
  }, []);

  // Send message
  const sendMessageToBot = useCallback(async (text) => {
    if (!sessionId || !text.trim()) return;

    setIsLoading(true);
    setError(null);

    // Add user message
    setMessages(prev => [...prev, { role: 'user', content: text }]);

    try {
      // In real app: const response = await sendMessage(sessionId, text);
      // Simulated response for demo
      const response = simulateBotResponse(sessionId, text);

      setCategoryId(response.category_id || null);
      setFilledSlots(response.filled_slots || {});
      setProgress(response.progress || { filled_count: 0, total_count: 0, percentage: 0, checklist: [] });
      setIsComplete(response.is_complete || false);

      setMessages(prev => [...prev, { role: 'assistant', content: response.bot_response }]);
    } catch (err) {
      setError("Failed to send message. Please try again.");
      setMessages(prev => [...prev, { role: 'assistant', content: "I encountered an error processing your message. Could you please rephrase?" }]);
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  // Submit complaint
  const submitComplaintHandler = useCallback(async () => {
    if (!sessionId) return;

    try {
      const response = await submitComplaint(sessionId, initialPhone);
      console.log("Complaint submitted:", response);
      setMessages(prev => [...prev, { role: 'assistant', content: `Thank you! Your complaint has been successfully submitted with ID: ${response.complaint_id}` }]);
      setIsComplete(true);
    } catch (err) {
      setError("Failed to submit complaint. Please try again.");
    }
  }, [sessionId, initialPhone]);

  // Upload evidence
  const uploadEvidenceHandler = useCallback(async (file) => {
    if (!sessionId || !file) return;

    try {
      const response = await uploadEvidence(sessionId, file);
      setMessages(prev => [...prev, { role: 'assistant', content: `Thank you! I've received your evidence file: ${file.name}` }]);
    } catch (err) {
      setError("Failed to upload evidence. Please try again.");
    }
  }, [sessionId]);

  // Clear chat
  const clearChat = useCallback(() => {
    setMessages([]);
    setCategoryId(null);
    setFilledSlots({});
    setProgress({ filled_count: 0, total_count: 0, percentage: 0, checklist: [] });
    setIsComplete(false);
  }, []);

  return {
    messages,
    sessionId,
    progress,
    categoryId,
    filledSlots,
    isComplete,
    isLoading,
    error,
    initializeSession,
    sendMessageToBot,
    submitComplaintHandler,
    uploadEvidenceHandler,
    clearChat
  };
}

// Simulated bot response function for demo purposes
function simulateBotResponse(sessionId, message) {
  const messageLower = message.toLowerCase();
  let botResponse = "";
  let category = null;
  let filledSlots = {};
  let progress = { filled_count: 0, total_count: 0, percentage: 0, checklist: [] };

  // Category detection
  if (messageLower.includes('upi') || messageLower.includes('transaction') || messageLower.includes('paytm') || messageLower.includes('google pay')) {
    category = 'UPI_FRAUD';
    filledSlots = { platform: 'Google Pay' };
    progress = { filled_count: 1, total_count: 5, percentage: 20, checklist: [] };
    botResponse = "I understand this involves a UPI transaction. Let me help you file a complaint for UPI Fraud. Could you please tell me when this incident occurred?";
  } else if (messageLower.includes('call') || messageLower.includes('phone') || messageLower.includes('missed') || messageLower.includes('voice')) {
    category = 'VISHING';
    filledSlots = { bank_name: 'SBI' };
    progress = { filled_count: 1, total_count: 4, percentage: 25, checklist: [] };
    botResponse = "I see this might be a vishing (voice phishing) case. Could you tell me when you received the suspicious call?";
  } else if (messageLower.includes('email') || messageLower.includes('website') || messageLower.includes('url') || messageLower.includes('link') || messageLower.includes('phishing')) {
    category = 'PHISHING';
    filledSlots = { phishing_url: 'https://fake-bank.com' };
    progress = { filled_count: 1, total_count: 3, percentage: 33, checklist: [] };
    botResponse = "This appears to be a phishing attempt. When did you visit the suspicious website?";
  } else if (messageLower.includes('investment') || messageLower.includes('stock') || messageLower.includes('crypto') || messageLower.includes('bitcoin') || messageLower.includes('scam')) {
    category = 'INVESTMENT_SCAM';
    filledSlots = { platform_name: 'Telegram' };
    progress = { filled_count: 1, total_count: 4, percentage: 25, checklist: [] };
    botResponse = "This sounds like an investment scam. Could you tell me when you started investing with them?";
  } else if (messageLower.includes('sextortion') || messageLower.includes('blackmail') || messageLower.includes('nude') || messageLower.includes('intimate')) {
    category = 'SEXTORTION';
    filledSlots = { platform_used: 'WhatsApp' };
    progress = { filled_count: 1, total_count: 3, percentage: 33, checklist: [] };
    botResponse = "I understand this is a serious case of sextortion. When did the blackmail start?";
  } else {
    category = 'VISHING';
    botResponse = "I'm ready to help you file your cybercrime complaint. Could you please describe what happened in detail?";
  }

  return {
    bot_response: botResponse,
    state: category ? 'FILLING_SLOTS' : 'COLLECTING_DESC',
    progress,
    category_id: category,
    filled_slots: filledSlots,
    is_complete: false
  };
}

export default useChat;
