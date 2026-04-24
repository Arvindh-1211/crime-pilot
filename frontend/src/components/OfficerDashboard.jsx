import { useState, useEffect, useCallback } from 'react';
import {
  officerGetComplaints,
  officerUpdateStatus,
  officerAssignFir,
  officerTransferComplaint,
} from '../services/api';

// ── Constants ────────────────────────────────────────────────────────────────

const STATUS_CONFIG = {
  pending:     { label: 'Pending',     color: '#f59e0b', bg: 'rgba(245,158,11,.12)' },
  accepted:    { label: 'Accepted',    color: '#10b981', bg: 'rgba(16,185,129,.12)' },
  rejected:    { label: 'Rejected',    color: '#ef4444', bg: 'rgba(239,68,68,.12)' },
  transferred: { label: 'Transferred', color: '#6366f1', bg: 'rgba(99,102,241,.12)' },
};

const STATIONS = [
  'Mumbai Cyber Crime Police Station',
  'Delhi Cyber Crime Unit – Dwarka',
  'Bengaluru CID Cyber Crime Division',
  'Chennai Cyber Crime Cell – Egmore',
  'Hyderabad Cyber Crime Police Station',
  'Kolkata Cyber Crime Police Station – Lalbazar',
  'Gujarat CID Cyber Crime Cell',
  'Pune Cyber Crime Cell',
  'UP Cyber Crime Cell – Lucknow',
  'Rajasthan Cyber Crime Cell – Jaipur',
  'Central Cyber Crime Coordination Centre (I4C)',
];

// ── Helper components ────────────────────────────────────────────────────────

function MetricCard({ label, value, icon, color }) {
  return (
    <div className="metric-card" style={{ '--accent': color }}>
      <div className="metric-icon" dangerouslySetInnerHTML={{ __html: icon }} />
      <div className="metric-body">
        <span className="metric-value">{value}</span>
        <span className="metric-label">{label}</span>
      </div>
    </div>
  );
}

function StatusBadge({ status }) {
  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.pending;
  return (
    <span className="status-badge" style={{ color: cfg.color, background: cfg.bg }}>
      <span className="status-dot" style={{ background: cfg.color }} />
      {cfg.label}
    </span>
  );
}

// ── FIR Modal ────────────────────────────────────────────────────────────────

function FirModal({ complaint, onClose, onAssign }) {
  const [firNumber, setFirNumber] = useState('');
  const [loading, setLoading] = useState(false);

  const handleAssign = async () => {
    if (!firNumber.trim()) return;
    setLoading(true);
    await onAssign(complaint.complaint_id, firNumber.trim());
    setLoading(false);
    onClose();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <h3 className="modal-title">Assign FIR Number</h3>
        <p className="modal-subtitle">
          Complaint <strong>{complaint.complaint_id}</strong> will be linked to this FIR.
          The ticket will remain open — it will <em>not</em> be closed.
        </p>

        <div className="modal-field">
          <label htmlFor="fir-input">FIR Number</label>
          <input
            id="fir-input"
            type="text"
            placeholder="e.g. FIR-2025-MH-04821"
            value={firNumber}
            onChange={(e) => setFirNumber(e.target.value)}
            autoFocus
          />
        </div>

        <div className="modal-actions">
          <button className="btn-ghost" onClick={onClose}>Cancel</button>
          <button className="btn-primary" disabled={!firNumber.trim() || loading} onClick={handleAssign}>
            {loading ? 'Assigning…' : 'Assign FIR'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Transfer Modal ───────────────────────────────────────────────────────────

function TransferModal({ complaint, onClose, onTransfer }) {
  const [station, setStation] = useState('');
  const [loading, setLoading] = useState(false);

  const handleTransfer = async () => {
    if (!station) return;
    setLoading(true);
    await onTransfer(complaint.complaint_id, station);
    setLoading(false);
    onClose();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <h3 className="modal-title">Transfer Complaint</h3>
        <p className="modal-subtitle">
          Transfer <strong>{complaint.complaint_id}</strong> to another jurisdiction.
        </p>

        <div className="modal-field">
          <label htmlFor="station-select">Target Station</label>
          <select id="station-select" value={station} onChange={(e) => setStation(e.target.value)}>
            <option value="">Select a station…</option>
            {STATIONS.filter(s => s !== complaint.assigned_station).map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>

        <div className="modal-actions">
          <button className="btn-ghost" onClick={onClose}>Cancel</button>
          <button className="btn-primary" disabled={!station || loading} onClick={handleTransfer}>
            {loading ? 'Transferring…' : 'Transfer'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Complaint Detail Drawer ──────────────────────────────────────────────────

function ComplaintDrawer({ complaint, onClose }) {
  if (!complaint) return null;

  const fields = complaint.fields || {};

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <div className="drawer" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-header">
          <div>
            <h3>{complaint.complaint_id}</h3>
            <p className="drawer-category">{complaint.complaint_category_label || 'Unknown Category'}</p>
          </div>
          <button className="drawer-close" onClick={onClose} aria-label="Close">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="w-6 h-6">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="drawer-body">
          {/* Status row */}
          <div className="drawer-row">
            <span className="drawer-label">Status</span>
            <StatusBadge status={complaint.status} />
          </div>
          <div className="drawer-row">
            <span className="drawer-label">NCRP Number</span>
            <span className="drawer-value mono">{complaint.ncrp_number || complaint.complaint_id}</span>
          </div>
          {complaint.fir_number && (
            <div className="drawer-row">
              <span className="drawer-label">FIR Number</span>
              <span className="drawer-value mono">{complaint.fir_number}</span>
            </div>
          )}
          <div className="drawer-row">
            <span className="drawer-label">Severity</span>
            <span className={`drawer-value severity-${complaint.severity_score > 7 ? 'high' : complaint.severity_score >= 5 ? 'mid' : 'low'}`}>
              {complaint.severity_score}/10
            </span>
          </div>
          <div className="drawer-row">
            <span className="drawer-label">Station</span>
            <span className="drawer-value">{complaint.assigned_station || '—'}</span>
          </div>
          <div className="drawer-row">
            <span className="drawer-label">Jurisdiction</span>
            <span className="drawer-value">{complaint.station_jurisdiction || '—'}</span>
          </div>
          <div className="drawer-row">
            <span className="drawer-label">Location</span>
            <span className="drawer-value">{complaint.user_location || '—'}</span>
          </div>
          <div className="drawer-row">
            <span className="drawer-label">Filed On</span>
            <span className="drawer-value">{complaint.date_filed ? new Date(complaint.date_filed).toLocaleString() : '—'}</span>
          </div>

          {/* Fields */}
          {Object.keys(fields).length > 0 && (
            <>
              <h4 className="drawer-section-title">Complaint Fields</h4>
              {Object.entries(fields).map(([key, field]) => (
                <div className="drawer-row" key={key}>
                  <span className="drawer-label">{field.label || key}</span>
                  <span className="drawer-value">{String(field.value)}</span>
                </div>
              ))}
            </>
          )}

          {complaint.raw_description && (
            <>
              <h4 className="drawer-section-title">Raw Description</h4>
              <p className="drawer-description">{complaint.raw_description}</p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Main Dashboard ───────────────────────────────────────────────────────────

function OfficerDashboard({ officer, onLogout }) {
  const [complaints, setComplaints] = useState([]);
  const [metrics, setMetrics] = useState({ total: 0, pending: 0, accepted: 0, rejected: 0, transferred: 0 });
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [firModal, setFirModal] = useState(null);
  const [transferModal, setTransferModal] = useState(null);
  const [drawerComplaint, setDrawerComplaint] = useState(null);
  const [actionLoading, setActionLoading] = useState(null);

  // ── Fetch complaints ────────────────────────────────────────────────────
  const fetchData = useCallback(async () => {
    try {
      const data = await officerGetComplaints();
      setComplaints(data.complaints || []);
      setMetrics(data.metrics || { total: 0, pending: 0, accepted: 0, rejected: 0, transferred: 0 });
    } catch (err) {
      console.error('Failed to load complaints', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  // Auto-refresh every 15 s
  useEffect(() => {
    const iv = setInterval(fetchData, 15000);
    return () => clearInterval(iv);
  }, [fetchData]);

  // ── Actions ─────────────────────────────────────────────────────────────
  const handleStatusChange = async (id, status) => {
    setActionLoading(id);
    try {
      await officerUpdateStatus(id, status);
      await fetchData();
    } catch (err) {
      console.error('Status update failed', err);
    }
    setActionLoading(null);
  };

  const handleAssignFir = async (id, firNumber) => {
    try {
      await officerAssignFir(id, firNumber);
      await fetchData();
    } catch (err) {
      console.error('FIR assignment failed', err);
    }
  };

  const handleTransfer = async (id, targetStation) => {
    try {
      await officerTransferComplaint(id, targetStation);
      await fetchData();
    } catch (err) {
      console.error('Transfer failed', err);
    }
  };

  // ── Filtering ───────────────────────────────────────────────────────────
  const filtered = complaints.filter((c) => {
    if (filterStatus !== 'all' && c.status !== filterStatus) return false;
    if (searchTerm) {
      const q = searchTerm.toLowerCase();
      return (
        (c.complaint_id || '').toLowerCase().includes(q) ||
        (c.fir_number || '').toLowerCase().includes(q) ||
        (c.complaint_category_label || '').toLowerCase().includes(q) ||
        (c.assigned_station || '').toLowerCase().includes(q) ||
        (c.user_location || '').toLowerCase().includes(q)
      );
    }
    return true;
  });

  // ── Render ──────────────────────────────────────────────────────────────
  return (
    <div className="dashboard-wrapper">
      {/* ─── Top bar ────────────────────────────────────────────────────── */}
      <header className="dash-header">
        <div className="dash-header-left">
          <div className="dash-shield">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path strokeLinecap="round" strokeLinejoin="round"
                d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
            </svg>
          </div>
          <div>
            <h1 className="dash-title">Cyber Crime Command Centre</h1>
            <p className="dash-subtitle">Officer Dashboard — NCRP Complaint Tracking</p>
          </div>
        </div>

        <div className="dash-header-right">
          <div className="officer-info">
            <span className="officer-name">{officer?.name || 'Officer'}</span>
            <span className="officer-badge">{officer?.badge || ''}</span>
          </div>
          <button className="btn-logout" onClick={onLogout} id="officer-logout-btn">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="w-5 h-5">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            Logout
          </button>
        </div>
      </header>

      <main className="dash-main">
        {/* ─── Metric cards ──────────────────────────────────────────────── */}
        <section className="metrics-grid">
          <MetricCard label="Total Complaints" value={metrics.total} color="#6366f1"
            icon='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>' />
          <MetricCard label="Pending" value={metrics.pending} color="#f59e0b"
            icon='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>' />
          <MetricCard label="Accepted" value={metrics.accepted} color="#10b981"
            icon='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>' />
          <MetricCard label="Rejected" value={metrics.rejected} color="#ef4444"
            icon='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>' />
          <MetricCard label="Transferred" value={metrics.transferred} color="#8b5cf6"
            icon='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"/></svg>' />
        </section>

        {/* ─── Toolbar ───────────────────────────────────────────────────── */}
        <section className="dash-toolbar">
          <div className="search-box">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="search-icon">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              id="complaint-search"
              type="text"
              placeholder="Search by ID, FIR, category, station, location…"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          <div className="filter-tabs">
            {['all', 'pending', 'accepted', 'rejected', 'transferred'].map((s) => (
              <button
                key={s}
                className={`filter-tab ${filterStatus === s ? 'active' : ''}`}
                onClick={() => setFilterStatus(s)}
              >
                {s === 'all' ? 'All' : STATUS_CONFIG[s]?.label}
                {s !== 'all' && <span className="filter-count">{metrics[s] ?? 0}</span>}
              </button>
            ))}
          </div>
        </section>

        {/* ─── Complaints table ──────────────────────────────────────────── */}
        <section className="table-wrapper">
          {loading ? (
            <div className="table-empty">
              <div className="loader" />
              <p>Loading complaints…</p>
            </div>
          ) : filtered.length === 0 ? (
            <div className="table-empty">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="empty-icon">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                  d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
              </svg>
              <p>{complaints.length === 0 ? 'No complaints filed yet.' : 'No complaints match your filter.'}</p>
            </div>
          ) : (
            <table className="complaints-table" id="complaints-table">
              <thead>
                <tr>
                  <th>NCRP Number</th>
                  <th>Category</th>
                  <th>Status</th>
                  <th>FIR Number</th>
                  <th>Severity</th>
                  <th>Assigned Station</th>
                  <th>Location</th>
                  <th>Filed</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((c) => (
                  <tr key={c.complaint_id} className="complaint-row">
                    <td>
                      <button className="link-btn" onClick={() => setDrawerComplaint(c)}>
                        {c.complaint_id}
                      </button>
                    </td>
                    <td>
                      <span className="category-chip">{c.complaint_category_label || '—'}</span>
                    </td>
                    <td><StatusBadge status={c.status} /></td>
                    <td className="mono">{c.fir_number || '—'}</td>
                    <td>
                      <span className={`severity severity-${c.severity_score > 7 ? 'high' : c.severity_score >= 5 ? 'mid' : 'low'}`}>
                        {c.severity_score}
                      </span>
                    </td>
                    <td className="station-cell">{c.assigned_station || '—'}</td>
                    <td>{c.user_location || '—'}</td>
                    <td className="date-cell">{c.date_filed ? new Date(c.date_filed).toLocaleDateString() : '—'}</td>
                    <td>
                      <div className="action-group">
                        {c.status === 'pending' && (
                          <>
                            <button
                              className="act-btn accept"
                              title="Accept"
                              disabled={actionLoading === c.complaint_id}
                              onClick={() => handleStatusChange(c.complaint_id, 'accepted')}
                            >
                              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                            </button>
                            <button
                              className="act-btn reject"
                              title="Reject"
                              disabled={actionLoading === c.complaint_id}
                              onClick={() => handleStatusChange(c.complaint_id, 'rejected')}
                            >
                              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                            </button>
                          </>
                        )}
                        {!c.fir_number && c.status !== 'rejected' && (
                          <button className="act-btn fir" title="Assign FIR" onClick={() => setFirModal(c)}>
                            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                          </button>
                        )}
                        {c.status !== 'transferred' && c.status !== 'rejected' && (
                          <button className="act-btn transfer" title="Transfer" onClick={() => setTransferModal(c)}>
                            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" /></svg>
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      </main>

      {/* ─── Modals / Drawers ────────────────────────────────────────────── */}
      {firModal && <FirModal complaint={firModal} onClose={() => setFirModal(null)} onAssign={handleAssignFir} />}
      {transferModal && <TransferModal complaint={transferModal} onClose={() => setTransferModal(null)} onTransfer={handleTransfer} />}
      {drawerComplaint && <ComplaintDrawer complaint={drawerComplaint} onClose={() => setDrawerComplaint(null)} />}
    </div>
  );
}

export default OfficerDashboard;
