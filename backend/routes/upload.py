"""Evidence upload routes for handling file uploads."""
from fastapi import APIRouter, HTTPException, UploadFile, File, Body
from typing import Dict, Any, Optional
import uuid
import os

router = APIRouter()

# In-memory evidence storage
stored_evidence: Dict[str, Dict[str, Any]] = {}


@router.post("/upload/evidence")
async def upload_evidence(
    session_id: str = Body(...),
    file: Optional[UploadFile] = File(None)
):
    """Upload evidence file (JPG, PNG, PDF).

    Args:
        session_id: Session ID for evidence storage
        file: The file to upload

    Returns:
        {file_id: str, file_name: str, file_type: str, upload_time: str}
    """
    # Verify file is provided
    if file is None:
        raise HTTPException(status_code=400, detail="No file provided")

    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "application/pdf"]
    file_type = file.content_type

    if file_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
        )

    # Read file content (store in memory for demo)
    file_content = await file.read()
    file_size = len(file_content)

    # Generate file ID
    file_id = f"FILE-{uuid.uuid4().hex[:8].upper()}"

    # Store evidence
    evidence_entry = {
        "file_id": file_id,
        "file_name": file.filename,
        "file_type": file_type,
        "file_size": file_size,
        "upload_time": str(uuid.uuid4())[:8],  # Simple timestamp
        "session_id": session_id,
        "data": file_content.hex()  # Store hex for demo (in real app, save to disk)
    }

    stored_evidence[file_id] = evidence_entry

    return {
        "file_id": file_id,
        "file_name": file.filename,
        "file_type": file_type,
        "upload_time": evidence_entry["upload_time"]
    }


@router.get("/upload/evidence/{file_id}")
async def get_evidence(file_id: str):
    """Retrieve evidence file by ID."""
    if file_id not in stored_evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    evidence = stored_evidence[file_id]

    return {
        "file_id": file_id,
        "file_name": evidence["file_name"],
        "file_type": evidence["file_type"],
        "file_size": evidence["file_size"],
        "session_id": evidence["session_id"],
        "upload_time": evidence["upload_time"]
    }


@router.delete("/upload/evidence/{file_id}")
async def delete_evidence(file_id: str):
    """Delete uploaded evidence."""
    if file_id not in stored_evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    del stored_evidence[file_id]

    return {"message": f"Evidence {file_id} deleted successfully"}
