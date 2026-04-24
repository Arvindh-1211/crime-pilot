import { useParams, Link } from 'react-router-dom';

const STATUS_CONFIG = {
  pending:     { label: 'Under Review',   color: 'bg-yellow-100 text-yellow-800 border-yellow-200', icon: '⏳' },
  accepted:    { label: 'Accepted',       color: 'bg-green-100 text-green-800 border-green-200',    icon: '✅' },
  rejected:    { label: 'Rejected',       color: 'bg-red-100 text-red-800 border-red-200',          icon: '❌' },
  transferred: { label: 'Transferred',   color: 'bg-blue-100 text-blue-800 border-blue-200',        icon: '🔀' },
};

const SLOT_LABELS = {
  victim_name: 'Complainant Name', victim_phone: 'Contact Phone', victim_email: 'Email',
  incident_date: 'Incident Date', incident_time: 'Incident Time', incident_location: 'City / State',
  amount_lost: 'Amount Lost (₹)', upi_transaction_id: 'UPI Transaction ID', suspect_upi_id: 'Suspect UPI ID',
  platform: 'UPI App Used', caller_number: "Caller's Phone", otp_shared: 'OTP Shared',
  caller_claimed_to_be: 'Caller Claimed To Be', phishing_url: 'Phishing URL',
  data_compromised: 'Data Compromised', amount_invested: 'Amount Invested (₹)',
  platform_name: 'Investment Platform', recruiter_contact: 'Recruiter Contact',
  platform_used: 'Platform Used', suspect_contact: 'Suspect Contact',
  amount_paid: 'Amount Paid (₹)', blackmail_method: 'Blackmail Method',
  job_platform: 'Job Platform', task_description: 'Tasks Assigned', deposit_paid: 'Deposit Paid (₹)',
  sim_stopped_working: 'SIM Stopped', service_hijacked: 'Service Hijacked', amount_lost_sim: 'Amount Lost (₹)',
  social_platform: 'Social Platform', fake_profile_id: 'Fake Profile', romance_money_sent: 'Money Sent (₹)',
  lottery_prize_claimed: 'Prize Claimed', processing_fee_paid: 'Fee Paid (₹)',
  shopping_website: 'Website', order_id: 'Order ID', product_not_received: 'Product',
  amount_paid_shopping: 'Amount Paid (₹)', identity_misused: 'Identity Misuse',
  loan_amount: 'Fraudulent Loan (₹)', financial_institution: 'Institution',
};

function formatVal(key, val) {
  if (val === 'true') return 'Yes';
  if (val === 'false') return 'No';
  if (key === 'incident_date') {
    try { return new Date(val).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }); } catch { return val; }
  }
  return val;
}

export default function ComplaintTracker() {
  const { complaintId } = useParams();

  // Read from localStorage (simulated database)
  let complaint = null;
  try {
    const raw = localStorage.getItem(`complaint_${complaintId}`);
    if (raw) complaint = JSON.parse(raw);
  } catch {}

  if (!complaint) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-xl shadow p-8 max-w-md w-full text-center">
          <div className="text-5xl mb-4">🔍</div>
          <h1 className="text-xl font-bold text-gray-800 mb-2">Complaint Not Found</h1>
          <p className="text-gray-500 text-sm mb-4">
            No complaint with ID <span className="font-mono font-bold">{complaintId}</span> was found in this browser.
          </p>
          <p className="text-xs text-gray-400 mb-6">
            Complaint data is stored in this browser's local storage. If you filed the complaint on a different device or browser, please use that device to track it.
          </p>
          <Link to="/chat" className="inline-block px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700">
            File a New Complaint
          </Link>
        </div>
      </div>
    );
  }

  const status = complaint.status || 'pending';
  const statusCfg = STATUS_CONFIG[status] || STATUS_CONFIG.pending;

  const fields = complaint.fields || {};
  const fieldEntries = Object.entries(fields);

  const dateFiled = complaint.date_filed
    ? new Date(complaint.date_filed).toLocaleString('en-IN', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
    : '—';

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-blue-700 text-white px-6 py-4 shadow">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <div>
            <p className="text-xs text-blue-200 uppercase tracking-widest">National Cybercrime Reporting Portal</p>
            <h1 className="text-lg font-bold mt-0.5">Complaint Tracker</h1>
          </div>
          <Link to="/chat" className="text-xs text-blue-200 hover:text-white">← File New Complaint</Link>
        </div>
      </div>

      <div className="max-w-3xl mx-auto p-4 sm:p-6 space-y-4">

        {/* Complaint ID + Status */}
        <div className="bg-white rounded-xl shadow p-5">
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div>
              <p className="text-xs text-gray-400 uppercase tracking-widest mb-1">Complaint ID</p>
              <p className="text-xl font-mono font-bold text-gray-900">{complaint.complaint_id}</p>
              <p className="text-xs text-gray-500 mt-1">Filed on {dateFiled}</p>
            </div>
            <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-semibold border ${statusCfg.color}`}>
              {statusCfg.icon} {statusCfg.label}
            </span>
          </div>

          <div className="mt-4 pt-4 border-t border-gray-100 grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
            <div>
              <span className="text-xs text-gray-400">Complaint Type</span>
              <p className="font-medium text-gray-800">{complaint.complaint_category_label || complaint.complaint_category || '—'}</p>
            </div>
            <div>
              <span className="text-xs text-gray-400">Assigned To</span>
              <p className="font-medium text-gray-800">{complaint.assigned_station || '—'}</p>
            </div>
            {complaint.fir_number && (
              <div>
                <span className="text-xs text-gray-400">FIR Number</span>
                <p className="font-medium text-gray-800">{complaint.fir_number}</p>
              </div>
            )}
            {complaint.severity_score && (
              <div>
                <span className="text-xs text-gray-400">Severity Score</span>
                <p className="font-medium text-orange-600">{complaint.severity_score} / 10</p>
              </div>
            )}
          </div>
        </div>

        {/* Progress Timeline */}
        <div className="bg-white rounded-xl shadow p-5">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Complaint Progress</h2>
          <div className="flex items-center gap-0">
            {['pending', 'accepted', 'transferred'].map((step, i) => {
              const isActive = status === step;
              const isPast = ['pending', 'accepted', 'transferred', 'rejected'].indexOf(status) > i;
              const stepLabels = { pending: 'Registered', accepted: 'Accepted', transferred: 'Transferred' };
              return (
                <div key={step} className="flex items-center flex-1">
                  <div className="flex flex-col items-center flex-shrink-0">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold border-2 transition-colors
                      ${isActive ? 'bg-blue-600 border-blue-600 text-white' : isPast ? 'bg-green-500 border-green-500 text-white' : 'bg-white border-gray-300 text-gray-400'}`}>
                      {isPast && !isActive ? '✓' : i + 1}
                    </div>
                    <span className={`text-xs mt-1 text-center w-16 ${isActive ? 'text-blue-700 font-semibold' : isPast ? 'text-green-600' : 'text-gray-400'}`}>
                      {stepLabels[step]}
                    </span>
                  </div>
                  {i < 2 && <div className={`flex-1 h-0.5 ${isPast ? 'bg-green-400' : 'bg-gray-200'}`} />}
                </div>
              );
            })}
          </div>
        </div>

        {/* Collected Details */}
        {fieldEntries.length > 0 && (
          <div className="bg-white rounded-xl shadow p-5">
            <h2 className="text-sm font-semibold text-gray-700 mb-3">Complaint Details</h2>
            <div className="divide-y divide-gray-100">
              {fieldEntries.map(([key, field]) => {
                const label = SLOT_LABELS[key] || field.label || key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
                const val = typeof field === 'object' && field.value !== undefined ? field.value : field;
                return (
                  <div key={key} className="flex justify-between items-start py-2.5 gap-4">
                    <span className="text-xs text-gray-500 w-40 flex-shrink-0">{label}</span>
                    <span className="text-xs text-gray-800 font-medium text-right break-all">{formatVal(key, val)}</span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Raw Description */}
        {complaint.raw_description && (
          <div className="bg-white rounded-xl shadow p-5">
            <h2 className="text-sm font-semibold text-gray-700 mb-2">Your Description</h2>
            <p className="text-sm text-gray-600 leading-relaxed">{complaint.raw_description}</p>
          </div>
        )}

        {/* Help Banner */}
        <div className="bg-blue-50 border border-blue-100 rounded-xl p-4 text-center">
          <p className="text-sm text-blue-800 font-medium">Need urgent help?</p>
          <p className="text-xs text-blue-600 mt-1">Call the National Cybercrime Helpline: <span className="font-bold text-lg">1930</span></p>
        </div>
      </div>
    </div>
  );
}
