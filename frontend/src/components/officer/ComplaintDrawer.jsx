import { useState, useEffect } from 'react';
import { officerGetComplaintDetail } from '../../services/api';

const SEV_COLOR = { Critical: 'text-red-600 bg-red-50', High: 'text-orange-600 bg-orange-50', Medium: 'text-yellow-600 bg-yellow-50', Low: 'text-green-600 bg-green-50' };
const STATUS_COLOR = { pending: 'bg-yellow-100 text-yellow-800', accepted: 'bg-blue-100 text-blue-800', rejected: 'bg-red-100 text-red-800', transferred: 'bg-purple-100 text-purple-800', fir_assigned: 'bg-green-100 text-green-800' };

function Row({ label, value }) {
  if (!value || value === '—') return null;
  return (
    <div className="flex justify-between py-2 border-b border-gray-100 last:border-0 text-sm">
      <span className="text-gray-500 font-medium w-40 shrink-0">{label}</span>
      <span className="text-gray-900 text-right break-all">{value}</span>
    </div>
  );
}

export default function ComplaintDrawer({ complaintId, onClose, onAction }) {
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('details');

  useEffect(() => {
    if (!complaintId) return;
    setLoading(true);
    officerGetComplaintDetail(complaintId)
      .then(setDetail)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [complaintId]);

  if (!complaintId) return null;

  const c = detail;
  const fields = c?.fields || {};
  const evidenceFiles = c?.evidence_files || [];
  const auditTrail = c?.audit_trail || [];
  const severity = c?.severity_score || '';

  const sevKey = severity > 7 ? 'Critical' : severity >= 5 ? 'High' : severity >= 3 ? 'Medium' : 'Low';

  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-black/40" onClick={onClose}>
      <div className="w-full max-w-2xl bg-white h-full shadow-2xl flex flex-col overflow-hidden" onClick={e => e.stopPropagation()}>

        {/* Header */}
        <div className="bg-blue-900 text-white px-6 py-4 flex justify-between items-start">
          <div>
            <p className="text-blue-300 text-xs font-mono mb-1">COMPLAINT DOSSIER</p>
            <h2 className="text-lg font-bold">{loading ? '...' : c?.complaint_id}</h2>
            <p className="text-blue-200 text-sm">{c?.complaint_category_label || '—'}</p>
          </div>
          <button onClick={onClose} className="text-blue-300 hover:text-white mt-1">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>

        {/* Status + Severity bar */}
        {c && (
          <div className="px-6 py-3 bg-gray-50 border-b flex items-center gap-3 flex-wrap">
            <span className={`px-2.5 py-1 rounded-full text-xs font-bold uppercase ${STATUS_COLOR[c.status] || 'bg-gray-100 text-gray-700'}`}>{c.status?.replace('_', ' ')}</span>
            {severity && <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${SEV_COLOR[sevKey] || ''}`}>Severity: {sevKey} ({severity}/10)</span>}
            {c.fir_number && <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-green-100 text-green-800 font-mono">FIR: {c.fir_number}</span>}
          </div>
        )}

        {/* Tabs */}
        <div className="flex border-b bg-white">
          {['details','evidence','audit'].map(t => (
            <button key={t} onClick={() => setTab(t)}
              className={`px-5 py-3 text-sm font-medium capitalize ${tab === t ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500 hover:text-gray-800'}`}>
              {t}{t === 'evidence' && evidenceFiles.length > 0 && <span className="ml-1.5 bg-blue-100 text-blue-700 text-xs px-1.5 py-0.5 rounded-full">{evidenceFiles.length}</span>}
              {t === 'audit' && auditTrail.length > 0 && <span className="ml-1.5 bg-gray-100 text-gray-600 text-xs px-1.5 py-0.5 rounded-full">{auditTrail.length}</span>}
            </button>
          ))}
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {loading && <p className="text-gray-400 text-center py-12">Loading dossier…</p>}

          {!loading && c && tab === 'details' && (
            <div className="space-y-4">
              <div>
                <h4 className="text-xs font-bold uppercase text-gray-400 mb-2">Core Info</h4>
                <Row label="NCRP Number" value={c.ncrp_number || c.complaint_id} />
                <Row label="Date Filed" value={c.date_filed ? new Date(c.date_filed).toLocaleString() : '—'} />
                <Row label="Assigned Station" value={c.assigned_station} />
                <Row label="Jurisdiction" value={c.station_jurisdiction} />
                <Row label="User Location" value={c.user_location} />
                {c.rejection_reason && <Row label="Rejection Reason" value={c.rejection_reason} />}
              </div>

              {c.raw_description && (
                <div>
                  <h4 className="text-xs font-bold uppercase text-gray-400 mb-2">Incident Narrative</h4>
                  <p className="text-sm text-gray-700 bg-gray-50 rounded-lg p-3 leading-relaxed">{c.raw_description}</p>
                </div>
              )}

              {Object.keys(fields).length > 0 && (
                <div>
                  <h4 className="text-xs font-bold uppercase text-gray-400 mb-2">Structured Fields</h4>
                  {Object.entries(fields).map(([k, v]) => (
                    <Row key={k} label={(v.label || k).replace(/_/g, ' ')} value={String(v.value ?? v)} />
                  ))}
                </div>
              )}

              {/* Action buttons */}
              <div className="pt-4 flex flex-wrap gap-2 border-t">
                {c.status === 'pending' && (
                  <button onClick={() => onAction('accept', c)} className="px-4 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700">✓ Accept</button>
                )}
                {c.status !== 'rejected' && (
                  <button onClick={() => onAction('reject', c)} className="px-4 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700">✕ Reject</button>
                )}
                {!c.fir_number && c.status !== 'rejected' && (
                  <button onClick={() => onAction('fir', c)} className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700">📋 Assign FIR</button>
                )}
                {c.status !== 'transferred' && c.status !== 'rejected' && (
                  <button onClick={() => onAction('transfer', c)} className="px-4 py-2 text-sm bg-purple-600 text-white rounded-lg hover:bg-purple-700">↗ Transfer</button>
                )}
              </div>
            </div>
          )}

          {!loading && tab === 'evidence' && (
            <div>
              {evidenceFiles.length === 0 ? (
                <p className="text-gray-400 text-center py-12 text-sm">No evidence files uploaded.</p>
              ) : (
                <div className="grid grid-cols-2 gap-3">
                  {evidenceFiles.map((f, i) => {
                    const isImage = /\.(jpg|jpeg|png|gif|webp)$/i.test(f.file_name || '');
                    const url = `http://localhost:8000/api/v1/upload/evidence/${f.file_id || f.file_name}`;
                    return (
                      <div key={i} className="border rounded-xl overflow-hidden bg-gray-50">
                        {isImage ? (
                          <img src={url} alt={f.file_name} className="w-full h-36 object-cover" />
                        ) : (
                          <div className="h-36 flex items-center justify-center text-4xl">📄</div>
                        )}
                        <div className="p-2">
                          <p className="text-xs text-gray-600 truncate font-medium">{f.file_name}</p>
                          <a href={url} download className="text-xs text-blue-600 hover:underline">Download</a>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {!loading && tab === 'audit' && (
            <div className="space-y-3">
              {auditTrail.length === 0 ? (
                <p className="text-gray-400 text-center py-12 text-sm">No officer actions recorded yet.</p>
              ) : auditTrail.map((e, i) => (
                <div key={i} className="flex gap-3 text-sm">
                  <div className="w-2 h-2 rounded-full bg-blue-500 mt-1.5 shrink-0" />
                  <div>
                    <p className="font-medium text-gray-800">{e.action.replace('_', ' ')}</p>
                    <p className="text-gray-500 text-xs">{e.officer_badge} · {new Date(e.timestamp).toLocaleString()}</p>
                    {e.notes && <p className="text-gray-600 text-xs mt-0.5 italic">{e.notes}</p>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
