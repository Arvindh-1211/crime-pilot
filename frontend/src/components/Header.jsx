import { useState } from 'react';
import StatusTracker from './StatusTracker';

function Header() {
  const [isTrackerOpen, setIsTrackerOpen] = useState(false);

  return (
    <>
      <header className="bg-blue-900 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            {/* Left side - Logo and Title */}
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-blue-800 rounded-lg">
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.461 10.29 8 11.622 4.539-1.332 8-6.03 8-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <div>
                <h1 className="text-xl font-bold tracking-wide">CrimePilot</h1>
                <p className="text-sm text-blue-200">Intelligent Complaint Filing Assistant</p>
              </div>
            </div>

            {/* Right side - Status/Info + Buttons */}
            <div className="hidden md:flex items-center space-x-4 text-sm">
              <div className="flex items-center text-blue-200 mr-2">
                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>Available 24/7</span>
              </div>

              {/* Track Status Button */}
              <button
                onClick={() => setIsTrackerOpen(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-700 hover:bg-blue-600 text-white text-xs font-semibold rounded-lg transition-colors duration-200 border border-blue-500"
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                Track Status
              </button>

              {/* Officer Portal Button */}
              <a
                href="/officer"
                id="officer-portal-link"
                className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg transition-colors duration-200 border border-indigo-400"
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
                </svg>
                Officer Portal
              </a>
            </div>
          </div>

          {/* Mobile Status Bar */}
          <div className="md:hidden mt-3 flex justify-between items-center gap-2">
            <button
              onClick={() => setIsTrackerOpen(true)}
              className="px-2 py-1 bg-blue-700 text-white rounded text-xs font-semibold flex-1"
            >
              Track Status
            </button>
            <a href="/officer" className="px-2 py-1 bg-indigo-600 text-white rounded text-xs font-semibold flex-1 text-center">
              Officer Portal
            </a>
          </div>
        </div>
      </header>

      <StatusTracker isOpen={isTrackerOpen} onClose={() => setIsTrackerOpen(false)} />
    </>
  );
}

export default Header;
