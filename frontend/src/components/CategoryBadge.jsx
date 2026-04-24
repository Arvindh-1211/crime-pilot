const categoryColors = {
  'VISHING': 'bg-orange-500',
  'UPI_FRAUD': 'bg-red-500',
  'PHISHING': 'bg-yellow-500',
  'INVESTMENT_SCAM': 'bg-purple-500',
  'SEXTORTION': 'bg-red-700'
};

const categoryLabels = {
  'VISHING': 'Vishing',
  'UPI_FRAUD': 'UPI Fraud',
  'PHISHING': 'Phishing',
  'INVESTMENT_SCAM': 'Investment Scam',
  'SEXTORTION': 'Sextortion'
};

function CategoryBadge({ categoryId, confidence }) {
  if (!categoryId) return null;

  const color = categoryColors[categoryId] || 'bg-gray-500';
  const label = categoryLabels[categoryId] || categoryId;
  const confidenceText = confidence ? ` (${Math.round(confidence * 100)}%)` : '';

  return (
    <div className="inline-flex items-center px-3 py-1.5 rounded-full text-sm font-medium text-white bg-gradient-to-r from-blue-600 to-blue-700 shadow-sm">
      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
      <span>{label}{confidenceText}</span>
    </div>
  );
}

export default CategoryBadge;
