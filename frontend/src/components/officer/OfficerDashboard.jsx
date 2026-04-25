import { useState, useEffect, useCallback } from 'react';
import {
  officerGetComplaints, officerAccept, officerReject,
  officerAssignFir, officerTransferComplaint, officerGetAdminMetrics,
} from '../../services/api';
import { FirModal, RejectModal, TransferModal } from './OfficerModals';
import ComplaintDrawer from './ComplaintDrawer';

const STATUS_CFG = {
  pending:      { label: 'Pending',          color: '#f59e0b', bg: 'rgba(245,158,11,.12)' },
  accepted:     { label: 'Accepted',         color: '#3b82f6', bg: 'rgba(59,130,246,.12)' },
  rejected:     { label: 'Rejected',         color: '#ef4444', bg: 'rgba(239,68,68,.12)'  },
  transferred:  { label: 'Transferred',      color: '#8b5cf6', bg: 'rgba(139,92,246,.12)' },
  fir_assigned: { label: 'FIR Assigned',     color: '#10b981', bg: 'rgba(16,185,129,.12)' },
};

function StatusBadge({ status }) {
  const c = STATUS_CFG[status] || STATUS_CFG.pending;
  return (
    <span style={{ color: c.color, background: c.bg }} className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold">
      <span className="w-1.5 h-1.5 rounded-full" style={{ background: c.color }} />
      {c.label}
    </span>
  );
}

function SeverityChip({ score }) {
  if (score === undefined || score === null) return <span className="text-gray-400">—</span>;
  const n = Number(score);
  const [label, cls] = n > 7 ? ['Critical','bg-red-100 text-red-700'] : n >= 5 ? ['High','bg-orange-100 text-orange-700'] : n >= 3 ? ['Medium','bg-yellow-100 text-yellow-700'] : ['Low','bg-green-100 text-green-700'];
  return <span className={`text-xs px-2 py-0.5 rounded-full font-bold ${cls}`}>{label}</span>;
}

function MetricCard({ label, value, color }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border p-4 flex items-center gap-4">
      <div className="w-10 h-10 rounded-xl flex items-center justify-center text-white text-lg font-bold" style={{ background: color }}>{value}</div>
      <span className="text-sm font-medium text-gray-600">{label}</span>
    </div>
  );
}

export default function OfficerDashboard({ officer, onLogout }) {
  const [complaints, setComplaints]     = useState([]);
  const [metrics, setMetrics]           = useState({});
  const [adminMetrics, setAdminMetrics] = useState(null);
  const [loading, setLoading]           = useState(true);
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterType, setFilterType]     = useState('all');
  const [search, setSearch]             = useState('');
  const [view, setView]                 = useState('queue'); // queue | admin
  const [drawerComplaintId, setDrawer]  = useState(null);
  const [modal, setModal]               = useState(null); // {type, complaint}
  const [toast, setToast]               = useState(null);
  const isAdmin = officer?.role === 'ADMIN_OFFICER';

  const showToast = (msg, ok = true) => {
    setToast({ msg, ok });
    setTimeout(() => setToast(null), 3500);
  };

  const fetchData = useCallback(async () => {
    try {
      const data = await officerGetComplaints();
      setComplaints(data.complaints || []);
      setMetrics(data.metrics || {});
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);
  useEffect(() => { const iv = setInterval(fetchData, 20000); return () => clearInterval(iv); }, [fetchData]);

  useEffect(() => {
    if (view === 'admin' && isAdmin && !adminMetrics) {
      officerGetAdminMetrics().then(setAdminMetrics).catch(console.error);
    }
  }, [view, isAdmin, adminMetrics]);

  // Actions
  const act = async (type, complaint) => {
    if (type === 'accept') {
      try { await officerAccept(complaint.complaint_id); showToast('Complaint accepted.'); await fetchData(); }
      catch { showToast('Failed.', false); }
    } else {
      setModal({ type, complaint });
    }
  };

  const handleFir = async (id, fir) => {
    try { await officerAssignFir(id, fir); showToast('FIR assigned.'); await fetchData(); }
    catch { showToast('Failed.', false); }
  };
  const handleReject = async (id, reason) => {
    try { await officerReject(id, reason); showToast('Complaint rejected.'); await fetchData(); }
    catch { showToast('Failed.', false); }
  };
  const handleTransfer = async (id, station, notes) => {
    try { await officerTransferComplaint(id, station, notes); showToast('Complaint transferred.'); await fetchData(); }
    catch { showToast('Failed.', false); }
  };

  // Filtering
  const fraudTypes = [...new Set(complaints.map(c => c.complaint_category_label || 'Unknown'))];
  const filtered = complaints.filter(c => {
    if (filterStatus !== 'all' && c.status !== filterStatus) return false;
    if (filterType !== 'all' && (c.complaint_category_label || 'Unknown') !== filterType) return false;
    if (search) {
      const q = search.toLowerCase();
      return (c.complaint_id||'').toLowerCase().includes(q) ||
             (c.user_location||'').toLowerCase().includes(q) ||
             (c.complaint_category_label||'').toLowerCase().includes(q) ||
             (c.fir_number||'').toLowerCase().includes(q);
    }
    return true;
  });

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-blue-900 text-white px-6 py-4 flex justify-between items-center shadow-lg">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-800 rounded-lg">
            <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z"/></svg>
          </div>
          <div>
            <h1 className="text-lg font-bold">CrimePilot Command Centre</h1>
            <p className="text-blue-300 text-xs">{officer?.station}</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right hidden md:block">
            <p className="text-sm font-semibold">{officer?.name}</p>
            <p className="text-blue-300 text-xs font-mono">{officer?.badge} · {officer?.role}</p>
          </div>
          {isAdmin && (
            <div className="flex rounded-lg overflow-hidden border border-blue-700 text-xs font-semibold">
              <button onClick={() => setView('queue')} className={`px-3 py-1.5 ${view==='queue'?'bg-blue-700 text-white':'text-blue-200 hover:bg-blue-800'}`}>Queue</button>
              <button onClick={() => setView('admin')} className={`px-3 py-1.5 ${view==='admin'?'bg-blue-700 text-white':'text-blue-200 hover:bg-blue-800'}`}>Admin</button>
            </div>
          )}
          <button onClick={onLogout} className="flex items-center gap-1.5 px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white text-xs font-semibold rounded-lg">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/></svg>
            Logout
          </button>
        </div>
      </header>

      <main className="flex-1 max-w-7xl mx-auto w-full px-4 py-6 space-y-5">
        {/* Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          <MetricCard label="Total"        value={metrics.total        ?? 0} color="#6366f1"/>
          <MetricCard label="Pending"      value={metrics.pending      ?? 0} color="#f59e0b"/>
          <MetricCard label="Accepted"     value={metrics.accepted     ?? 0} color="#3b82f6"/>
          <MetricCard label="FIR Assigned" value={metrics.fir_assigned ?? 0} color="#10b981"/>
          <MetricCard label="Rejected"     value={metrics.rejected     ?? 0} color="#ef4444"/>
          <MetricCard label="Transferred"  value={metrics.transferred  ?? 0} color="#8b5cf6"/>
        </div>

        {view === 'queue' && (
          <>
            {/* Filters */}
            <div className="bg-white rounded-xl shadow-sm border p-4 flex flex-wrap gap-3 items-center">
              <div className="relative flex-1 min-w-48">
                <svg className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
                <input className="w-full pl-9 pr-3 py-2 text-sm border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" placeholder="Search ID, location, type…" value={search} onChange={e => setSearch(e.target.value)} />
              </div>
              <select className="text-sm border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none" value={filterStatus} onChange={e => setFilterStatus(e.target.value)}>
                <option value="all">All Statuses</option>
                {Object.entries(STATUS_CFG).map(([v,c]) => <option key={v} value={v}>{c.label}</option>)}
              </select>
              <select className="text-sm border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none" value={filterType} onChange={e => setFilterType(e.target.value)}>
                <option value="all">All Fraud Types</option>
                {fraudTypes.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
              <span className="text-xs text-gray-500 ml-auto">{filtered.length} complaint{filtered.length !== 1 ? 's' : ''}</span>
            </div>

            {/* Table */}
            <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
              {loading ? (
                <div className="py-20 text-center text-gray-400">Loading complaints…</div>
              ) : filtered.length === 0 ? (
                <div className="py-20 text-center text-gray-400">
                  <svg className="w-12 h-12 mx-auto mb-3 text-gray-200" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"/></svg>
                  {complaints.length === 0 ? 'No complaints filed yet.' : 'No complaints match your filters.'}
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50 text-gray-500 text-xs uppercase tracking-wider">
                      <tr>{['Tracking ID','Category','Severity','Status','FIR','Amount','Location','Filed','Actions'].map(h => <th key={h} className="px-4 py-3 text-left font-semibold">{h}</th>)}</tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {filtered.map(c => (
                        <tr key={c.complaint_id} className="hover:bg-blue-50/30 transition-colors">
                          <td className="px-4 py-3">
                            <button className="font-mono text-blue-700 font-semibold hover:underline text-xs" onClick={() => setDrawer(c.complaint_id)}>{c.complaint_id}</button>
                          </td>
                          <td className="px-4 py-3 max-w-[160px]"><span className="text-xs bg-gray-100 px-2 py-0.5 rounded-full">{c.complaint_category_label || '—'}</span></td>
                          <td className="px-4 py-3"><SeverityChip score={c.severity_score} /></td>
                          <td className="px-4 py-3"><StatusBadge status={c.status} /></td>
                          <td className="px-4 py-3 font-mono text-xs text-gray-600">{c.fir_number || '—'}</td>
                          <td className="px-4 py-3 text-xs text-gray-700">{c.fields?.amount_lost?.value ? `₹${c.fields.amount_lost.value}` : '—'}</td>
                          <td className="px-4 py-3 text-xs text-gray-600">{c.user_location || '—'}</td>
                          <td className="px-4 py-3 text-xs text-gray-500 whitespace-nowrap">{c.date_filed ? new Date(c.date_filed).toLocaleDateString('en-IN') : '—'}</td>
                          <td className="px-4 py-3">
                            <div className="flex gap-1">
                              {c.status === 'pending' && <button title="Accept" onClick={() => act('accept', c)} className="p-1.5 rounded-lg bg-green-100 text-green-700 hover:bg-green-200"><svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7"/></svg></button>}
                              {c.status !== 'rejected' && <button title="Reject" onClick={() => act('reject', c)} className="p-1.5 rounded-lg bg-red-100 text-red-700 hover:bg-red-200"><svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12"/></svg></button>}
                              {!c.fir_number && c.status !== 'rejected' && <button title="Assign FIR" onClick={() => act('fir', c)} className="p-1.5 rounded-lg bg-blue-100 text-blue-700 hover:bg-blue-200"><svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg></button>}
                              {c.status !== 'transferred' && c.status !== 'rejected' && <button title="Transfer" onClick={() => act('transfer', c)} className="p-1.5 rounded-lg bg-purple-100 text-purple-700 hover:bg-purple-200"><svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"/></svg></button>}
                              <button title="View Dossier" onClick={() => setDrawer(c.complaint_id)} className="p-1.5 rounded-lg bg-gray-100 text-gray-600 hover:bg-gray-200"><svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg></button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </>
        )}

        {view === 'admin' && isAdmin && (
          <div className="space-y-5">
            {!adminMetrics ? (
              <div className="py-20 text-center text-gray-400">Loading admin metrics…</div>
            ) : (
              <>
                {/* Fraud type breakdown */}
                <div className="bg-white rounded-xl shadow-sm border p-5">
                  <h3 className="font-bold text-gray-800 mb-4">Complaints by Fraud Type</h3>
                  <div className="space-y-2">
                    {Object.entries(adminMetrics.by_fraud_type || {}).sort((a,b)=>b[1]-a[1]).map(([type, count]) => (
                      <div key={type} className="flex items-center gap-3">
                        <span className="text-sm text-gray-600 w-52 truncate">{type}</span>
                        <div className="flex-1 bg-gray-100 rounded-full h-2">
                          <div className="bg-blue-600 h-2 rounded-full" style={{width:`${Math.min(100,(count/adminMetrics.total_complaints)*100)}%`}}/>
                        </div>
                        <span className="text-sm font-bold text-gray-800 w-8 text-right">{count}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* By station */}
                <div className="bg-white rounded-xl shadow-sm border p-5">
                  <h3 className="font-bold text-gray-800 mb-4">Complaints by Station</h3>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead><tr className="text-xs text-gray-500 uppercase">{['Station','Total','Pending','Accepted','Rejected','Transferred','FIR Assigned'].map(h=><th key={h} className="text-left py-2 pr-4">{h}</th>)}</tr></thead>
                      <tbody className="divide-y divide-gray-100">
                        {Object.entries(adminMetrics.by_station || {}).map(([st, m]) => (
                          <tr key={st}>
                            <td className="py-2 pr-4 text-gray-700 max-w-xs truncate">{st}</td>
                            <td className="py-2 pr-4 font-bold">{m.total}</td>
                            <td className="py-2 pr-4 text-yellow-600">{m.pending}</td>
                            <td className="py-2 pr-4 text-blue-600">{m.accepted}</td>
                            <td className="py-2 pr-4 text-red-600">{m.rejected}</td>
                            <td className="py-2 pr-4 text-purple-600">{m.transferred}</td>
                            <td className="py-2 pr-4 text-green-600">{m.fir_assigned}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </>
            )}
          </div>
        )}
      </main>

      {/* Modals */}
      {modal?.type === 'fir'      && <FirModal      complaint={modal.complaint} onClose={() => setModal(null)} onAssign={handleFir}      />}
      {modal?.type === 'reject'   && <RejectModal   complaint={modal.complaint} onClose={() => setModal(null)} onReject={handleReject}   />}
      {modal?.type === 'transfer' && <TransferModal complaint={modal.complaint} onClose={() => setModal(null)} onTransfer={handleTransfer}/>}

      {/* Drawer */}
      <ComplaintDrawer
        complaintId={drawerComplaintId}
        onClose={() => setDrawer(null)}
        onAction={(type, c) => { setDrawer(null); setModal({ type, complaint: c }); }}
      />

      {/* Toast */}
      {toast && (
        <div className={`fixed bottom-5 right-5 px-5 py-3 rounded-xl shadow-lg text-white text-sm font-medium z-50 ${toast.ok ? 'bg-green-600' : 'bg-red-600'}`}>
          {toast.msg}
        </div>
      )}
    </div>
  );
}
