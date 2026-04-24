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
        "INVESTMENT_SCAM": 8.0,
        "VISHING": 7.0,
        "UPI_FRAUD": 6.5,
        "PHISHING": 6.0
    }

    # Slot labels for display
    SLOT_LABELS = {
        "incident_date": "Incident Date",
        "amount_lost": "Amount Lost",
        "upi_transaction_id": "UPI Transaction ID",
        "suspect_upi_id": "Suspect UPI ID",
        "platform": "Platform",
        "caller_number": "Caller Number",
        "bank_name": "Bank Name",
        "call_recording": "Call Recording Available",
        "otp_shared": "OTP Shared",
        "phishing_url": "Phishing URL",
        "data_compromised": "Data Compromised",
        "email_screenshot": "Email Screenshot Available",
        "bank_involved": "Bank Involved",
        "amount_invested": "Amount Invested",
        "platform_name": "Platform Name",
        "recruiter_contact": "Recruiter Contact",
        "payment_proof": "Payment Proof Available",
        "platform_used": "Platform Used",
        "suspect_contact": "Suspect Contact",
        "screenshot_available": "Screenshot Available",
        "amount_demanded": "Amount Demanded",
        "utr_number": "UTR Number",
        "screenshot": "Screenshot Available"
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
        """Build the complete complaint JSON structure.

        Args:
            session_data: Session data including filled_slots, category_id, etc.
            complaint_id: Generated complaint ID

        Returns:
            Complete complaint JSON dictionary
        """
        self._load_categories()

        # Extract session data
        filled_slots = session_data.get("filled_slots", {})
        category_id = session_data.get("category_id")
        raw_description = session_data.get("raw_description", "")

        # Build complaint structure
        complaint = {
            "complaint_id": complaint_id,
            "complaint_category": category_id,
            "complaint_category_label": self._get_category_label(category_id),
            "date_filed": datetime.now().isoformat(),
            "status": "pending",
            "fields": {},
            "meta": {
                "source": "chat_assistant",
                "assistant_version": "1.0.0"
            }
        }

        # Add category-specific fields
        if category_id and category_id in self._categories:
            category = self._categories[category_id]
            mandatory = category.get("mandatory_slots", [])
            optional = category.get("optional_slots", [])

            # Add all filled slots to fields
            for slot in mandatory + optional:
                if slot in filled_slots and filled_slots[slot] is not None:
                    complaint["fields"][slot] = {
                        "value": filled_slots[slot],
                        "label": self.SLOT_LABELS.get(slot, slot),
                        "is_optional": slot not in mandatory
                    }

        # Add raw description
        if raw_description:
            complaint["raw_description"] = raw_description

        # Add optional evidence
        complaint["optional_evidence"] = {
            "has_screenshot": filled_slots.get("screenshot") == "true" or filled_slots.get("email_screenshot") == "true" or filled_slots.get("screenshot_available") == "true",
            "has_call_recording": filled_slots.get("call_recording") == "true",
            "has_payment_proof": filled_slots.get("payment_proof") == "true"
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
