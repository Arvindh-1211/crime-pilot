"""Chat routes for session management and message processing."""
from fastapi import APIRouter, HTTPException, Body
from typing import Any, Dict
import uuid

from utils.session_store import session_store
from core.dialogue_manager import dialogue_manager

router = APIRouter()


@router.post("/chat/start")
async def start_session(request: Dict[str, Any] = Body(...)):
    """Start a new chat session.

    Args:
        request: {phone_number: str}

    Returns:
        {session_id: str, welcome_message: str}
    """
    phone_number = request.get("phone_number", "")

    if not phone_number:
        raise HTTPException(status_code=400, detail="Phone number is required")

    # Generate session ID
    session_id = str(uuid.uuid4())

    # Create session with initial data
    initial_data = {
        "phone_number": phone_number,
        "state": "GREETING",
        "category_id": None,
        "filled_slots": {},
        "slot_queue": [],
        "raw_description": None,
    }

    session_store.create_session(session_id, initial_data)

    welcome_message = (
        "Hello! I'm your NCRP Cybercrime Assistant. "
        "I'm here to help you file a complaint on the National Cybercrime Reporting Portal. "
        "Please describe what happened to you."
    )

    return {
        "session_id": session_id,
        "welcome_message": welcome_message,
    }


@router.post("/chat/message")
async def process_message(request: Dict[str, Any] = Body(...)):
    """Process a user message through the dialogue manager.

    Args:
        request: {session_id: str, message: str}

    Returns:
        ChatMessageResponse with bot response, state, progress, etc.
    """
    session_id = request.get("session_id", "")
    message = request.get("message", "")

    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID is required")

    if not message:
        raise HTTPException(status_code=400, detail="Message is required")

    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found. Please start a new session.")

    try:
        result = dialogue_manager.process_message(session_id, message)

        # ── KEY FIX: sync the dialogue manager's rich session state back into
        # session_store so that /complaint/submit can read filled_slots etc.
        dm_session = dialogue_manager._sessions.get(session_id, {})
        session_store.update_session(session_id, {
            "filled_slots":   dm_session.get("filled_slots", {}),
            "category_id":    dm_session.get("category_id"),
            "raw_description":dm_session.get("raw_description"),
            "state":          dm_session.get("state"),
        })

        return {
            "bot_response":  result["bot_response"],
            "state":         result["state"],
            "progress":      result["progress"],
            "category_id":   result["category_id"],
            "filled_slots":  result["filled_slots"],
            "is_complete":   result["is_complete"],
            "complaint_id":  result.get("complaint_id"),
            "email_preview": result.get("email_preview"),
            "tracking_url":  result.get("tracking_url"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

