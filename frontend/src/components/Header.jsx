function Header() {
  return (
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
              <h1 className="text-xl font-bold tracking-wide">National Cybercrime Reporting Portal</h1>
              <p className="text-sm text-blue-200">Intelligent Complaint Filing Assistant</p>
            </div>
          </div>

          {/* Right side - Status/Info */}
          <div className="hidden md:flex items-center space-x-4 text-sm">
            <div className="flex items-center text-blue-200">
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>Available 24/7</span>
            </div>
            <div className="flex items-center text-blue-200">
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>Real-time Support</span>
            </div>
          </div>
        </div>

        {/* Mobile Status Bar */}
        <div className="md:hidden mt-3 text-xs text-blue-200 flex justify-between">
          <span>Available 24/7</span>
          <span>Real-time Support</span>
        </div>
      </div>
    </header>
  );
}

export default Header;
