import { useState, useCallback } from 'react';

function EvidenceUpload({ onUpload }) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState(null);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);

    const file = e.dataTransfer.files[0];
    if (file) {
      validateAndUpload(file);
    }
  }, []);

  const handleFileSelect = useCallback((e) => {
    const file = e.target.files[0];
    if (file) {
      validateAndUpload(file);
    }
  }, []);

  const validateAndUpload = useCallback((file) => {
    // Validate file type
    const allowedTypes = ['image/jpeg', 'image/png', 'application/pdf'];
    if (!allowedTypes.includes(file.type)) {
      setUploadStatus({ error: 'Invalid file type. Please upload JPG, PNG, or PDF only.' });
      setTimeout(() => setUploadStatus(null), 3000);
      return;
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      setUploadStatus({ error: 'File too large. Maximum size is 10MB.' });
      setTimeout(() => setUploadStatus(null), 3000);
      return;
    }

    // Upload
    setUploadStatus({ loading: true });
    onUpload(file);

    // Simulate upload delay
    setTimeout(() => {
      setUploadedFile(file);
      setUploadStatus({ success: true });
      setTimeout(() => {
        setUploadStatus(null);
        setUploadedFile(null);
      }, 3000);
    }, 1000);
  }, [onUpload]);

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="text-lg font-semibold text-gray-800 mb-3">Upload Evidence</h3>

      {/* Drag and Drop Zone */}
      <div
        className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
          isDragging
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          type="file"
          id="file-upload"
          className="hidden"
          accept="image/jpeg,image/png,application/pdf"
          onChange={handleFileSelect}
        />
        <label htmlFor="file-upload" className="cursor-pointer">
          <div className="flex flex-col items-center">
            <svg className="w-12 h-12 text-gray-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <p className="text-sm text-gray-600">Drag and drop files here, or click to select</p>
            <p className="text-xs text-gray-400 mt-1">JPG, PNG, or PDF (max 10MB)</p>
          </div>
        </label>
      </div>

      {/* Status Messages */}
      {uploadStatus && (
        <div className={`mt-3 p-2 rounded text-sm ${
          uploadStatus.error ? 'bg-red-100 text-red-700' :
          uploadStatus.success ? 'bg-green-100 text-green-700' :
          uploadStatus.loading ? 'bg-blue-100 text-blue-700' : ''
        }`}>
          {uploadStatus.error}
          {uploadStatus.success && 'File uploaded successfully!'}
          {uploadStatus.loading && 'Uploading...'}
        </div>
      )}

      {/* Uploaded File Info */}
      {uploadedFile && (
        <div className="mt-3 p-3 bg-green-50 rounded">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="text-sm text-gray-800">{uploadedFile.name}</span>
            </div>
            <span className="text-xs text-gray-500">{(uploadedFile.size / 1024).toFixed(1)} KB</span>
          </div>
        </div>
      )}

      {/* File Type Legend */}
      <div className="mt-4 pt-3 border-t border-gray-200">
        <h4 className="text-xs font-medium text-gray-500 mb-2">Accepted File Types:</h4>
        <div className="flex flex-wrap gap-2">
          <span className="inline-flex items-center px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded">
            📷 JPG Images
          </span>
          <span className="inline-flex items-center px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded">
            📷 PNG Images
          </span>
          <span className="inline-flex items-center px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded">
            📄 PDF Documents
          </span>
        </div>
      </div>
    </div>
  );
}

export default EvidenceUpload;
