import { useState, useCallback } from 'react';

function ComplaintSummary({ filledSlots, categoryId, onSubmit }) {
  const [copied, setCopied] = useState(false);

  // Category colors for severity
  const categoryColors = {
    'UPI_FRAUD': 'bg-red-100 text-red-800',
    'VISHING': 'bg-orange-100 text-orange-800',
    'PHISHING': 'bg-yellow-100 text-yellow-800',
    'INVESTMENT_SCAM': 'bg-purple-100 text-purple-800',
    'SEXTORTION': 'bg-red-900 text-red-100'
  };

  const severityColors = {
    red: 'bg-red-100 text-red-800 border-red-200',
    orange: 'bg-orange-100 text-orange-800 border-orange-200',
    green: 'bg-green-100 text-green-800 border-green-200'
  };

  const categoryLabels = {
    'UPI_FRAUD': 'UPI Fraud',
    'VISHING': 'Vishing',
    'PHISHING': 'Phishing',
    'INVESTMENT_SCAM': 'Investment Scam',
    'SEXTORTION': 'Sextortion'
  };

  // Format slot value
  const formatValue = (key, value) => {
    if (value === 'true') return 'Yes';
    if (value === 'false') return 'No';
    if (key === 'incident_date') return new Date(value).toLocaleDateString();
    return value;
  };

  const handleCopy = useCallback(() => {
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, []);

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="text-lg font-semibold text-gray-800 mb-3">Complaint Summary</h3>

      {/* Category Badge */}
      {categoryId && (
        <div className={`inline-block px-3 py-1 rounded-full text-sm font-medium mb-4 ${categoryColors[categoryId] || categoryColors.VISHING}`}>
          {categoryLabels[categoryId] || categoryId}
        </div>
      )}

      {/* Filled Slots */}
      <div className="space-y-2 mb-4 max-h-60 overflow-y-auto pr-2">
        {Object.entries(filledSlots).length > 0 ? (
          Object.entries(filledSlots).map(([key, value]) => (
            <div key={key} className="flex justify-between text-sm py-2 border-b border-gray-100">
              <span className="text-gray-600">{key.replace(/_/g, ' ')}</span>
              <span className="text-gray-800 font-medium text-right max-w-[60%] truncate">
                {formatValue(key, value)}
              </span>
            </div>
          ))
        ) : (
          <p className="text-sm text-gray-500 italic">No details filled yet</p>
        )}
      </div>

      {/* Severity Score (simulated for display) */}
      <div className="mb-4 p-3 bg-gray-50 rounded">
        <div className="flex justify-between items-center">
          <span className="text-sm font-medium text-gray-600">Severity Score</span>
          <span className="text-lg font-bold text-blue-600">6.8</span>
        </div>
        <div className="mt-1 text-xs text-gray-500">
          Higher scores indicate more severe cases
        </div>
      </div>

      {/* Submit Button */}
      <div className="mb-3">
        <button
          onClick={onSubmit}
          className="w-full py-2 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors font-medium"
        >
          Submit Complaint
        </button>
        <p className="text-xs text-gray-400 mt-2 text-center">
          After submission, your complaint will be reviewed by NCRP authorities
        </p>
      </div>

      {/* Complaint ID Display (shown after submit) */}
      <div className="mt-3 p-3 bg-green-50 rounded border border-green-100 hidden">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs text-green-600 font-medium uppercase">Complaint Submitted</p>
            <p className="text-sm font-bold text-gray-800">CY-2025-ABCD1234</p>
          </div>
          <button
            onClick={handleCopy}
            className="text-blue-600 hover:text-blue-800"
          >
            {copied ? 'Copied!' : 'Copy'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ComplaintSummary;
