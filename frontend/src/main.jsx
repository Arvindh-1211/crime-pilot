import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import App from './App';
import OfficerPage from './OfficerPage';
import PortalLanding from './PortalLanding';
import ComplaintTracker from './components/ComplaintTracker';
import './styles/index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        {/* Landing Portal */}
        <Route path="/" element={<PortalLanding />} />
        {/* User‑facing chatbot */}
        <Route path="/chat/*" element={<App />} />
        {/* Officer login + dashboard */}
        <Route path="/officer/*" element={<OfficerPage />} />
        {/* Complaint tracker */}
        <Route path="/track/:complaintId" element={<ComplaintTracker />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
