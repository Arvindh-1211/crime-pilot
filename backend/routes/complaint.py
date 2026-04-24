"""Complaint routes for submission and retrieval."""
from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any
import uuid

from utils.session_store import session_store
from core.complaint_builder import complaint_builder
from core.duplicate_checker import duplicate_checker
from core.complaint_store import complaint_store   # shared store

router = APIRouter()




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

    complaint_store.save(complaint_id, complaint_json)

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

@router.get("/complaint/{complaint_id}/status")
async def get_complaint_status(complaint_id: str):
    """Public endpoint to check complaint status by ID only (no login)."""
    complaint = complaint_store.get(complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Tracking ID not found")
        
    # Return only non-sensitive public tracking data
    return {
        "complaint_id": complaint.get("complaint_id"),
        "status": complaint.get("status", "pending"),
        "assigned_station": complaint.get("assigned_station"),
        "date_filed": complaint.get("date_filed"),
        "fir_number": complaint.get("fir_number"),
        "last_updated": complaint.get("status_updated_at") or complaint.get("date_filed"),
        "severity": complaint.get("severity_score")
    }

