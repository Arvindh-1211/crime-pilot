import React from 'react';

const ComplaintDossier = ({ content }) => {
  // Simple parser for the summary format
  const lines = content.split('\n');
  
  const extractValue = (pattern) => {
    const line = lines.find(l => l.includes(pattern));
    if (!line) return '';
    return line.split('**: ')[1] || line.split('** : ')[1] || '';
  };

  const type = extractValue('**Complaint Type**');
  const severity = extractValue('**Severity Rating**');
  const description = extractValue('**Your Description**');
  
  // Extract bullet points (Details collected)
  const detailLines = lines.filter(l => l.startsWith('• **'));
  const details = detailLines.map(l => {
    const parts = l.replace('• **', '').split('**: ');
    return { label: parts[0], value: parts[1] };
  });

  const getSeverityColor = (sev) => {
    if (sev.includes('Critical') || sev.includes('🔴')) return 'text-red-600 bg-red-50 border-red-200';
    if (sev.includes('High') || sev.includes('🟠')) return 'text-orange-600 bg-orange-50 border-orange-200';
    if (sev.includes('Medium') || sev.includes('🟡')) return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    return 'text-green-600 bg-green-50 border-green-200';
  };

  return (
    <div className="my-4 bg-white border border-gray-200 rounded-xl shadow-lg overflow-hidden transition-all hover:shadow-xl">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-700 to-indigo-800 px-5 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="bg-white/20 p-2 rounded-lg backdrop-blur-sm">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h3 className="text-white font-bold tracking-tight">Incident Case Review</h3>
        </div>
        <span className="text-xs font-medium text-blue-100 uppercase tracking-widest opacity-80">Draft Report</span>
      </div>

      <div className="p-5 space-y-6">
        {/* Core Info */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-1">
            <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Classification</span>
            <div className="text-sm font-semibold text-gray-800 flex items-center">
              <span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
              {type || 'Unknown'}
            </div>
          </div>
          <div className="space-y-1">
            <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Priority Level</span>
            <div>
              <span className={`text-xs px-2 py-1 rounded-full border ${getSeverityColor(severity)}`}>
                {severity || 'Pending'}
              </span>
            </div>
          </div>
        </div>

        {/* Narrative Section */}
        <div className="bg-gray-50 rounded-lg p-4 border border-gray-100 relative">
          <span className="absolute -top-2 left-3 bg-white px-2 text-[9px] font-bold text-gray-400 uppercase tracking-tight">Incident Narrative</span>
          <p className="text-sm text-gray-700 italic leading-relaxed">
            "{description}"
          </p>
        </div>

        {/* Collected Details Grid */}
        {details.length > 0 && (
          <div className="space-y-3">
             <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Evidence & Metadata</span>
             <div className="grid grid-cols-1 gap-2">
                {details.map((detail, i) => (
                  <div key={i} className="flex items-center justify-between py-2 px-3 bg-white border border-gray-100 rounded-lg shadow-sm hover:border-blue-100 transition-colors">
                    <span className="text-xs font-medium text-gray-500">{detail.label}</span>
                    <span className="text-xs font-bold text-gray-800">{detail.value}</span>
                  </div>
                ))}
             </div>
          </div>
        )}
      </div>

      {/* Footer Info */}
      <div className="bg-blue-50/50 px-5 py-3 border-t border-gray-100">
        <p className="text-[11px] text-blue-600 flex items-center">
          <svg className="w-3 h-3 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Review carefully before final submission to NCRP.
        </p>
      </div>
    </div>
  );
};

export default ComplaintDossier;
