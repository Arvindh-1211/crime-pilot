"""Complaint routes for submission and retrieval."""
from fastapi import APIRouter, HTTPException, Body, BackgroundTasks
from typing import Dict, Any
import uuid
import asyncio

from utils.session_store import session_store
from core.complaint_builder import complaint_builder
from core.duplicate_checker import duplicate_checker
from core.complaint_store import complaint_store   # shared store
from utils.email_sender import send_email
from routes.upload import get_evidence_by_session

router = APIRouter()




@router.post("/complaint/submit")
async def submit_complaint(request: Dict[str, Any] = Body(...), background_tasks: BackgroundTasks = None):


    """Submit a completed complaint via the REST API.

    Args:
        request: {session_id, phone_number, email (optional)}

    Returns:
        {complaint_id, complaint_json, severity_score, tracking_url, email_preview}
    """
    session_id = request.get("session_id", "")
    # Contact details are now passed directly from the frontend form
    phone_number = request.get("phone_number", "")
    email = request.get("email", "")
    name = request.get("name", "the complainant")
    incident_datetime = request.get("incident_datetime", "")
    location = request.get("location", "")

    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID is required")

    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    filled_slots = session.get("filled_slots", {})
    category_id = session.get("category_id")

    # Manually inject the form data into filled_slots for the complaint builder
    filled_slots["victim_name"] = name
    filled_slots["victim_phone"] = phone_number
    filled_slots["victim_email"] = email
    filled_slots["incident_location"] = location
    filled_slots["incident_datetime"] = incident_datetime

    complaint_id = _generate_complaint_id()
    complaint_json = complaint_builder.build_complaint(session, complaint_id)
    
    # Link any evidence uploaded during this session
    evidence_meta = get_evidence_by_session(session_id)
    if evidence_meta:
        complaint_json["evidence_files"] = [
            {k: v for k, v in m.items() if k != "disk_name"}
            for m in evidence_meta
        ]
        
    severity_score = complaint_builder.compute_severity(filled_slots, category_id)

    raw_description = session.get("raw_description", "")
    
    # Run duplicate check in thread to avoid blocking the event loop
    try:
        dup_result = await asyncio.to_thread(duplicate_checker.check, phone_number, filled_slots, raw_description)
    except Exception as e:
        print(f"Duplicate check failed: {e}")
        dup_result = {"is_duplicate": False}

    duplicate_warning = None
    if dup_result.get("is_duplicate"):
        duplicate_warning = (
            f"Potential duplicate of complaint {dup_result['matched_complaint_id']} "
            f"detected via {dup_result['method']} match"
        )

    # Register in background to speed up response
    background_tasks.add_task(duplicate_checker.register, phone_number, complaint_id, filled_slots, raw_description)

    complaint_json["complaint_id"] = complaint_id
    complaint_json["ncrp_number"] = complaint_id
    complaint_json["severity_score"] = severity_score
    complaint_json["status"] = "pending"
    complaint_json["fir_number"] = None
    complaint_json["phone_number"] = phone_number
    complaint_json["victim_name"] = name
    complaint_json["victim_email"] = email

    # Location routing
    user_location = (
        filled_slots.get("incident_location")
        or filled_slots.get("location")
        or filled_slots.get("city")
        or "Unknown"
    )
    station = route_to_station(user_location)
    complaint_json["user_location"] = user_location
    complaint_json["assigned_station"] = station["name"]
    complaint_json["station_jurisdiction"] = station["jurisdiction"]

    complaint_store.save(complaint_id, complaint_json)

    from core.complaint_store import complaint_store as shared_store
    shared_store.save(complaint_id, complaint_json)

    # Generate tracking URL and email preview
    tracking_url = f"http://localhost:5173/track/{complaint_id}"
    from datetime import datetime
    date_filed = datetime.now().strftime("%d %B %Y, %I:%M %p")
    category_label = complaint_json.get("complaint_category_label", category_id or "Unknown")

    email_preview = {
        "to": email,
        "subject": f"NCRP Complaint Registered — {complaint_id}",
        "body": (
            f"Dear {name},\n\n"
            f"Your cybercrime complaint has been successfully registered on the National Cybercrime Reporting Portal.\n\n"
            f"Complaint ID   : {complaint_id}\n"
            f"Complaint Type : {category_label}\n"
            f"Date Filed     : {date_filed}\n"
            f"Assigned To    : {station['name']}\n\n"
            f"Track your complaint at:\n{tracking_url}\n\n"
            f"Please save your Complaint ID — you will need it to follow up.\n"
            f"National Cybercrime Helpline: 1930\n\n"
            f"Regards,\nNational Cybercrime Reporting Portal (NCRP)\ncybercrime.gov.in"
        )
    }

    # Dispatch email in background
    if email:
        background_tasks.add_task(send_email, email_preview["to"], email_preview["subject"], email_preview["body"])

    result = {
        "complaint_id": complaint_id,
        "complaint_json": complaint_json,
        "severity_score": severity_score,
        "assigned_station": station["name"],
        "tracking_url": tracking_url,
        "email_preview": email_preview,
    }
    if duplicate_warning:
        result["warning"] = duplicate_warning
    return result


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

