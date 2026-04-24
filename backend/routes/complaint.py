"""Complaint routes for submission and retrieval."""
from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any
import uuid

from utils.session_store import session_store
from core.complaint_builder import complaint_builder
from core.duplicate_checker import duplicate_checker
from core.complaint_store import complaint_store   # shared store

router = APIRouter()

# In-memory complaint storage
stored_complaints: Dict[str, Dict[str, Any]] = {}


def _seed_demo_complaints():
    """Populate stored_complaints with realistic demo data for the officer dashboard."""
    demos = [
        {
            "complaint_id": "CY-2025-DEMO0001",
            "ncrp_number": "CY-2025-DEMO0001",
            "complaint_category": "UPI_FRAUD",
            "complaint_category_label": "UPI / Payment Fraud",
            "date_filed": "2025-04-22T09:14:03",
            "status": "pending",
            "fir_number": None,
            "severity_score": 7.2,
            "phone_number": "9876543210",
            "user_location": "Mumbai",
            "assigned_station": "Mumbai Cyber Crime Police Station",
            "station_jurisdiction": "Mumbai Metropolitan Region",
            "fields": {
                "amount_lost": {"value": "45000", "label": "Amount Lost", "is_optional": False},
                "upi_transaction_id": {"value": "TXN2024041500123", "label": "UPI Transaction ID", "is_optional": False},
                "suspect_upi_id": {"value": "scammer@paytm", "label": "Suspect UPI ID", "is_optional": False},
                "incident_date": {"value": "2025-04-20", "label": "Incident Date", "is_optional": False},
            },
            "raw_description": "I received a call from someone posing as bank official and was tricked into transferring ₹45,000 via UPI.",
            "meta": {"source": "chat_assistant", "assistant_version": "1.0.0"},
        },
        {
            "complaint_id": "CY-2025-DEMO0002",
            "ncrp_number": "CY-2025-DEMO0002",
            "complaint_category": "PHISHING",
            "complaint_category_label": "Phishing / Email Fraud",
            "date_filed": "2025-04-21T14:30:55",
            "status": "accepted",
            "fir_number": "FIR-2025-MH-00421",
            "fir_assigned_at": "2025-04-21T16:00:00",
            "severity_score": 6.5,
            "phone_number": "9123456780",
            "user_location": "Pune",
            "assigned_station": "Pune Cyber Crime Cell",
            "station_jurisdiction": "Pune Division",
            "fields": {
                "phishing_url": {"value": "http://fake-sbi-login.xyz", "label": "Phishing URL", "is_optional": False},
                "data_compromised": {"value": "Credit card details", "label": "Data Compromised", "is_optional": False},
                "incident_date": {"value": "2025-04-19", "label": "Incident Date", "is_optional": False},
            },
            "raw_description": "Received a phishing email pretending to be SBI Bank. Clicked the link and entered card details before realising.",
            "meta": {"source": "chat_assistant", "assistant_version": "1.0.0"},
        },
        {
            "complaint_id": "CY-2025-DEMO0003",
            "ncrp_number": "CY-2025-DEMO0003",
            "complaint_category": "INVESTMENT_SCAM",
            "complaint_category_label": "Investment / Trading Scam",
            "date_filed": "2025-04-20T11:05:22",
            "status": "transferred",
            "fir_number": None,
            "severity_score": 8.8,
            "phone_number": "9988776655",
            "user_location": "Delhi",
            "assigned_station": "Delhi Cyber Crime Unit – Dwarka",
            "station_jurisdiction": "NCR Delhi Region",
            "fields": {
                "amount_invested": {"value": "250000", "label": "Amount Invested", "is_optional": False},
                "platform_name": {"value": "CryptoProfit365", "label": "Platform Name", "is_optional": False},
                "recruiter_contact": {"value": "+91-9000000001", "label": "Recruiter Contact", "is_optional": False},
                "incident_date": {"value": "2025-04-10", "label": "Incident Date", "is_optional": False},
            },
            "raw_description": "Lured into a fake crypto trading platform. Lost ₹2.5 lakh over 3 weeks before the platform vanished.",
            "meta": {"source": "chat_assistant", "assistant_version": "1.0.0"},
        },
        {
            "complaint_id": "CY-2025-DEMO0004",
            "ncrp_number": "CY-2025-DEMO0004",
            "complaint_category": "VISHING",
            "complaint_category_label": "Vishing / Phone Fraud",
            "date_filed": "2025-04-19T08:45:10",
            "status": "rejected",
            "fir_number": None,
            "severity_score": 5.0,
            "phone_number": "8765432190",
            "user_location": "Bengaluru",
            "assigned_station": "Bengaluru CID Cyber Crime Division",
            "station_jurisdiction": "Karnataka State",
            "fields": {
                "caller_number": {"value": "+91-8000000099", "label": "Caller Number", "is_optional": False},
                "otp_shared": {"value": "true", "label": "OTP Shared", "is_optional": False},
                "bank_name": {"value": "ICICI Bank", "label": "Bank Name", "is_optional": False},
                "incident_date": {"value": "2025-04-18", "label": "Incident Date", "is_optional": False},
            },
            "raw_description": "Got a call claiming to be from ICICI Bank KYC department. Shared OTP accidentally. No financial loss but account was accessed.",
            "meta": {"source": "chat_assistant", "assistant_version": "1.0.0"},
        },
        {
            "complaint_id": "CY-2025-DEMO0005",
            "ncrp_number": "CY-2025-DEMO0005",
            "complaint_category": "SEXTORTION",
            "complaint_category_label": "Sextortion / Blackmail",
            "date_filed": "2025-04-18T20:12:44",
            "status": "pending",
            "fir_number": None,
            "severity_score": 9.1,
            "phone_number": "7654321098",
            "user_location": "Hyderabad",
            "assigned_station": "Hyderabad Cyber Crime Police Station",
            "station_jurisdiction": "Telangana State",
            "fields": {
                "platform_used": {"value": "Instagram", "label": "Platform Used", "is_optional": False},
                "suspect_contact": {"value": "@fake_user_ig", "label": "Suspect Contact", "is_optional": False},
                "amount_demanded": {"value": "50000", "label": "Amount Demanded", "is_optional": False},
                "incident_date": {"value": "2025-04-15", "label": "Incident Date", "is_optional": False},
            },
            "raw_description": "Unknown person on Instagram is blackmailing me with morphed images and demanding ₹50,000.",
            "meta": {"source": "chat_assistant", "assistant_version": "1.0.0"},
        },
    ]
    for c in demos:
        stored_complaints[c["complaint_id"]] = c


# Seed on module load
_seed_demo_complaints()


@router.post("/complaint/submit")
async def submit_complaint(request: Dict[str, Any] = Body(...)):
    """Submit a completed complaint via the REST API (alternative to chat flow).

    Args:
        request: {session_id: str, phone_number: str}

    Returns:
        {complaint_id: str, complaint_json: dict, severity_score: float}
    """
    session_id = request.get("session_id", "")
    phone_number = request.get("phone_number", "")

    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID is required")

    if not phone_number:
        raise HTTPException(status_code=400, detail="Phone number is required")

    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    filled_slots = session.get("filled_slots", {})
    category_id = session.get("category_id")

    complaint_id = _generate_complaint_id()
    complaint_json = complaint_builder.build_complaint(session, complaint_id)
    severity_score = complaint_builder.compute_severity(filled_slots, category_id)

    raw_description = session.get("raw_description", "")
    dup_result = duplicate_checker.check(phone_number, filled_slots, raw_description)

    if dup_result["is_duplicate"]:
        return {
            "complaint_id": complaint_id,
            "complaint_json": complaint_json,
            "severity_score": severity_score,
            "warning": (
                f"Potential duplicate of complaint {dup_result['matched_complaint_id']} "
                f"detected via {dup_result['method']} match"
            ),
        }

    duplicate_checker.register(phone_number, complaint_id, filled_slots, raw_description)

    # Store complaint with tracking metadata
    complaint_json["complaint_id"] = complaint_id
    complaint_json["ncrp_number"] = complaint_id  # NCRP number is same as complaint_id
    complaint_json["severity_score"] = severity_score
    complaint_json["status"] = "pending"  # pending | accepted | rejected | transferred
    complaint_json["fir_number"] = None
    complaint_json["phone_number"] = phone_number

    # Location routing — assign to nearest cyber crime station
    user_location = filled_slots.get("location") or filled_slots.get("city") or filled_slots.get("state") or "Unknown"
    station = route_to_station(user_location)
    complaint_json["user_location"] = user_location
    complaint_json["assigned_station"] = station["name"]
    complaint_json["station_jurisdiction"] = station["jurisdiction"]

    stored_complaints[complaint_id] = complaint_json

    return {
        "complaint_id": complaint_id,
        "complaint_json": complaint_json,
        "severity_score": severity_score,
        "assigned_station": station["name"]
    }


@router.get("/complaint/{complaint_id}")
async def get_complaint(complaint_id: str):
    """Retrieve a complaint by ID."""
    complaint = complaint_store.get(complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    return {
        "complaint_id": complaint.get("complaint_id"),
        "complaint_json": complaint,
        "severity_score": complaint.get("severity_score", 0),
    }


@router.get("/complaints")
async def list_complaints():
    """List all stored complaints."""
    all_complaints = complaint_store.list_all()
    return {
        "complaints": all_complaints,
        "total": len(all_complaints),
    }


def _generate_complaint_id() -> str:
    """Generate a unique complaint ID in format CY-2025-{8 char UUID hex}."""
    # Generate 8 character UUID hex string
    uuid_hex = uuid.uuid4().hex[:8].upper()
    return f"CY-2025-{uuid_hex}"


# ── Location Routing ──────────────────────────────────────────────────────────

# Mapping of keywords → cyber crime police station
CYBER_STATIONS = [
    {"keywords": ["mumbai", "thane", "navi mumbai", "maharashtra"],
     "name": "Mumbai Cyber Crime Police Station",
     "jurisdiction": "Mumbai Metropolitan Region"},
    {"keywords": ["delhi", "new delhi", "noida", "gurgaon", "gurugram", "faridabad"],
     "name": "Delhi Cyber Crime Unit – Dwarka",
     "jurisdiction": "NCR Delhi Region"},
    {"keywords": ["bangalore", "bengaluru", "karnataka", "mysore"],
     "name": "Bengaluru CID Cyber Crime Division",
     "jurisdiction": "Karnataka State"},
    {"keywords": ["chennai", "tamil nadu", "coimbatore", "madurai"],
     "name": "Chennai Cyber Crime Cell – Egmore",
     "jurisdiction": "Tamil Nadu State"},
    {"keywords": ["hyderabad", "telangana", "secunderabad"],
     "name": "Hyderabad Cyber Crime Police Station",
     "jurisdiction": "Telangana State"},
    {"keywords": ["kolkata", "west bengal", "howrah"],
     "name": "Kolkata Cyber Crime Police Station – Lalbazar",
     "jurisdiction": "West Bengal State"},
    {"keywords": ["ahmedabad", "gujarat", "surat", "vadodara"],
     "name": "Gujarat CID Cyber Crime Cell",
     "jurisdiction": "Gujarat State"},
    {"keywords": ["pune", "nagpur"],
     "name": "Pune Cyber Crime Cell",
     "jurisdiction": "Pune Division"},
    {"keywords": ["lucknow", "uttar pradesh", "kanpur", "varanasi"],
     "name": "UP Cyber Crime Cell – Lucknow",
     "jurisdiction": "Uttar Pradesh State"},
    {"keywords": ["jaipur", "rajasthan", "jodhpur", "udaipur"],
     "name": "Rajasthan Cyber Crime Cell – Jaipur",
     "jurisdiction": "Rajasthan State"},
]


def route_to_station(location: str) -> dict:
    """Route a complaint to the nearest cyber crime police station based on location.

    Args:
        location: User-provided location string (city, state, etc.)

    Returns:
        dict with 'name' and 'jurisdiction' of the assigned station
    """
    if not location:
        return {"name": "Central Cyber Crime Coordination Centre (I4C)",
                "jurisdiction": "National – India"}

    location_lower = location.lower().strip()

    for station in CYBER_STATIONS:
        for kw in station["keywords"]:
            if kw in location_lower:
                return {"name": station["name"],
                        "jurisdiction": station["jurisdiction"]}

    # Fallback to national centre
    return {"name": "Central Cyber Crime Coordination Centre (I4C)",
            "jurisdiction": "National – India"}

