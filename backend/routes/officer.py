"""Officer dashboard routes for complaint tracking and management."""
from datetime import datetime
from fastapi import APIRouter, HTTPException, Body, Depends
from typing import Dict, Any

from .complaint import stored_complaints

router = APIRouter()

# ── Hardcoded officer credentials ─────────────────────────────────────────────
# In production this would come from a database + hashed passwords
OFFICERS = {
    "officer": {
        "password": "officer123",
        "name": "Inspector Raj Kumar",
        "badge": "CYB-1042",
        "station": "Central Cyber Crime Coordination Centre (I4C)",
    },
    "admin": {
        "password": "admin123",
        "name": "SP Arun Sharma",
        "badge": "CYB-0001",
        "station": "Central Cyber Crime Coordination Centre (I4C)",
    },
}


@router.post("/officer/login")
async def officer_login(request: Dict[str, str] = Body(...)):
    """Authenticate an officer and return profile info.

    Credentials:
        officer / officer123
        admin   / admin123
    """
    username = request.get("username", "").strip()
    password = request.get("password", "")

    officer = OFFICERS.get(username)
    if not officer or officer["password"] != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {
        "token": f"tok-{username}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "role": "officer",
        "name": officer["name"],
        "badge": officer["badge"],
        "station": officer["station"],
    }


# ── Dashboard endpoints ───────────────────────────────────────────────────────

@router.get("/officer/complaints")
async def get_all_complaints():
    """Return every complaint with its tracking metadata."""
    complaints = list(stored_complaints.values())
    # Sort by date_filed descending (newest first)
    complaints.sort(key=lambda c: c.get("date_filed", ""), reverse=True)

    # Compute summary metrics
    total = len(complaints)
    pending   = sum(1 for c in complaints if c.get("status") == "pending")
    accepted  = sum(1 for c in complaints if c.get("status") == "accepted")
    rejected  = sum(1 for c in complaints if c.get("status") == "rejected")
    transferred = sum(1 for c in complaints if c.get("status") == "transferred")

    return {
        "complaints": complaints,
        "metrics": {
            "total": total,
            "pending": pending,
            "accepted": accepted,
            "rejected": rejected,
            "transferred": transferred,
        },
    }


@router.get("/officer/complaints/{complaint_id}")
async def get_complaint_detail(complaint_id: str):
    """Get full detail of a single complaint."""
    if complaint_id not in stored_complaints:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return stored_complaints[complaint_id]


@router.put("/officer/complaints/{complaint_id}/status")
async def update_complaint_status(
    complaint_id: str,
    request: Dict[str, str] = Body(...),
):
    """Update a complaint's tracking status.

    Body: { "status": "accepted" | "rejected" | "transferred" }
    """
    status = request.get("status", "").lower()
    allowed = {"accepted", "rejected", "transferred"}
    if status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(allowed)}",
        )

    if complaint_id not in stored_complaints:
        raise HTTPException(status_code=404, detail="Complaint not found")

    stored_complaints[complaint_id]["status"] = status
    stored_complaints[complaint_id]["status_updated_at"] = datetime.now().isoformat()

    return {
        "message": f"Complaint {complaint_id} marked as {status}",
        "complaint": stored_complaints[complaint_id],
    }


@router.put("/officer/complaints/{complaint_id}/fir")
async def assign_fir_number(
    complaint_id: str,
    request: Dict[str, str] = Body(...),
):
    """Assign an FIR number to a complaint (does NOT close the ticket).

    Body: { "fir_number": "FIR-2025-XXXX" }
    """
    fir_number = request.get("fir_number", "").strip()
    if not fir_number:
        raise HTTPException(status_code=400, detail="FIR number is required")

    if complaint_id not in stored_complaints:
        raise HTTPException(status_code=404, detail="Complaint not found")

    stored_complaints[complaint_id]["fir_number"] = fir_number
    stored_complaints[complaint_id]["fir_assigned_at"] = datetime.now().isoformat()

    # Auto-accept if still pending
    if stored_complaints[complaint_id].get("status") == "pending":
        stored_complaints[complaint_id]["status"] = "accepted"
        stored_complaints[complaint_id]["status_updated_at"] = datetime.now().isoformat()

    return {
        "message": f"FIR {fir_number} assigned to complaint {complaint_id}",
        "complaint": stored_complaints[complaint_id],
    }


@router.put("/officer/complaints/{complaint_id}/transfer")
async def transfer_complaint(
    complaint_id: str,
    request: Dict[str, str] = Body(...),
):
    """Transfer a complaint to another station.

    Body: { "target_station": "Station Name" }
    """
    target_station = request.get("target_station", "").strip()
    if not target_station:
        raise HTTPException(status_code=400, detail="Target station is required")

    if complaint_id not in stored_complaints:
        raise HTTPException(status_code=404, detail="Complaint not found")

    stored_complaints[complaint_id]["status"] = "transferred"
    stored_complaints[complaint_id]["assigned_station"] = target_station
    stored_complaints[complaint_id]["transferred_at"] = datetime.now().isoformat()

    return {
        "message": f"Complaint {complaint_id} transferred to {target_station}",
        "complaint": stored_complaints[complaint_id],
    }
