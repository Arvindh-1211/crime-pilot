function SlotProgress({ progress, categoryId }) {
  const categoryLabels = {
    'UPI_FRAUD': 'UPI Fraud',
    'VISHING': 'Vishing',
    'PHISHING': 'Phishing',
    'INVESTMENT_SCAM': 'Investment Scam',
    'SEXTORTION': 'Sextortion'
  };

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="text-lg font-semibold text-gray-800 mb-3">Complaint Details</h3>

      {/* Category Badge */}
      {categoryId && (
        <div className="inline-block px-3 py-1 rounded-full text-sm font-medium mb-4 bg-blue-100 text-blue-800">
          {categoryLabels[categoryId] || categoryId}
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
          <p className="text-xs text-gray-500 mt-1">
            {progress.filled_count} of {progress.total_count} fields filled
          </p>
        </div>
      )}

      {/* Slot Checklist */}
      <div className="space-y-2 max-h-48 overflow-y-auto pr-2">
        <h4 className="text-sm font-medium text-gray-600">Remaining Details:</h4>
        {progress.checklist && progress.checklist.length > 0 ? (
          progress.checklist.map((slot, idx) => (
            <div key={idx} className="flex items-start">
              {slot.filled ? (
                <svg className="w-4 h-4 text-green-500 mr-2 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              ) : (
                <svg className="w-4 h-4 text-gray-300 mr-2 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
              )}
              <span className="text-sm text-gray-700">{slot.label}</span>
            </div>
          ))
        ) : (
          <p className="text-sm text-gray-500 italic">Select a category to see details</p>
        )}
      </div>
    </div>
  );
}

export default SlotProgress;
