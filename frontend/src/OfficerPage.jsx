import { useState, useEffect } from 'react';
import OfficerLogin from './components/OfficerLogin';
import OfficerDashboard from './components/officer/OfficerDashboard';

function OfficerPage() {
  const [officer, setOfficer] = useState(null);

  useEffect(() => {
    const token = sessionStorage.getItem('officer_token');
    if (token) {
      setOfficer({
        token,
        name:     sessionStorage.getItem('officer_name')     || 'Officer',
        badge:    sessionStorage.getItem('officer_badge')    || '',
        station:  sessionStorage.getItem('officer_station')  || '',
        role:     sessionStorage.getItem('officer_role')     || 'OFFICER',
        username: sessionStorage.getItem('officer_username') || '',
      });
    }
  }, []);

  const handleLoginSuccess = (data) => {
    sessionStorage.setItem('officer_token',    data.token);
    sessionStorage.setItem('officer_name',     data.name);
    sessionStorage.setItem('officer_badge',    data.badge);
    sessionStorage.setItem('officer_station',  data.station);
    sessionStorage.setItem('officer_role',     data.role);
    sessionStorage.setItem('officer_username', data.username || '');
    setOfficer(data);
  };

  const handleLogout = () => {
    ['officer_token','officer_name','officer_badge','officer_station','officer_role','officer_username']
      .forEach(k => sessionStorage.removeItem(k));
    setOfficer(null);
  };

  if (!officer) return <OfficerLogin onLoginSuccess={handleLoginSuccess} />;
  return <OfficerDashboard officer={officer} onLogout={handleLogout} />;
}

export default OfficerPage;
