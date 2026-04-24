"""Dialogue Manager for orchestrating chat flow."""
from enum import Enum
from typing import Dict, Any, Optional
import uuid

from .intent_classifier import intent_classifier
from .slot_engine import slot_engine
from .validator import validator
from .llm_handler import llm_handler
from .duplicate_checker import duplicate_checker


class DialogueState(str, Enum):
    """Dialogue states for the complaint filing process."""
    GREETING = "GREETING"
    COLLECTING_DESC = "COLLECTING_DESC"
    CONFIRMING_CAT = "CONFIRMING_CAT"
    FILLING_SLOTS = "FILLING_SLOTS"
    REVIEWING = "REVIEWING"
    SUBMITTED = "SUBMITTED"


class DialogueManager:
    """Manages the chat dialogue flow and state."""

    def __init__(self):
        """Initialize the dialogue manager."""
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def process_message(self, session_id: str, user_text: str) -> Dict[str, Any]:
        """Process a user message and return response.

        Args:
            session_id: Session identifier
            user_text: User's message

        Returns:
            Dict with keys:
                - bot_response: Assistant's response
                - state: Current dialogue state
                - progress: Slot filling progress
                - category_id: Detected category (if any)
                - filled_slots: Currently filled slots
                - is_complete: Whether complaint is complete
        """
        # Get or create session
        session = self._get_session(session_id)

        # Update conversation history
        if "conversation_history" not in session:
            session["conversation_history"] = []

        session["conversation_history"].append(f"User: {user_text}")
        session["last_message"] = user_text

        # Process based on current state
        response = self._process_by_state(session, user_text)

        # Save session
        self._sessions[session_id] = session

        # Build response
        return {
            "bot_response": response["bot_response"],
            "state": session["state"],
            "progress": response["progress"],
            "category_id": session.get("category_id"),
            "filled_slots": session.get("filled_slots", {}),
            "is_complete": session["state"] == DialogueState.SUBMITTED
        }

    def _get_session(self, session_id: str) -> Dict[str, Any]:
        """Get or create session data."""
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "state": DialogueState.GREETING,
                "category_id": None,
                "category_confidence": 0,
                "needs_confirmation": False,
                "filled_slots": {},
                "slot_queue": [],
                "raw_description": None,
                "conversation_history": [],
                "category_detected": False
            }
        return self._sessions[session_id]

    def _process_by_state(self, session: Dict[str, Any], user_text: str) -> Dict[str, Any]:
        """Process message based on current dialogue state."""
        state = session["state"]

        if state == DialogueState.GREETING:
            return self._handle_greeting(session, user_text)

        elif state == DialogueState.COLLECTING_DESC:
            return self._handle_collecting_desc(session, user_text)

        elif state == DialogueState.CONFIRMING_CAT:
            return self._handle_confirming_cat(session, user_text)

        elif state == DialogueState.FILLING_SLOTS:
            return self._handle_filling_slots(session, user_text)

        elif state == DialogueState.REVIEWING:
            return self._handle_reviewing(session, user_text)

        elif state == DialogueState.SUBMITTED:
            return self._handle_submitted(session, user_text)

        # Default fallback
        return self._get_default_response(session)

    def _handle_greeting(self, session: Dict[str, Any], user_text: str) -> Dict[str, Any]:
        """Handle greeting state - welcome user and ask for incident description."""
        context = {
            "current_state": "GREETING",
            "category_label": None
        }
        bot_response = llm_handler.generate_response(context)
        session["raw_description"] = user_text
        session["state"] = DialogueState.COLLECTING_DESC

        return {
            "bot_response": bot_response,
            "progress": self._get_progress(session),
            "filled_slots": session.get("filled_slots", {})
        }

    def _handle_collecting_desc(self, session: Dict[str, Any], user_text: str) -> Dict[str, Any]:
        """Handle collecting description - classify fraud type."""
        session["raw_description"] = user_text

        # Classify intent
        classification = intent_classifier.classify(user_text)
        session["category_id"] = classification["category_id"]
        session["category_confidence"] = classification["confidence"]
        session["needs_confirmation"] = classification["needs_confirmation"]

        if classification["needs_confirmation"]:
            session["state"] = DialogueState.CONFIRMING_CAT
            bot_response = llm_handler.generate_category_confirmation(
                session["category_id"],
                session["category_confidence"]
            )
        else:
            # Confirm without asking
            session["category_detected"] = True
            session["state"] = DialogueState.FILLING_SLOTS

            # Load slots for this category
            session["slot_queue"] = slot_engine.load_slots(session["category_id"])

            # Ask first slot
            slot_name = slot_engine.get_next_empty_slot(session["slot_queue"], session.get("filled_slots", {}))
            slot_info = slot_engine.get_slot_definition(slot_name) if slot_name else None

            context = {
                "current_state": "FILLING_SLOTS",
                "slot_being_asked": slot_name,
                "category_label": session["category_id"]
            }
            bot_response = llm_handler.generate_response(context)

        return {
            "bot_response": bot_response,
            "progress": self._get_progress(session),
            "category_id": session["category_id"],
            "filled_slots": session.get("filled_slots", {})
        }

    def _handle_confirming_cat(self, session: Dict[str, Any], user_text: str) -> Dict[str, Any]:
        """Handle category confirmation."""
        user_lower = user_text.lower()

        if any(x in user_lower for x in ["yes", "haan", "correct", "right", "true"]):
            session["category_detected"] = True
            session["state"] = DialogueState.FILLING_SLOTS

            # Load slots for this category
            session["slot_queue"] = slot_engine.load_slots(session["category_id"])

            slot_name = slot_engine.get_next_empty_slot(session["slot_queue"], session.get("filled_slots", {}))
            slot_info = slot_engine.get_slot_definition(slot_name) if slot_name else None

            context = {
                "current_state": "FILLING_SLOTS",
                "slot_being_asked": slot_name,
                "category_label": session["category_id"]
            }
            bot_response = llm_handler.generate_response(context)
        elif any(x in user_lower for x in ["no", "nahi", "wrong", "incorrect", "false"]):
            session["category_id"] = None
            session["category_detected"] = False
            session["state"] = DialogueState.COLLECTING_DESC
            bot_response = "Understood. Please describe your incident again so I can correctly identify the type of cybercrime."
        else:
            bot_response = "Please answer Yes or No. Was this a case of {}?".format(session["category_id"])

        return {
            "bot_response": bot_response,
            "progress": self._get_progress(session),
            "category_id": session["category_id"],
            "filled_slots": session.get("filled_slots", {})
        }

    def _handle_filling_slots(self, session: Dict[str, Any], user_text: str) -> Dict[str, Any]:
        """Handle slot filling."""
        category_id = session["category_id"]
        slot_queue = session.get("slot_queue", [])
        filled_slots = session.get("filled_slots", {})

        # Get next slot
        slot_name = slot_engine.get_next_empty_slot(slot_queue, filled_slots)

        if slot_name is None:
            # All slots filled, move to reviewing
            session["state"] = DialogueState.REVIEWING

            context = {
                "current_state": "REVIEWING",
                "category_label": category_id
            }
            bot_response = llm_handler.generate_response(context)
        else:
            # Validate user input for this slot
            slot_info = slot_engine.get_slot_definition(slot_name)
            slot_type = slot_engine.get_slot_type(slot_name)

            validation = validator.validate(slot_name, user_text, slot_type)

            if validation["valid"]:
                # Save valid value
                filled_slots[slot_name] = validation["cleaned_value"]
                session["filled_slots"] = filled_slots

                # Check if there are more slots
                slot_name = slot_engine.get_next_empty_slot(slot_queue, filled_slots)

                if slot_name is None:
                    session["state"] = DialogueState.REVIEWING
                    context = {
                        "current_state": "REVIEWING",
                        "category_label": category_id
                    }
                    bot_response = llm_handler.generate_response(context)
                else:
                    # Ask next slot
                    slot_info = slot_engine.get_slot_definition(slot_name)
                    context = {
                        "current_state": "FILLING_SLOTS",
                        "slot_being_asked": slot_name,
                        "category_label": category_id
                    }
                    bot_response = llm_handler.generate_response(context)
            else:
                # Invalid input - re-ask with error
                context = {
                    "current_state": "FILLING_SLOTS",
                    "slot_being_asked": slot_name,
                    "validation_error": validation["error"],
                    "category_label": category_id
                }
                bot_response = llm_handler.generate_error_reask(slot_name, validation["error"], slot_info)

        return {
            "bot_response": bot_response,
            "progress": self._get_progress(session),
            "category_id": category_id,
            "filled_slots": filled_slots
        }

    def _handle_reviewing(self, session: Dict[str, Any], user_text: str) -> Dict[str, Any]:
        """Handle reviewing state - confirm complaint is complete."""
        user_lower = user_text.lower()

        if any(x in user_lower for x in ["yes", "haan", "correct", "sure", "ok", "submit", "final"]):
            session["state"] = DialogueState.SUBMITTED
            return {
                "bot_response": "Thank you! Your complaint has been successfully submitted. A confirmation will be sent to your registered mobile number.",
                "progress": self._get_progress(session),
                "category_id": session.get("category_id"),
                "filled_slots": session.get("filled_slots", {}),
                "is_complete": True
            }
        elif any(x in user_lower for x in ["no", "nahi", "change", "modify", "edit"]):
            session["state"] = DialogueState.FILLING_SLOTS
            bot_response = "Which field would you like to change? You can say the slot name or describe what you want to update."
        else:
            bot_response = "Please confirm: Are you ready to submit your complaint? Answer Yes or No."

        return {
            "bot_response": bot_response,
            "progress": self._get_progress(session),
            "category_id": session.get("category_id"),
            "filled_slots": session.get("filled_slots", {})
        }

    def _handle_submitted(self, session: Dict[str, Any], user_text: str) -> Dict[str, Any]:
        """Handle submitted state - new complaint starts."""
        session["state"] = DialogueState.GREETING
        session["category_id"] = None
        session["filled_slots"] = {}

        context = {
            "current_state": "GREETING",
            "category_label": None
        }
        bot_response = llm_handler.generate_response(context)

        return {
            "bot_response": bot_response,
            "progress": self._get_progress(session),
            "category_id": None,
            "filled_slots": {}
        }

    def _get_default_response(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Get default response when state is unrecognized."""
        context = {
            "current_state": "COLLECTING_DESC",
            "category_label": None
        }
        bot_response = llm_handler.generate_response(context)
        return {
            "bot_response": bot_response,
            "progress": self._get_progress(session),
            "category_id": session.get("category_id"),
            "filled_slots": session.get("filled_slots", {})
        }

    def _get_progress(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Get slot filling progress for current session."""
        slot_queue = session.get("slot_queue", [])
        filled_slots = session.get("filled_slots", {})

        if not slot_queue and session.get("category_id"):
            slot_queue = slot_engine.load_slots(session["category_id"])

        return slot_engine.get_progress(slot_queue, filled_slots)


# Global dialogue manager instance
dialogue_manager = DialogueManager()
