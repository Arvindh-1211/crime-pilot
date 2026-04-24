import axios from 'axios';

// Create axios instance with base URL
const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json'
  }
});

/**
 * Start a new chat session
 * @param {string} phoneNumber - User's phone number
 * @returns {Promise<{session_id: string, welcome_message: string}>}
 */
export const startSession = async (phoneNumber) => {
  const response = await api.post('/chat/start', { phone_number: phoneNumber });
  return response.data;
};

/**
 * Send a message to the chatbot
 * @param {string} sessionId - Session ID from startSession
 * @param {string} message - User's message
 * @returns {Promise<{bot_response: string, state: string, progress: Object, category_id: string|null, filled_slots: Object, is_complete: boolean}>}
 */
export const sendMessage = async (sessionId, message) => {
  const response = await api.post('/chat/message', { session_id: sessionId, message });
  return response.data;
};

/**
 * Submit the completed complaint
 * @param {string} sessionId - Session ID
 * @param {Object} formData - Contact details from the frontend form
 * @returns {Promise<{complaint_id, complaint_json, severity_score, tracking_url, email_preview}>}
 */
export const submitComplaint = async (sessionId, formData) => {
  const response = await api.post('/complaint/submit', {
    session_id: sessionId,
    phone_number: formData.phone || '',
    email: formData.email || '',
    name: formData.name || '',
    incident_datetime: formData.incident_datetime || '',
    location: formData.location || ''
  });
  return response.data;
};


/**
 * Upload evidence file
 * @param {string} sessionId - Session ID
 * @param {File} file - File to upload
 * @returns {Promise<{file_id: string, file_name: string, file_type: string}>}
 */
export const uploadEvidence = async (sessionId, file) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('session_id', sessionId);

  const response = await api.post('/upload/evidence', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });
  return response.data;
};

/**
 * Get complaint details by ID
 * @param {string} complaintId - Complaint ID
 * @returns {Promise<{complaint_id: string, complaint_json: Object, severity_score: number}>}
 */
export const getComplaint = async (complaintId) => {
  const response = await api.get(`/complaint/${complaintId}`);
  return response.data;
};

/**
 * List all complaints (admin/debug endpoint)
 * @returns {Promise<{complaints: Array, total: number}>}
 */
export const listComplaints = async () => {
  const response = await api.get('/complaints');
  return response.data;
};

// ── Officer Dashboard API ────────────────────────────────────────────────────

/**
 * Authenticate an officer
 * @param {string} username
 * @param {string} password
 * @returns {Promise<{token: string, role: string, name: string, badge: string, station: string}>}
 */
export const officerLogin = async (username, password) => {
  const response = await api.post('/officer/login', { username, password });
  return response.data;
};

/**
 * Fetch all complaints with tracking metrics (officer dashboard)
 * @returns {Promise<{complaints: Array, metrics: Object}>}
 */
export const officerGetComplaints = async () => {
  const response = await api.get('/officer/complaints');
  return response.data;
};

/**
 * Get single complaint detail
 * @param {string} complaintId
 */
export const officerGetComplaintDetail = async (complaintId) => {
  const response = await api.get(`/officer/complaints/${complaintId}`);
  return response.data;
};

/**
 * Update complaint status (accepted / rejected / transferred)
 * @param {string} complaintId
 * @param {string} status
 */
export const officerUpdateStatus = async (complaintId, status) => {
  const response = await api.put(`/officer/complaints/${complaintId}/status`, { status });
  return response.data;
};

/**
 * Assign an FIR number to a complaint
 * @param {string} complaintId
 * @param {string} firNumber
 */
export const officerAssignFir = async (complaintId, firNumber) => {
  const response = await api.put(`/officer/complaints/${complaintId}/fir`, { fir_number: firNumber });
  return response.data;
};

/**
 * Transfer complaint to another station
 * @param {string} complaintId
 * @param {string} targetStation
 */
export const officerTransferComplaint = async (complaintId, targetStation) => {
  const response = await api.put(`/officer/complaints/${complaintId}/transfer`, { target_station: targetStation });
  return response.data;
};

// Export axios instance for custom requests
export { api };
