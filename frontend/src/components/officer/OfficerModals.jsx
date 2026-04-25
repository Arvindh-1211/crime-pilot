import { useState } from 'react';

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

function ModalShell({ title, subtitle, onClose, children }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6" onClick={e => e.stopPropagation()}>
        <h3 className="text-lg font-bold text-gray-900 mb-1">{title}</h3>
        {subtitle && <p className="text-sm text-gray-500 mb-4">{subtitle}</p>}
        {children}
      </div>
    </div>
  );
}

export function FirModal({ complaint, onClose, onAssign }) {
  const [fir, setFir] = useState('');
  const [loading, setLoading] = useState(false);
  const handle = async () => {
    if (!fir.trim()) return;
    setLoading(true);
    await onAssign(complaint.complaint_id, fir.trim());
    setLoading(false); onClose();
  };
  return (
    <ModalShell title="Assign FIR Number" subtitle={`Complaint ${complaint.complaint_id} — ticket stays open after FIR assignment.`} onClose={onClose}>
      <input autoFocus className="w-full border rounded-lg px-3 py-2 mb-4 text-sm font-mono focus:ring-2 focus:ring-blue-500 outline-none" placeholder="e.g. FIR-2025-MH-04821" value={fir} onChange={e => setFir(e.target.value)} />
      <div className="flex gap-2 justify-end">
        <button onClick={onClose} className="px-4 py-2 text-sm rounded-lg border hover:bg-gray-50">Cancel</button>
        <button onClick={handle} disabled={!fir.trim() || loading} className="px-4 py-2 text-sm rounded-lg bg-blue-600 text-white disabled:opacity-50 hover:bg-blue-700">{loading ? 'Assigning…' : 'Assign FIR'}</button>
      </div>
    </ModalShell>
  );
}

export function RejectModal({ complaint, onClose, onReject }) {
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);
  const QUICK = ['Outside jurisdiction', 'Duplicate complaint', 'No cognizable offence', 'Insufficient evidence'];
  const handle = async () => {
    if (!reason.trim()) return;
    setLoading(true);
    await onReject(complaint.complaint_id, reason.trim());
    setLoading(false); onClose();
  };
  return (
    <ModalShell title="Reject Complaint" subtitle={`${complaint.complaint_id} — provide a mandatory reason for the citizen record.`} onClose={onClose}>
      <div className="flex flex-wrap gap-2 mb-3">
        {QUICK.map(q => <button key={q} onClick={() => setReason(q)} className={`text-xs px-2 py-1 rounded-full border ${reason === q ? 'bg-red-100 border-red-400 text-red-700' : 'hover:bg-gray-50'}`}>{q}</button>)}
      </div>
      <textarea className="w-full border rounded-lg px-3 py-2 mb-4 text-sm focus:ring-2 focus:ring-red-400 outline-none resize-none" rows={3} placeholder="Enter rejection reason…" value={reason} onChange={e => setReason(e.target.value)} />
      <div className="flex gap-2 justify-end">
        <button onClick={onClose} className="px-4 py-2 text-sm rounded-lg border hover:bg-gray-50">Cancel</button>
        <button onClick={handle} disabled={!reason.trim() || loading} className="px-4 py-2 text-sm rounded-lg bg-red-600 text-white disabled:opacity-50 hover:bg-red-700">{loading ? 'Rejecting…' : 'Confirm Reject'}</button>
      </div>
    </ModalShell>
  );
}

export function TransferModal({ complaint, onClose, onTransfer }) {
  const [station, setStation] = useState('');
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const handle = async () => {
    if (!station) return;
    setLoading(true);
    await onTransfer(complaint.complaint_id, station, notes);
    setLoading(false); onClose();
  };
  return (
    <ModalShell title="Transfer Complaint" subtitle={`Re-route ${complaint.complaint_id} to another cyber cell.`} onClose={onClose}>
      <select className="w-full border rounded-lg px-3 py-2 mb-3 text-sm focus:ring-2 focus:ring-purple-500 outline-none" value={station} onChange={e => setStation(e.target.value)}>
        <option value="">Select destination station…</option>
        {STATIONS.filter(s => s !== complaint.assigned_station).map(s => <option key={s} value={s}>{s}</option>)}
      </select>
      <textarea className="w-full border rounded-lg px-3 py-2 mb-4 text-sm focus:ring-2 focus:ring-purple-400 outline-none resize-none" rows={2} placeholder="Transfer notes (optional)…" value={notes} onChange={e => setNotes(e.target.value)} />
      <div className="flex gap-2 justify-end">
        <button onClick={onClose} className="px-4 py-2 text-sm rounded-lg border hover:bg-gray-50">Cancel</button>
        <button onClick={handle} disabled={!station || loading} className="px-4 py-2 text-sm rounded-lg bg-purple-600 text-white disabled:opacity-50 hover:bg-purple-700">{loading ? 'Transferring…' : 'Transfer'}</button>
      </div>
    </ModalShell>
  );
}
