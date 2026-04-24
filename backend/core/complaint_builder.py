"""Complaint Builder for constructing final complaint JSON."""
import os
import json
import math
from datetime import datetime
from typing import Dict, Any, Optional
import uuid


class ComplaintBuilder:
    """Builds final complaint JSON from session data."""

    # Base scores for each category
    CATEGORY_BASE_SCORES = {
        "SEXTORTION": 9.0,
        "IDENTITY_THEFT": 8.5,
        "INVESTMENT_SCAM": 8.0,
        "OTP_SIM_SWAP": 7.5,
        "VISHING": 7.0,
        "UPI_FRAUD": 6.5,
        "PHISHING": 6.0,
        "JOB_FRAUD": 6.0,
        "SOCIAL_MEDIA_FRAUD": 5.5,
        "ONLINE_SHOPPING_FRAUD": 5.0,
        "LOTTERY_SCAM": 5.0,
    }

    # Slot labels for display (used by officer dashboard)
    SLOT_LABELS = {
        # Universal
        "victim_name": "Complainant Name",
        "victim_phone": "Contact Phone",
        "victim_email": "Email Address",
        "incident_date": "Incident Date",
        "incident_time": "Incident Time",
        "incident_location": "City / State",
        # UPI
        "amount_lost": "Amount Lost (₹)",
        "upi_transaction_id": "UPI Transaction ID",
        "suspect_upi_id": "Suspect UPI ID",
        "platform": "UPI App Used",
        "utr_number": "UTR Number",
        "bank_name_victim": "Your Bank",
        "account_number_victim": "Your Account Number",
        "screenshot": "Screenshot Available",
        # Vishing
        "caller_number": "Caller Phone Number",
        "caller_claimed_to_be": "Caller Claimed To Be",
        "otp_shared": "OTP / PIN Shared",
        "call_recording": "Call Recording Available",
        "bank_name": "Bank Claimed",
        "remote_app_installed": "Remote App Installed",
        # Phishing
        "phishing_url": "Phishing URL",
        "data_compromised": "Data Compromised",
        "email_screenshot": "Email/Message Screenshot",
        "bank_involved": "Bank Targeted",
        "account_compromised": "Account Accessed",
        # Investment
        "amount_invested": "Amount Invested (₹)",
        "platform_name": "Investment Platform",
        "recruiter_contact": "Recruiter Contact",
        "payment_mode": "Payment Mode",
        "payment_proof": "Payment Proof Available",
        "withdrawal_blocked": "Withdrawal Blocked",
        # Sextortion
        "platform_used": "Platform Used by Suspect",
        "suspect_contact": "Suspect Contact / ID",
        "amount_paid": "Amount Already Paid (₹)",
        "blackmail_method": "Blackmail Method",
        "screenshot_available": "Screenshots Available",
        "amount_demanded": "Amount Demanded (₹)",
        "content_recorded": "Content Was Recorded",
        # Job Fraud
        "job_platform": "Job/Task Platform",
        "task_description": "Tasks Assigned",
        "deposit_paid": "Deposit / Fee Paid (₹)",
        "recruiter_contact_job": "Recruiter / HR Contact",
        "job_offer_screenshot": "Job Offer Screenshot",
        "app_used_for_tasks": "Task App Used",
        "website_url": "Scam Website URL",
        # SIM Swap
        "sim_stopped_working": "SIM Stopped Working",
        "service_hijacked": "Service Hijacked",
        "amount_lost_sim": "Amount Lost (₹)",
        "bank_name_sim": "Bank Account Drained",
        "transaction_sms": "Transaction SMS Available",
        "telecom_operator": "Telecom Operator",
        # Social Media / Romance
        "social_platform": "Social Platform",
        "fake_profile_id": "Fake Profile ID / Name",
        "romance_money_sent": "Money Sent to Suspect (₹)",
        "how_long_known": "Duration of Contact",
        "profile_screenshot": "Profile Screenshot",
        "chat_screenshot": "Chat Screenshot",
        "amount_total_sent": "Total Amount Sent (₹)",
        # Lottery
        "lottery_prize_claimed": "Prize Claimed",
        "processing_fee_paid": "Processing Fee Paid (₹)",
        "contact_channel": "Contact Channel",
        "sender_contact": "Sender Contact",
        "lottery_message_screenshot": "Lottery Message Screenshot",
        "bank_used_for_payment": "Bank Used for Fee Payment",
        # Shopping
        "shopping_website": "Shopping Website / Platform",
        "order_id": "Order ID",
        "product_not_received": "Product Ordered",
        "amount_paid_shopping": "Amount Paid (₹)",
        "order_screenshot": "Order Screenshot",
        "seller_contact": "Seller Contact",
        "delivery_status": "Delivery Status",
        # Identity Theft
        "identity_misused": "Type of Identity Misuse",
        "how_discovered": "How Discovered",
        "loan_amount": "Fraudulent Loan Amount (₹)",
        "financial_institution": "Financial Institution",
        "aadhaar_misused": "Aadhaar Misused",
        "pan_misused": "PAN Misused",
        "credit_score_affected": "Credit Score Affected",
    }

    def __init__(self):
        """Initialize the complaint builder."""
        self._loaded_categories = False
        self._categories = {}

    def _load_categories(self):
        """Load category definitions."""
        if self._loaded_categories:
            return

        taxonomy_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data", "fraud_taxonomy.json"
        )
        try:
            with open(taxonomy_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._categories = {cat["id"]: cat for cat in data["categories"]}
                self._loaded_categories = True
        except Exception:
            self._categories = {}

    def build_complaint(self, session_data: Dict[str, Any], complaint_id: str) -> Dict[str, Any]:
        """Build the complete complaint JSON structure."""
        self._load_categories()

        filled_slots = session_data.get("filled_slots", {})
        category_id = session_data.get("category_id")
        raw_description = session_data.get("raw_description", "")

        # Extract universal contact fields
        victim_name = filled_slots.get("victim_name", "")
        victim_phone = filled_slots.get("victim_phone", "")
        victim_email = filled_slots.get("victim_email", "")
        incident_location = filled_slots.get("incident_location", "")

        complaint = {
            "complaint_id": complaint_id,
            "ncrp_number": complaint_id,
            "complaint_category": category_id,
            "complaint_category_label": self._get_category_label(category_id),
            "date_filed": datetime.now().isoformat(),
            "status": "pending",
            "victim_name": victim_name,
            "victim_phone": victim_phone,
            "victim_email": victim_email,
            "user_location": incident_location,
            "fields": {},
            "meta": {
                "source": "chat_assistant",
                "assistant_version": "2.0.0"
            }
        }

        # Add all filled slots to fields
        universal = {"victim_name", "victim_phone", "victim_email",
                     "incident_date", "incident_time", "incident_location"}
        if category_id and category_id in self._categories:
            category = self._categories[category_id]
            mandatory = category.get("mandatory_slots", [])
            optional = category.get("optional_slots", [])
            all_slots = list(universal) + mandatory + optional
        else:
            all_slots = list(universal) + list(filled_slots.keys())
            mandatory = []

        for slot in all_slots:
            if slot in filled_slots and filled_slots[slot] is not None:
                complaint["fields"][slot] = {
                    "value": filled_slots[slot],
                    "label": self.SLOT_LABELS.get(slot, slot.replace("_", " ").title()),
                    "is_optional": slot not in mandatory and slot not in universal,
                }

        if raw_description:
            complaint["raw_description"] = raw_description

        complaint["optional_evidence"] = {
            "has_screenshot": any(
                filled_slots.get(s) == "true"
                for s in ["screenshot", "email_screenshot", "screenshot_available",
                           "job_offer_screenshot", "order_screenshot", "lottery_message_screenshot"]
            ),
            "has_call_recording": filled_slots.get("call_recording") == "true",
            "has_payment_proof": filled_slots.get("payment_proof") == "true",
        }

        return complaint

    def compute_severity(self, filled_slots: Dict[str, Any], category_id: Optional[str]) -> float:
        """Compute severity score for the complaint.

        Formula:
        - base = CATEGORY_BASE_SCORES[category] or 5.0
        - amount_score = min(log10(amount + 1), 10) if amount available
        - evidence_score = (optional_filled / total_optional * 10) or 5
        - severity = (amount_score + evidence_score + base) / 3

        Args:
            filled_slots: All filled slot values
            category_id: Detected fraud category

        Returns:
            Severity score rounded to 1 decimal (0-10)
        """
        # Get base score
        base = self.CATEGORY_BASE_SCORES.get(category_id, 5.0)

        # Calculate amount score
        amount_score = 0
        amount = None

        # Try to get amount from various slot names
        for slot_name in ["amount_lost", "amount_invested", "amount_demanded"]:
            if slot_name in filled_slots:
                try:
                    amount = int(filled_slots[slot_name])
                    break
                except (ValueError, TypeError):
                    continue

        if amount and amount > 0:
            amount_score = min(math.log10(amount + 1), 10)
        else:
            amount_score = 0

        # Calculate evidence score
        evidence_score = 0

        # Count optional slots and how many are filled
        optional_slots = []
        if category_id and category_id in self._categories:
            category = self._categories[category_id]
            optional_slots = category.get("optional_slots", [])

        if optional_slots:
            total_optional = len(optional_slots)
            filled_optional = sum(1 for slot in optional_slots
                                  if slot in filled_slots and filled_slots[slot] is not None)
            evidence_score = (filled_optional / total_optional) * 10
        else:
            # Default evidence score if we can't determine
            evidence_score = 5

        # Calculate final severity
        severity = (amount_score + evidence_score + base) / 3

        return round(severity, 1)

    def _get_category_label(self, category_id: Optional[str]) -> str:
        """Get display label for category."""
        if not category_id:
            return "Unknown"

        self._load_categories()

        if category_id in self._categories:
            return self._categories[category_id].get("label", category_id)

        return category_id

    def get_severity_color(self, severity: float) -> str:
        """Get color for severity score."""
        if severity > 7:
            return "red"
        elif severity >= 5:
            return "orange"
        else:
            return "green"


# Global builder instance
complaint_builder = ComplaintBuilder()
