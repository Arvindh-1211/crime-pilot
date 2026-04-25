"""Officer dashboard routes — JWT auth, complaint management, audit trail, admin metrics."""
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Body, Depends

from core.complaint_store import complaint_store
from core.auth import OFFICER_DB, verify_password, create_token, get_current_officer, require_admin
from core.audit_log import audit_log

router = APIRouter()

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

@router.post("/officer/login")
async def officer_login(request: Dict[str, str] = Body(...)):
    """Authenticate an officer and return a signed JWT.

    Roles: OFFICER | ADMIN_OFFICER
    Credentials (dev):
        officer  / officer123
        admin    / admin123
        officer2 / officer456
    """
    username = request.get("username", "").strip().lower()
    password = request.get("password", "")

    officer = OFFICER_DB.get(username)
    if not officer or not verify_password(password, officer["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token(username, officer)
    return {
        "token": token,
        "role": officer["role"],
        "name": officer["name"],
        "badge": officer["badge"],
        "station": officer["station"],
        "username": username,
    }


@router.post("/officer/logout")
async def officer_logout(officer: Dict = Depends(get_current_officer)):
    """Acknowledge logout (client must discard the token)."""
    audit_log.record(
        officer_username=officer["sub"],
        officer_badge=officer["badge"],
        complaint_id="—",
        action="LOGOUT",
        notes="Officer logged out.",
    )
    return {"message": "Logged out successfully."}


# ---------------------------------------------------------------------------
# Complaints — Read
# ---------------------------------------------------------------------------

@router.get("/officer/complaints")
async def get_all_complaints(officer: Dict = Depends(get_current_officer)):
    """Return complaints with metrics. Station filter applied for OFFICER role."""
    complaints = complaint_store.list_all()
    complaints.sort(key=lambda c: c.get("date_filed", ""), reverse=True)

    # OFFICER sees only their station's complaints; ADMIN sees all
    if officer.get("role") == "OFFICER":
        station = officer.get("station", "")
        complaints = [c for c in complaints if c.get("assigned_station", "") == station or c.get("original_station", "") == station]

    total        = len(complaints)
    pending      = sum(1 for c in complaints if c.get("status") == "pending")
    accepted     = sum(1 for c in complaints if c.get("status") == "accepted")
    rejected     = sum(1 for c in complaints if c.get("status") == "rejected")
    transferred  = sum(1 for c in complaints if c.get("status") == "transferred")
    fir_assigned = sum(1 for c in complaints if c.get("fir_number"))

    # Fraud type breakdown
    fraud_counts: Dict[str, int] = {}
    for c in complaints:
        cat = c.get("complaint_category_label") or c.get("complaint_category") or "Unknown"
        fraud_counts[cat] = fraud_counts.get(cat, 0) + 1

    return {
        "complaints": complaints,
        "metrics": {
            "total": total,
            "pending": pending,
            "accepted": accepted,
            "rejected": rejected,
            "transferred": transferred,
            "fir_assigned": fir_assigned,
            "fraud_type_breakdown": fraud_counts,
        },
    }


@router.get("/officer/complaints/{complaint_id}")
async def get_complaint_detail(complaint_id: str, officer: Dict = Depends(get_current_officer)):
    """Full complaint dossier including audit trail."""
    complaint = complaint_store.get(complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    audit = audit_log.get_for_complaint(complaint_id)
    return {**complaint, "audit_trail": audit}


# ---------------------------------------------------------------------------
# Complaints — Actions
# ---------------------------------------------------------------------------

@router.put("/officer/complaints/{complaint_id}/accept")
async def accept_complaint(
    complaint_id: str,
    officer: Dict = Depends(get_current_officer),
):
    """Accept a complaint (without FIR — just status change)."""
    complaint = complaint_store.get(complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    complaint["status"] = "accepted"
    complaint["status_updated_at"] = datetime.utcnow().isoformat() + "Z"
    complaint_store.save(complaint_id, complaint)

    audit_log.record(
        officer_username=officer["sub"],
        officer_badge=officer["badge"],
        complaint_id=complaint_id,
        action="ACCEPTED",
        notes="Complaint accepted for investigation.",
    )
    return {"message": f"Complaint {complaint_id} accepted.", "complaint": complaint}


@router.put("/officer/complaints/{complaint_id}/reject")
async def reject_complaint(
    complaint_id: str,
    request: Dict[str, str] = Body(...),
    officer: Dict = Depends(get_current_officer),
):
    """Reject a complaint with a mandatory reason.

    Body: { "reason": "Outside jurisdiction / Duplicate / No cognizable offence" }
    """
    reason = request.get("reason", "").strip()
    if not reason:
        raise HTTPException(status_code=400, detail="Rejection reason is required.")

    complaint = complaint_store.get(complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    complaint["status"] = "rejected"
    complaint["rejection_reason"] = reason
    complaint["status_updated_at"] = datetime.utcnow().isoformat() + "Z"
    complaint_store.save(complaint_id, complaint)

    audit_log.record(
        officer_username=officer["sub"],
        officer_badge=officer["badge"],
        complaint_id=complaint_id,
        action="REJECTED",
        notes=f"Reason: {reason}",
    )
    return {"message": f"Complaint {complaint_id} rejected.", "complaint": complaint}


@router.put("/officer/complaints/{complaint_id}/fir")
async def assign_fir_number(
    complaint_id: str,
    request: Dict[str, str] = Body(...),
    officer: Dict = Depends(get_current_officer),
):
    """Assign an FIR number — status → 'FIR Assigned', then 'Under Investigation'.

    Body: { "fir_number": "FIR-2025-MH-04821" }
    """
    fir_number = request.get("fir_number", "").strip()
    if not fir_number:
        raise HTTPException(status_code=400, detail="FIR number is required.")

    complaint = complaint_store.get(complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    complaint["fir_number"] = fir_number
    complaint["fir_assigned_at"] = datetime.utcnow().isoformat() + "Z"
    complaint["status"] = "fir_assigned"
    complaint["status_updated_at"] = datetime.utcnow().isoformat() + "Z"
    complaint_store.save(complaint_id, complaint)

    audit_log.record(
        officer_username=officer["sub"],
        officer_badge=officer["badge"],
        complaint_id=complaint_id,
        action="FIR_ASSIGNED",
        notes=f"FIR number: {fir_number}",
    )
    return {"message": f"FIR {fir_number} assigned to {complaint_id}.", "complaint": complaint}


@router.put("/officer/complaints/{complaint_id}/transfer")
async def transfer_complaint(
    complaint_id: str,
    request: Dict[str, str] = Body(...),
    officer: Dict = Depends(get_current_officer),
):
    """Transfer complaint to another station.

    Body: { "target_station": "Station Name", "notes": "Optional transfer notes" }
    """
    target_station = request.get("target_station", "").strip()
    notes = request.get("notes", "").strip()
    if not target_station:
        raise HTTPException(status_code=400, detail="Target station is required.")

    complaint = complaint_store.get(complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    # Keep original station for audit
    complaint["original_station"] = complaint.get("assigned_station", "")
    complaint["status"] = "transferred"
    complaint["assigned_station"] = target_station
    complaint["transfer_notes"] = notes
    complaint["transferred_at"] = datetime.utcnow().isoformat() + "Z"
    complaint_store.save(complaint_id, complaint)

    audit_log.record(
        officer_username=officer["sub"],
        officer_badge=officer["badge"],
        complaint_id=complaint_id,
        action="TRANSFERRED",
        notes=f"Transferred to: {target_station}. {notes}".strip(),
    )
    return {"message": f"Complaint {complaint_id} transferred to {target_station}.", "complaint": complaint}


# ---------------------------------------------------------------------------
# Audit Trail
# ---------------------------------------------------------------------------

@router.get("/officer/audit")
async def get_audit_log(officer: Dict = Depends(get_current_officer)):
    """Full audit log (admin only)."""
    require_admin(officer)
    return {"entries": audit_log.get_all()}


@router.get("/officer/audit/{complaint_id}")
async def get_complaint_audit(complaint_id: str, officer: Dict = Depends(get_current_officer)):
    """Audit trail for a specific complaint."""
    return {"entries": audit_log.get_for_complaint(complaint_id)}


# ---------------------------------------------------------------------------
# Admin Metrics
# ---------------------------------------------------------------------------

@router.get("/officer/admin/metrics")
async def admin_metrics(officer: Dict = Depends(get_current_officer)):
    """Aggregate metrics across all complaints (admin only)."""
    require_admin(officer)

    complaints = complaint_store.list_all()

    # By station
    by_station: Dict[str, Dict[str, int]] = {}
    for c in complaints:
        station = c.get("assigned_station") or c.get("original_station") or "Unknown"
        if station not in by_station:
            by_station[station] = {"total": 0, "pending": 0, "accepted": 0, "rejected": 0, "transferred": 0, "fir_assigned": 0}
        by_station[station]["total"] += 1
        status = c.get("status", "pending")
        if status in by_station[station]:
            by_station[station][status] += 1
        if c.get("fir_number"):
            by_station[station]["fir_assigned"] += 1

    # By fraud type
    by_fraud: Dict[str, int] = {}
    for c in complaints:
        cat = c.get("complaint_category_label") or c.get("complaint_category") or "Unknown"
        by_fraud[cat] = by_fraud.get(cat, 0) + 1

    # By date (last 30 days, daily)
    from collections import defaultdict
    by_date: Dict[str, int] = defaultdict(int)
    for c in complaints:
        df = c.get("date_filed", "")
        if df:
            day = df[:10]  # YYYY-MM-DD
            by_date[day] += 1

    # Action summary from audit log
    action_summary = audit_log.get_summary()

    return {
        "total_complaints": len(complaints),
        "by_station": by_station,
        "by_fraud_type": by_fraud,
        "by_date": dict(sorted(by_date.items())),
        "action_summary": action_summary,
    }


# ---------------------------------------------------------------------------
# Legacy endpoints — kept for backward compatibility (re-route to new ones)
# ---------------------------------------------------------------------------

@router.put("/officer/complaints/{complaint_id}/status")
async def update_complaint_status_legacy(
    complaint_id: str,
    request: Dict[str, str] = Body(...),
    officer: Dict = Depends(get_current_officer),
):
    """Legacy status update — route to new specific endpoints."""
    status = request.get("status", "").lower()
    if status == "accepted":
        return await accept_complaint(complaint_id, officer)
    elif status == "rejected":
        reason = request.get("reason", "No reason provided.")
        return await reject_complaint(complaint_id, {"reason": reason}, officer)
    elif status == "transferred":
        target = request.get("target_station", "")
        return await transfer_complaint(complaint_id, {"target_station": target}, officer)
    raise HTTPException(status_code=400, detail="Invalid status.")
