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

    complaint_json["complaint_id"] = complaint_id
    complaint_json["severity_score"] = severity_score
    complaint_store.save(complaint_id, complaint_json)

    return {
        "complaint_id": complaint_id,
        "complaint_json": complaint_json,
        "severity_score": severity_score,
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
    return f"CY-2025-{uuid.uuid4().hex[:8].upper()}"
