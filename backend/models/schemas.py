from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class StartSessionRequest(BaseModel):
    phone_number: str = Field(..., description="User's phone number for session tracking")


class StartSessionResponse(BaseModel):
    session_id: str = Field(..., description="Unique session identifier")
    welcome_message: str = Field(..., description="Initial welcome message")


class ChatMessageRequest(BaseModel):
    session_id: str = Field(..., description="Session ID from start session")
    message: str = Field(..., description="User's message or response")


class ChatMessageResponse(BaseModel):
    bot_response: str = Field(..., description="Assistant's response message")
    state: str = Field(..., description="Current dialogue state")
    progress: Dict[str, Any] = Field(..., description="Slot filling progress")
    category_id: Optional[str] = Field(None, description="Detected fraud category")
    filled_slots: Dict[str, Any] = Field(default_factory=dict, description="Currently filled slots")
    is_complete: bool = Field(default=False, description="Whether the complaint is complete")


class SubmitComplaintRequest(BaseModel):
    session_id: str = Field(..., description="Session ID to submit")
    phone_number: str = Field(..., description="User's phone number for duplicate checking")


class SubmitComplaintResponse(BaseModel):
    complaint_id: str = Field(..., description="Generated complaint ID")
    complaint_json: Dict[str, Any] = Field(..., description="Full complaint structure")
    severity_score: float = Field(..., description="Calculated severity score (0-10)")


class EvidenceUploadRequest(BaseModel):
    session_id: str = Field(..., description="Session ID for evidence storage")
    file_id: str = Field(..., description="Generated file ID")
    file_name: str = Field(..., description="Original file name")
    file_type: str = Field(..., description="MIME type of the file")


class EvidenceUploadResponse(BaseModel):
    file_id: str = Field(..., description="Generated file ID")
    file_name: str = Field(..., description="Original file name")
    file_type: str = Field(..., description="MIME type of the file")
    upload_time: str = Field(..., description="Timestamp of upload")


class DuplicateCheckResult(BaseModel):
    is_duplicate: bool = Field(..., description="Whether this is a duplicate complaint")
    matched_complaint_id: Optional[str] = Field(None, description="ID of matching complaint if duplicate")
    method: Optional[str] = Field(None, description="Detection method: 'exact' or 'semantic'")


class ComplaintDetail(BaseModel):
    complaint_id: str = Field(..., description="Complaint ID")
    complaint_json: Dict[str, Any] = Field(..., description="Full complaint structure")
    severity_score: float = Field(..., description="Severity score")
    created_at: str = Field(..., description="Creation timestamp")
