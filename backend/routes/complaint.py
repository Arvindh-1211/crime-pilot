"""Complaint routes for submission and retrieval."""
from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, List
import uuid

from utils.session_store import session_store
from core.complaint_builder import complaint_builder
from core.duplicate_checker import duplicate_checker

router = APIRouter()

# In-memory complaint storage
stored_complaints: Dict[str, Dict[str, Any]] = {}


@router.post("/complaint/submit")
async def submit_complaint(request: Dict[str, Any] = Body(...)):
    """Submit a completed complaint.

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

    # Verify session exists
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get filled slots from session
    filled_slots = session.get("filled_slots", {})
    category_id = session.get("category_id")

    # Build complaint
    complaint_id = generate_complaint_id()
    complaint_json = complaint_builder.build_complaint(session, complaint_id)

    # Compute severity score
    severity_score = complaint_builder.compute_severity(filled_slots, category_id)

    # Check for duplicates
    raw_description = session.get("raw_description", "")
    dup_result = duplicate_checker.check(phone_number, filled_slots, raw_description)

    if dup_result["is_duplicate"]:
        return {
            "complaint_id": complaint_id,
            "complaint_json": complaint_json,
            "severity_score": severity_score,
            "warning": f"Potential duplicate of complaint {dup_result['matched_complaint_id']} detected via {dup_result['method']} match"
        }

    # Register in duplicate checker
    duplicate_checker.register(phone_number, complaint_id, filled_slots, raw_description)

    # Store complaint
    complaint_json["complaint_id"] = complaint_id
    complaint_json["severity_score"] = severity_score
    stored_complaints[complaint_id] = complaint_json

    return {
        "complaint_id": complaint_id,
        "complaint_json": complaint_json,
        "severity_score": severity_score
    }


@router.get("/complaint/{complaint_id}")
async def get_complaint(complaint_id: str):
    """Retrieve a complaint by ID.

    Args:
        complaint_id: Complaint ID to retrieve

    Returns:
        Complaint detail including full JSON and severity score
    """
    if complaint_id not in stored_complaints:
        raise HTTPException(status_code=404, detail="Complaint not found")

    complaint = stored_complaints[complaint_id]

    return {
        "complaint_id": complaint.get("complaint_id"),
        "complaint_json": complaint,
        "severity_score": complaint.get("severity_score", 0)
    }


@router.get("/complaints")
async def list_complaints():
    """List all complaints (admin endpoint for testing)."""
    return {
        "complaints": list(stored_complaints.values()),
        "total": len(stored_complaints)
    }


def generate_complaint_id() -> str:
    """Generate a unique complaint ID in format CY-2025-{8 char UUID hex}."""
    # Generate 8 character UUID hex string
    uuid_hex = uuid.uuid4().hex[:8].upper()
    return f"CY-2025-{uuid_hex}"
