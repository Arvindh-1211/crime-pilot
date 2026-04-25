import { useState } from 'react';
import { checkComplaintStatus } from '../services/api';

function StatusTracker({ isOpen, onClose }) {
  const [trackingId, setTrackingId] = useState('');
  const [statusData, setStatusData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleCheckStatus = async (e) => {
    e.preventDefault();
    if (!trackingId.trim()) return;

    setIsLoading(true);
    setError(null);
    setStatusData(null);

    try {
      const data = await checkComplaintStatus(trackingId.trim());
      setStatusData(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Could not find a complaint with that Tracking ID.");
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'pending': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'accepted': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'transferred': return 'bg-purple-100 text-purple-800 border-purple-200';
      case 'resolved': return 'bg-green-100 text-green-800 border-green-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 backdrop-blur-sm p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in duration-200">
        
        {/* Header */}
        <div className="bg-indigo-600 px-6 py-4 flex justify-between items-center text-white">
          <h2 className="text-lg font-bold flex items-center gap-2">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
            </svg>
            Track Complaint Status
          </h2>
          <button onClick={onClose} className="text-indigo-200 hover:text-white transition-colors">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          <p className="text-sm text-gray-600 mb-4">
            Enter your Tracking ID below to see the current status of your cybercrime complaint. No login required.
          </p>
          
          <form onSubmit={handleCheckStatus} className="mb-6">
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="e.g. CY-2025-ABCD1234"
                value={trackingId}
                onChange={(e) => setTrackingId(e.target.value)}
                className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none uppercase tracking-wider font-mono text-sm"
              />
              <button
                type="submit"
                disabled={isLoading || !trackingId.trim()}
                className="bg-indigo-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors whitespace-nowrap"
              >
                {isLoading ? 'Checking...' : 'Check Status'}
              </button>
            </div>
          </form>

          {error && (
            <div className="p-3 bg-red-50 text-red-700 border border-red-200 rounded-lg text-sm mb-4">
              {error}
            </div>
          )}

          {statusData && (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-5 space-y-4">
              
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-xs text-gray-500 uppercase tracking-wider font-semibold mb-1">Tracking ID</p>
                  <p className="font-mono font-bold text-gray-900">{statusData.complaint_id}</p>
                </div>
                <div className={`px-3 py-1 text-xs font-bold uppercase tracking-wider rounded-full border ${getStatusColor(statusData.status)}`}>
                  {statusData.status}
                </div>
              </div>

              <div className="pt-3 border-t border-gray-200">
                <p className="text-xs text-gray-500 uppercase tracking-wider font-semibold mb-1">Assigned Station</p>
                <p className="font-medium text-gray-900 flex items-center gap-1.5">
                  <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  {statusData.assigned_station}
                </p>
              </div>

              {statusData.fir_number && (
                <div className="pt-3 border-t border-gray-200">
                  <p className="text-xs text-gray-500 uppercase tracking-wider font-semibold mb-1">FIR Number</p>
                  <p className="font-mono font-bold text-indigo-700 bg-indigo-50 inline-block px-2 py-0.5 rounded border border-indigo-100">
                    {statusData.fir_number}
                  </p>
                </div>
              )}

              <div className="pt-3 border-t border-gray-200 flex justify-between text-xs">
                <div>
                  <span className="text-gray-500 font-semibold uppercase tracking-wider">Severity:</span>
                  <span className="ml-1 text-gray-900 font-medium">{statusData.severity}</span>
                </div>
                <div className="text-gray-400">
                  Updated: {new Date(statusData.last_updated).toLocaleDateString()}
                </div>
              </div>

            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default StatusTracker;
