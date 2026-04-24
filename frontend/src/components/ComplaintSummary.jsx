import { useState, useCallback } from 'react';

// Human-readable labels for slot keys
const SLOT_LABELS = {
  victim_name: 'Complainant Name',
  victim_phone: 'Contact Phone',
  victim_email: 'Email Address',
  incident_date: 'Incident Date',
  incident_time: 'Incident Time',
  incident_location: 'City / State',
  amount_lost: 'Amount Lost (₹)',
  upi_transaction_id: 'UPI Transaction ID',
  suspect_upi_id: 'Suspect UPI ID',
  platform: 'UPI App Used',
  utr_number: 'UTR Number',
  bank_name_victim: 'Your Bank',
  account_number_victim: 'Your Account Number',
  screenshot: 'Screenshot Available',
  caller_number: "Caller's Phone Number",
  caller_claimed_to_be: 'Caller Claimed To Be',
  otp_shared: 'OTP / PIN Shared',
  call_recording: 'Call Recording Available',
  bank_name: 'Bank Claimed',
  remote_app_installed: 'Remote App Installed',
  phishing_url: 'Phishing URL',
  data_compromised: 'Data Compromised',
  email_screenshot: 'Email/Message Screenshot',
  bank_involved: 'Bank Targeted',
  account_compromised: 'Account Accessed',
  amount_invested: 'Amount Invested (₹)',
  platform_name: 'Investment Platform',
  recruiter_contact: 'Recruiter Contact',
  payment_mode: 'Payment Mode',
  payment_proof: 'Payment Proof Available',
  withdrawal_blocked: 'Withdrawal Blocked',
  platform_used: 'Platform Used by Suspect',
  suspect_contact: 'Suspect Contact / ID',
  amount_paid: 'Amount Already Paid (₹)',
  blackmail_method: 'Blackmail Method',
  screenshot_available: 'Screenshots Available',
  amount_demanded: 'Amount Demanded (₹)',
  content_recorded: 'Content Was Recorded',
  job_platform: 'Job / Task Platform',
  task_description: 'Tasks Assigned',
  deposit_paid: 'Deposit / Fee Paid (₹)',
  recruiter_contact_job: 'Recruiter / HR Contact',
  job_offer_screenshot: 'Job Offer Screenshot',
  app_used_for_tasks: 'Task App Used',
  website_url: 'Scam Website URL',
  sim_stopped_working: 'SIM Stopped Working',
  service_hijacked: 'Service Hijacked',
  amount_lost_sim: 'Amount Lost (₹)',
  bank_name_sim: 'Bank Account Drained',
  transaction_sms: 'Transaction SMS Available',
  telecom_operator: 'Telecom Operator',
  social_platform: 'Social Platform',
  fake_profile_id: 'Fake Profile ID / Name',
  romance_money_sent: 'Money Sent to Suspect (₹)',
  how_long_known: 'Duration of Contact',
  profile_screenshot: 'Profile Screenshot',
  chat_screenshot: 'Chat Screenshot',
  amount_total_sent: 'Total Amount Sent (₹)',
  lottery_prize_claimed: 'Prize Claimed',
  processing_fee_paid: 'Processing Fee Paid (₹)',
  contact_channel: 'Contact Channel',
  sender_contact: 'Sender Contact',
  lottery_message_screenshot: 'Lottery Message Screenshot',
  bank_used_for_payment: 'Bank Used for Fee Payment',
  shopping_website: 'Shopping Website / Platform',
  order_id: 'Order ID',
  product_not_received: 'Product Ordered',
  amount_paid_shopping: 'Amount Paid (₹)',
  order_screenshot: 'Order Screenshot',
  seller_contact: 'Seller Contact',
  delivery_status: 'Delivery Status',
  identity_misused: 'Type of Identity Misuse',
  how_discovered: 'How Discovered',
  loan_amount: 'Fraudulent Loan Amount (₹)',
  financial_institution: 'Financial Institution',
  aadhaar_misused: 'Aadhaar Misused',
  pan_misused: 'PAN Misused',
  credit_score_affected: 'Credit Score Affected',
};

const CATEGORY_COLORS = {
  UPI_FRAUD: 'bg-red-100 text-red-800',
  VISHING: 'bg-orange-100 text-orange-800',
  PHISHING: 'bg-yellow-100 text-yellow-800',
  INVESTMENT_SCAM: 'bg-purple-100 text-purple-800',
  SEXTORTION: 'bg-red-900 text-red-100',
  JOB_FRAUD: 'bg-yellow-100 text-yellow-900',
  OTP_SIM_SWAP: 'bg-blue-100 text-blue-800',
  SOCIAL_MEDIA_FRAUD: 'bg-pink-100 text-pink-800',
  LOTTERY_SCAM: 'bg-green-100 text-green-800',
  ONLINE_SHOPPING_FRAUD: 'bg-indigo-100 text-indigo-800',
  IDENTITY_THEFT: 'bg-gray-200 text-gray-900',
};

const CATEGORY_LABELS = {
  UPI_FRAUD: 'UPI / Bank Fraud',
  VISHING: 'Vishing (Fake Call)',
  PHISHING: 'Phishing',
  INVESTMENT_SCAM: 'Investment Scam',
  SEXTORTION: 'Sextortion',
  JOB_FRAUD: 'Job / Task Fraud',
  OTP_SIM_SWAP: 'OTP / SIM Swap',
  SOCIAL_MEDIA_FRAUD: 'Social Media / Romance Scam',
  LOTTERY_SCAM: 'Lottery / Prize Scam',
  ONLINE_SHOPPING_FRAUD: 'Online Shopping Fraud',
  IDENTITY_THEFT: 'Identity Theft',
};

function formatValue(key, value) {
  if (value === 'true') return 'Yes';
  if (value === 'false') return 'No';
  if (key === 'incident_date') {
    try { return new Date(value).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }); }
    catch { return value; }
  }
  return value;
}

function SlotRow({ slotKey, value }) {
  const label = SLOT_LABELS[slotKey] || slotKey.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  const display = formatValue(slotKey, value);
  return (
    <div className="flex justify-between items-start py-2 border-b border-gray-100 last:border-0 gap-2">
      <span className="text-xs text-gray-500 flex-shrink-0 w-36">{label}</span>
      <span className="text-xs text-gray-800 font-medium text-right break-all">{display}</span>
    </div>
  );
}

function ComplaintSummary({ filledSlots, categoryId, onSubmit, isSubmitting, submissionResult }) {
  const [copied, setCopied] = useState(false);
  const [emailExpanded, setEmailExpanded] = useState(false);

  const handleCopy = useCallback((text) => {
    navigator.clipboard.writeText(text).catch(() => {});
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, []);

  const slotEntries = Object.entries(filledSlots || {}).filter(([, v]) => v != null && v !== '');

  return (
    <div className="bg-white rounded-lg shadow p-4 space-y-4">
      <h3 className="text-lg font-semibold text-gray-800">Complaint Summary</h3>

      {/* Category Badge */}
      {categoryId && (
        <span className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${CATEGORY_COLORS[categoryId] || 'bg-gray-100 text-gray-800'}`}>
          {CATEGORY_LABELS[categoryId] || categoryId}
        </span>
      )}

      {/* Key-Value Details */}
      <div className="max-h-64 overflow-y-auto pr-1">
        {slotEntries.length > 0 ? (
          slotEntries.map(([k, v]) => <SlotRow key={k} slotKey={k} value={v} />)
        ) : (
          <p className="text-sm text-gray-400 italic">No details collected yet.</p>
        )}
      </div>

      {/* Submit Button — shown only before submission */}
      {!submissionResult && (
        <div>
          <button
            onClick={onSubmit}
            disabled={isSubmitting}
            className="w-full py-2.5 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed transition-colors font-medium text-sm flex items-center justify-center gap-2"
          >
            {isSubmitting ? (
              <>
                <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                </svg>
                Submitting…
              </>
            ) : (
              '🚀 Submit Complaint'
            )}
          </button>
          <p className="text-xs text-gray-400 mt-1.5 text-center">
            Your complaint will be reviewed by NCRP authorities
          </p>
        </div>
      )}

      {/* ── Post-Submission Section ── */}
      {submissionResult && (
        <div className="space-y-3">
          {/* Success Banner */}
          <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-xs text-green-700 font-semibold uppercase tracking-wide mb-1">✅ Complaint Registered</p>
            <div className="flex items-center justify-between">
              <p className="text-base font-mono font-bold text-gray-900">{submissionResult.complaint_id}</p>
              <button
                onClick={() => handleCopy(submissionResult.complaint_id)}
                className="text-xs text-blue-600 hover:text-blue-800 font-medium px-2 py-1 border border-blue-200 rounded bg-white"
              >
                {copied ? '✓ Copied' : 'Copy ID'}
              </button>
            </div>
            {submissionResult.severity_score && (
              <p className="text-xs text-gray-500 mt-1">Severity Score: <span className="font-semibold text-orange-600">{submissionResult.severity_score}</span></p>
            )}
          </div>

          {/* Track Status Link */}
          <a
            href={`/track/${submissionResult.complaint_id}`}
            className="flex items-center justify-between w-full p-3 bg-blue-50 border border-blue-100 rounded-lg text-sm text-blue-700 font-medium hover:bg-blue-100 transition-colors"
          >
            <span>🔗 Track Complaint Status</span>
            <span>→</span>
          </a>

          {/* Email Preview Panel */}
          {submissionResult.email_preview && (
            <div className="border border-gray-200 rounded-lg overflow-hidden">
              <button
                onClick={() => setEmailExpanded(e => !e)}
                className="w-full flex items-center justify-between px-3 py-2 bg-gray-50 border-b border-gray-200 text-xs text-gray-600 font-medium hover:bg-gray-100"
              >
                <span>📧 Email Acknowledgement Preview</span>
                <span>{emailExpanded ? '▲' : '▼'}</span>
              </button>
              {emailExpanded && (
                <div className="p-3 bg-white text-xs space-y-1">
                  <div>
                    <span className="text-gray-400">To: </span>
                    <span className="text-gray-700">{submissionResult.email_preview.to || 'your registered email'}</span>
                  </div>
                  <div>
                    <span className="text-gray-400">Subject: </span>
                    <span className="text-gray-700 font-medium">{submissionResult.email_preview.subject}</span>
                  </div>
                  <div className="mt-2 bg-gray-50 rounded p-2 font-mono text-gray-700 whitespace-pre-wrap leading-relaxed">
                    {submissionResult.email_preview.body}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default ComplaintSummary;
