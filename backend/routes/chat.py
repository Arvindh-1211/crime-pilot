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
        "raw_description": None
    }

    session_store.create_session(session_id, initial_data)

    # Generate welcome message
    welcome_message = f"Namaste! I'm your NCRP Cybercrime Assistant. I'll help you file a complaint for cyber incidents. What type of cybercrime did you experience? You can describe it in English or Hinglish."

    return {
        "session_id": session_id,
        "welcome_message": welcome_message
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

    # Verify session exists
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found. Please start a new session.")

    try:
        # Process message through dialogue manager
        result = dialogue_manager.process_message(session_id, message)

        return {
            "bot_response": result["bot_response"],
            "state": result["state"],
            "progress": result["progress"],
            "category_id": result["category_id"],
            "filled_slots": result["filled_slots"],
            "is_complete": result["is_complete"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")
