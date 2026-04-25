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
 * Refine transcribed speech text via LLM
 * @param {string} text - Raw transcribed speech
 * @returns {Promise<{refined_text: string}>}
 */
export const refineSpeech = async (text) => {
  const response = await api.post('/chat/refine', { text });
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
 * Public endpoint to track complaint status by Tracking ID
 * @param {string} trackingId - Tracking ID
 * @returns {Promise<{complaint_id: string, status: string, assigned_station: string, date_filed: string, fir_number: string, last_updated: string, severity: string}>}
 */
export const checkComplaintStatus = async (trackingId) => {
  const response = await api.get(`/complaint/${trackingId}/status`);
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

const getOfficerToken = () => sessionStorage.getItem('officer_token');

const officerApi = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

officerApi.interceptors.request.use((config) => {
  const token = getOfficerToken();
  if (token) config.headers['Authorization'] = `Bearer ${token}`;
  return config;
});

export const officerLogin = async (username, password) => {
  const response = await api.post('/officer/login', { username, password });
  return response.data;
};

export const officerGetComplaints = async () => {
  const response = await officerApi.get('/officer/complaints');
  return response.data;
};

export const officerGetComplaintDetail = async (complaintId) => {
  const response = await officerApi.get(`/officer/complaints/${complaintId}`);
  return response.data;
};

export const officerAccept = async (complaintId) => {
  const response = await officerApi.put(`/officer/complaints/${complaintId}/accept`);
  return response.data;
};

export const officerReject = async (complaintId, reason) => {
  const response = await officerApi.put(`/officer/complaints/${complaintId}/reject`, { reason });
  return response.data;
};

export const officerAssignFir = async (complaintId, firNumber) => {
  const response = await officerApi.put(`/officer/complaints/${complaintId}/fir`, { fir_number: firNumber });
  return response.data;
};

export const officerTransferComplaint = async (complaintId, targetStation, notes = '') => {
  const response = await officerApi.put(`/officer/complaints/${complaintId}/transfer`, { target_station: targetStation, notes });
  return response.data;
};

export const officerUpdateStatus = async (complaintId, status, extra = {}) => {
  const response = await officerApi.put(`/officer/complaints/${complaintId}/status`, { status, ...extra });
  return response.data;
};

export const officerGetAdminMetrics = async () => {
  const response = await officerApi.get('/officer/admin/metrics');
  return response.data;
};

export const officerGetAuditLog = async (complaintId) => {
  const url = complaintId ? `/officer/audit/${complaintId}` : '/officer/audit';
  const response = await officerApi.get(url);
  return response.data;
};

// Export axios instance for custom requests
export { api };
