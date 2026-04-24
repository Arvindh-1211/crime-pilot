import { useState, useEffect } from 'react';
import OfficerLogin from './components/OfficerLogin';
import OfficerDashboard from './components/OfficerDashboard';

/**
 * Manages officer authentication state.
 * Shows OfficerLogin when unauthenticated, OfficerDashboard when logged in.
 */
function OfficerPage() {
  const [officer, setOfficer] = useState(null);

  // Restore session from sessionStorage
  useEffect(() => {
    const token = sessionStorage.getItem('officer_token');
    if (token) {
      setOfficer({
        token,
        name: sessionStorage.getItem('officer_name') || 'Officer',
        badge: sessionStorage.getItem('officer_badge') || '',
        station: sessionStorage.getItem('officer_station') || '',
      });
    }
  }, []);

  const handleLoginSuccess = (data) => {
    setOfficer(data);
  };

  const handleLogout = () => {
    sessionStorage.removeItem('officer_token');
    sessionStorage.removeItem('officer_name');
    sessionStorage.removeItem('officer_badge');
    sessionStorage.removeItem('officer_station');
    setOfficer(null);
  };

  if (!officer) {
    return <OfficerLogin onLoginSuccess={handleLoginSuccess} />;
  }

  return <OfficerDashboard officer={officer} onLogout={handleLogout} />;
}

export default OfficerPage;
