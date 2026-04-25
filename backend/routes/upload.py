"""Evidence upload routes — saves files to disk and links them to complaints."""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from datetime import datetime
from typing import Dict, Any, Optional
import uuid
import os

from core.complaint_store import complaint_store

router = APIRouter()

# Directory where evidence is saved on disk
EVIDENCE_DIR = os.path.join(os.path.dirname(__file__), "..", "evidence_store")
os.makedirs(EVIDENCE_DIR, exist_ok=True)

# In-memory index: file_id → metadata
_evidence_index: Dict[str, Dict[str, Any]] = {}


@router.post("/upload/evidence")
async def upload_evidence(
    session_id: str = Form(...),
    complaint_id: Optional[str] = Form(None),
    file: UploadFile = File(...),
):
    """Upload evidence file (JPG, PNG, PDF, max 10MB).

    Saves to disk and links the file metadata into the complaint record.
    """
    ALLOWED = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
    if file.content_type not in ALLOWED:
        raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {', '.join(ALLOWED)}")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large. Max 10 MB per file.")

    file_id = f"FILE-{uuid.uuid4().hex[:10].upper()}"
    ext = os.path.splitext(file.filename or "upload")[1] or ".bin"
    disk_name = f"{file_id}{ext}"
    disk_path = os.path.join(EVIDENCE_DIR, disk_name)

    with open(disk_path, "wb") as f:
        f.write(content)

    now = datetime.utcnow().isoformat() + "Z"
    meta = {
        "file_id":   file_id,
        "file_name": file.filename,
        "file_type": file.content_type,
        "file_size": len(content),
        "disk_name": disk_name,
        "session_id": session_id,
        "complaint_id": complaint_id,
        "uploaded_at": now,
    }
    _evidence_index[file_id] = meta

    # Link to complaint if ID is provided
    if complaint_id:
        complaint = complaint_store.get(complaint_id)
        if complaint is not None:
            files = complaint.get("evidence_files", [])
            files.append({k: v for k, v in meta.items() if k != "disk_name"})
            complaint["evidence_files"] = files
            complaint_store.save(complaint_id, complaint)

    return {"file_id": file_id, "file_name": file.filename, "file_type": file.content_type, "uploaded_at": now}


@router.get("/upload/evidence/{file_id}")
async def serve_evidence(file_id: str):
    """Serve an evidence file by ID (for inline preview in Officer Dashboard)."""
    meta = _evidence_index.get(file_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Evidence not found")
    disk_path = os.path.join(EVIDENCE_DIR, meta["disk_name"])
    if not os.path.exists(disk_path):
        raise HTTPException(status_code=404, detail="File missing from disk")
    return FileResponse(disk_path, media_type=meta["file_type"], filename=meta["file_name"])


@router.delete("/upload/evidence/{file_id}")
async def delete_evidence(file_id: str):
    """Delete uploaded evidence."""
    meta = _evidence_index.pop(file_id, None)
    if not meta:
        raise HTTPException(status_code=404, detail="Evidence not found")
    disk_path = os.path.join(EVIDENCE_DIR, meta["disk_name"])
    if os.path.exists(disk_path):
        os.remove(disk_path)
    return {"message": f"Evidence {file_id} deleted."}
