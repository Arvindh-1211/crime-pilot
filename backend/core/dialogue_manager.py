"""Dialogue Manager for orchestrating the cybercrime complaint chat flow."""
import uuid
from enum import Enum
from typing import Dict, Any, Optional

from .intent_classifier import intent_classifier
from .slot_engine import slot_engine
from .validator import validator
from .llm_handler import llm_handler
from .duplicate_checker import duplicate_checker
from .complaint_builder import complaint_builder
from .complaint_store import complaint_store


class DialogueState(str, Enum):
    """Dialogue states for the complaint filing process."""
    GREETING = "GREETING"
    COLLECTING_DESC = "COLLECTING_DESC"
    CONFIRMING_CAT = "CONFIRMING_CAT"
    FILLING_SLOTS = "FILLING_SLOTS"
    REVIEWING = "REVIEWING"
    SUBMITTED = "SUBMITTED"


def _generate_complaint_id() -> str:
    """Generate a unique complaint ID in format CY-2025-{8 char UUID hex}."""
    return f"CY-2025-{uuid.uuid4().hex[:8].upper()}"


class DialogueManager:
    """Manages the chat dialogue flow and state."""

    def __init__(self):
        """Initialize the dialogue manager."""
        self._sessions: Dict[str, Dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process_message(self, session_id: str, user_text: str) -> Dict[str, Any]:
        """Process a user message and return a structured response.

        Returns:
            Dict with keys: bot_response, state, progress, category_id,
                            filled_slots, is_complete, complaint_id (optional)
        """
        session = self._get_session(session_id)

        if "conversation_history" not in session:
            session["conversation_history"] = []
        session["conversation_history"].append(f"User: {user_text}")
        session["last_message"] = user_text

        response = self._process_by_state(session, user_text)
        self._sessions[session_id] = session

        return {
            "bot_response": response["bot_response"],
            "state": session["state"],
            "progress": response.get("progress", self._get_progress(session)),
            "category_id": session.get("category_id"),
            "filled_slots": session.get("filled_slots", {}),
            "is_complete": session["state"] == DialogueState.SUBMITTED,
            "complaint_id": response.get("complaint_id"),
        }

    # ------------------------------------------------------------------
    # Session helpers
    # ------------------------------------------------------------------

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
                "category_detected": False,
            }
        return self._sessions[session_id]

    # ------------------------------------------------------------------
    # State router
    # ------------------------------------------------------------------

    def _process_by_state(self, session: Dict[str, Any], user_text: str) -> Dict[str, Any]:
        """Route message to the correct state handler."""
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

        return self._get_default_response(session)

    # ------------------------------------------------------------------
    # State handlers
    # ------------------------------------------------------------------

    def _handle_greeting(self, session: Dict[str, Any], user_text: str) -> Dict[str, Any]:
        """Handle GREETING state.

        If the user's first message looks like a real description (>20 chars),
        skip the greeting ping-pong and immediately classify it. Otherwise send
        a welcome message and wait for the description.
        """
        user_text_stripped = user_text.strip()
        is_descriptive = len(user_text_stripped) > 20

        if is_descriptive:
            # User has already described their problem — skip to classification
            session["raw_description"] = user_text_stripped
            session["state"] = DialogueState.COLLECTING_DESC
            return self._handle_collecting_desc(session, user_text_stripped)

        # Short greeting — respond warmly and ask for description
        session["state"] = DialogueState.COLLECTING_DESC
        context = {
            "current_state": "GREETING",
            "conversation_history": session.get("conversation_history", []),
        }
        bot_response = llm_handler.generate_response(context)
        session["conversation_history"].append(f"Assistant: {bot_response}")
        return {"bot_response": bot_response, "progress": self._get_progress(session)}

    def _handle_collecting_desc(self, session: Dict[str, Any], user_text: str) -> Dict[str, Any]:
        """Handle COLLECTING_DESC — gather enough context, then classify.

        We stay in this state, asking follow-up questions, until the LLM decides
        the description is sufficient to confidently identify the fraud type.
        Only then do we classify and move to slot-filling.
        """
        # Accumulate all user input into a growing description
        existing = session.get("raw_description") or ""
        if existing and user_text.strip() not in existing:
            session["raw_description"] = f"{existing} {user_text.strip()}"
        else:
            session["raw_description"] = user_text.strip()

        accumulated = session["raw_description"]

        # Ask LLM: do we have enough to classify?
        assessment = llm_handler.assess_description(
            accumulated,
            session.get("conversation_history", [])
        )

        if not assessment.get("sufficient", False):
            # Not enough info yet — ask a targeted follow-up question
            bot_response = assessment.get(
                "follow_up",
                "Could you tell me more about what happened? What did the scammer ask you to do?"
            )
            session["conversation_history"].append(f"Assistant: {bot_response}")
            return {
                "bot_response": bot_response,
                "progress": self._get_progress(session),
                "category_id": session.get("category_id"),
                "filled_slots": session.get("filled_slots", {}),
            }

        # Description is sufficient — classify using Gemini (falls back to sentence-transformers)
        llm_category = llm_handler.classify_with_llm(accumulated)
        if llm_category:
            session["category_id"] = llm_category
        else:
            classification = intent_classifier.classify(accumulated)
            session["category_id"] = classification["category_id"]

        session["category_detected"] = True
        session["state"] = DialogueState.FILLING_SLOTS
        session["slot_queue"] = slot_engine.load_slots(session["category_id"])
        self._prefill_slots_from_description(session)

        # Announce the detected category — inform, don't ask for confirmation
        category_label = self._get_category_label(session["category_id"])

        # If all slots were pre-filled from the description, jump straight to review
        next_slot = slot_engine.get_next_empty_slot(
            session["slot_queue"], session.get("filled_slots", {})
        )
        if next_slot is None:
            return self._transition_to_review(
                session, session["category_id"], session.get("filled_slots", {})
            )

        # Announce category then ask first missing slot
        first_question = self._ask_next_slot(session)
        bot_response = (
            f"Based on your description, this appears to be a case of **{category_label}**. "
            f"I'll need a few more details.\n\n{first_question}"
        )
        session["conversation_history"].append(f"Assistant: {bot_response}")
        return {
            "bot_response": bot_response,
            "progress": self._get_progress(session),
            "category_id": session["category_id"],
            "filled_slots": session.get("filled_slots", {}),
        }


    def _handle_confirming_cat(self, session: Dict[str, Any], user_text: str) -> Dict[str, Any]:
        """CONFIRMING_CAT is no longer used (category is classified silently).
        Treat any message here as a description and re-classify."""
        session["state"] = DialogueState.COLLECTING_DESC
        return self._handle_collecting_desc(session, user_text)

    def _handle_filling_slots(self, session: Dict[str, Any], user_text: str) -> Dict[str, Any]:
        """Handle FILLING_SLOTS — validate and save the user's answer, ask the next slot."""
        category_id = session["category_id"]
        slot_queue = session.get("slot_queue", [])
        filled_slots = session.get("filled_slots", {})

        # Which slot are we currently collecting?
        slot_name = slot_engine.get_next_empty_slot(slot_queue, filled_slots)

        if slot_name is None:
            # All slots are filled — move to review
            return self._transition_to_review(session, category_id, filled_slots)

        # Validate user's answer for this slot
        slot_type = slot_engine.get_slot_type(slot_name)
        validation = validator.validate(slot_name, user_text, slot_type)

        if validation["valid"]:
            filled_slots[slot_name] = validation["cleaned_value"]
            session["filled_slots"] = filled_slots

            # Check if there are more slots
            next_slot = slot_engine.get_next_empty_slot(slot_queue, filled_slots)
            if next_slot is None:
                return self._transition_to_review(session, category_id, filled_slots)

            bot_response = self._ask_next_slot(session)
        else:
            # Invalid input — re-ask with error
            slot_info = slot_engine.get_slot_definition(slot_name) or {}
            bot_response = llm_handler.generate_error_reask(slot_name, validation["error"], slot_info)

        session["conversation_history"].append(f"Assistant: {bot_response}")
        return {
            "bot_response": bot_response,
            "progress": self._get_progress(session),
            "category_id": category_id,
            "filled_slots": filled_slots,
        }

    def _handle_reviewing(self, session: Dict[str, Any], user_text: str) -> Dict[str, Any]:
        """Handle REVIEWING — user confirms or wants to edit.

        On confirmation, actually build + store the complaint and return its ID.
        """
        user_lower = user_text.lower()

        if any(x in user_lower for x in ["yes", "haan", "correct", "sure", "ok", "submit", "final", "yeah", "confirm"]):
            return self._submit_complaint(session)

        elif any(x in user_lower for x in ["no", "nahi", "change", "modify", "edit", "update"]):
            session["state"] = DialogueState.FILLING_SLOTS
            bot_response = "Of course! Which piece of information would you like to change? Please describe what needs to be updated."

        else:
            bot_response = "Are you ready to submit your complaint? Please reply **Yes** to confirm or **No** if you need to make changes."

        session["conversation_history"].append(f"Assistant: {bot_response}")
        return {
            "bot_response": bot_response,
            "progress": self._get_progress(session),
            "category_id": session.get("category_id"),
            "filled_slots": session.get("filled_slots", {}),
        }

    def _handle_submitted(self, session: Dict[str, Any], user_text: str) -> Dict[str, Any]:
        """Handle SUBMITTED — offer to file a new complaint."""
        complaint_id = session.get("complaint_id", "")
        bot_response = (
            f"Your complaint (ID: **{complaint_id}**) has already been submitted. "
            "If you have another incident to report, please start a new session."
        )
        session["conversation_history"].append(f"Assistant: {bot_response}")
        return {
            "bot_response": bot_response,
            "progress": self._get_progress(session),
            "category_id": session.get("category_id"),
            "filled_slots": session.get("filled_slots", {}),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _prefill_slots_from_description(self, session: Dict[str, Any]) -> None:
        """Use Gemini to extract slot values from the raw incident description
        and pre-fill them so we don't ask questions the user already answered."""
        raw_description = session.get("raw_description", "")
        slot_queue = session.get("slot_queue", [])
        filled_slots = session.get("filled_slots", {})

        if not raw_description or not slot_queue:
            return

        # Only try to extract slots that aren't already filled
        unfilled = [s for s in slot_queue if s not in filled_slots]
        if not unfilled:
            return

        extracted = llm_handler.extract_slots_from_description(
            raw_description,
            unfilled,
            slot_engine.slot_definitions
        )

        # Validate each extracted value before accepting it
        for slot_name, raw_value in extracted.items():
            slot_type = slot_engine.get_slot_type(slot_name)
            try:
                validation = validator.validate(slot_name, str(raw_value), slot_type)
                if validation["valid"]:
                    filled_slots[slot_name] = validation["cleaned_value"]
            except Exception:
                pass  # Skip if validation crashes

        session["filled_slots"] = filled_slots

    def _ask_next_slot(self, session: Dict[str, Any]) -> str:
        """Generate the question for the next unfilled slot."""
        slot_queue = session.get("slot_queue", [])
        filled_slots = session.get("filled_slots", {})
        category_id = session.get("category_id", "")
        raw_description = session.get("raw_description", "")

        slot_name = slot_engine.get_next_empty_slot(slot_queue, filled_slots)
        if slot_name is None:
            # All slots filled — transition to review directly
            return self._transition_to_review(
                session, session.get("category_id", ""), filled_slots
            )["bot_response"]

        slot_info = slot_engine.get_slot_definition(slot_name) or {}

        context = {
            "current_state": "FILLING_SLOTS",
            "slot_being_asked": slot_name,
            "category_label": category_id,
            "raw_description": raw_description,
            "already_provided": {k: v for k, v in filled_slots.items() if v is not None},
            "conversation_history": session.get("conversation_history", []),
        }
        return llm_handler.generate_response(context)

    def _transition_to_review(
        self,
        session: Dict[str, Any],
        category_id: str,
        filled_slots: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Move to REVIEWING state and show a full complaint summary."""
        session["state"] = DialogueState.REVIEWING

        # Human-readable category label
        category_label = self._get_category_label(category_id)

        # Slot labels map (reuse from complaint_builder)
        slot_labels = {
            "incident_date": "Incident Date",
            "amount_lost": "Amount Lost (₹)",
            "amount_invested": "Amount Invested (₹)",
            "amount_demanded": "Amount Demanded (₹)",
            "upi_transaction_id": "UPI Transaction ID",
            "suspect_upi_id": "Suspect UPI ID",
            "platform": "Platform / App Used",
            "platform_used": "Platform Used by Suspect",
            "platform_name": "Investment Platform",
            "caller_number": "Caller's Phone Number",
            "suspect_contact": "Suspect Contact",
            "recruiter_contact": "Recruiter Contact",
            "bank_name": "Bank / Institution",
            "bank_involved": "Bank Targeted",
            "phishing_url": "Phishing URL",
            "data_compromised": "Data Compromised",
            "call_recording": "Call Recording Available",
            "otp_shared": "OTP Shared with Caller",
            "email_screenshot": "Email Screenshot Available",
            "screenshot_available": "Screenshots Available",
            "screenshot": "Screenshot Available",
            "payment_proof": "Payment Proof Available",
            "utr_number": "UTR Number",
        }

        # Build slot lines
        lines = []
        for slot, value in filled_slots.items():
            label = slot_labels.get(slot, slot.replace("_", " ").title())
            # Make boolean values readable
            if value == "true":
                display = "Yes"
            elif value == "false":
                display = "No"
            else:
                display = value
            lines.append(f"• **{label}**: {display}")

        raw_desc = session.get("raw_description", "")
        desc_snippet = (raw_desc[:120] + "...") if len(raw_desc) > 120 else raw_desc

        summary_parts = [
            f"📋 **Complaint Summary**",
            f"**Complaint Type**: {category_label}",
            f"**Your Description**: {desc_snippet}",
        ]
        if lines:
            summary_parts.append("**Details collected:**")
            summary_parts.extend(lines)

        summary = "\n".join(summary_parts)
        bot_response = (
            f"{summary}\n\n"
            "Please review the above. Reply **Yes** to submit your complaint or **No** to make changes."
        )
        session["conversation_history"].append(f"Assistant: {bot_response}")
        return {
            "bot_response": bot_response,
            "progress": self._get_progress(session),
            "category_id": category_id,
            "filled_slots": filled_slots,
        }

    def _submit_complaint(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Build the complaint, store it, and return confirmation with complaint ID."""
        complaint_id = _generate_complaint_id()
        session["state"] = DialogueState.SUBMITTED
        session["complaint_id"] = complaint_id

        # Build the full complaint JSON
        complaint_json = complaint_builder.build_complaint(session, complaint_id)

        # Compute severity
        severity_score = complaint_builder.compute_severity(
            session.get("filled_slots", {}),
            session.get("category_id")
        )
        complaint_json["severity_score"] = severity_score

        # Store in shared complaint store
        complaint_store.save(complaint_id, complaint_json)

        # Register with duplicate checker (best-effort)
        try:
            phone = session.get("phone_number", "unknown")
            duplicate_checker.register(
                phone,
                complaint_id,
                session.get("filled_slots", {}),
                session.get("raw_description", "")
            )
        except Exception:
            pass

        bot_response = (
            f"✅ Your complaint has been successfully submitted!\n\n"
            f"**Complaint ID: {complaint_id}**\n\n"
            f"Please save this ID for future reference. "
            f"Authorities will review your complaint and get in touch with you."
        )
        session["conversation_history"].append(f"Assistant: {bot_response}")
        return {
            "bot_response": bot_response,
            "progress": self._get_progress(session),
            "category_id": session.get("category_id"),
            "filled_slots": session.get("filled_slots", {}),
            "complaint_id": complaint_id,
        }

    def _get_default_response(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback when state is unrecognized."""
        context = {"current_state": "COLLECTING_DESC"}
        bot_response = llm_handler.generate_response(context)
        return {
            "bot_response": bot_response,
            "progress": self._get_progress(session),
            "category_id": session.get("category_id"),
            "filled_slots": session.get("filled_slots", {}),
        }

    def _get_progress(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Get slot filling progress for the current session."""
        slot_queue = session.get("slot_queue", [])
        filled_slots = session.get("filled_slots", {})

        if not slot_queue and session.get("category_id"):
            slot_queue = slot_engine.load_slots(session["category_id"])

        return slot_engine.get_progress(slot_queue, filled_slots)

    def _get_category_label(self, category_id: Optional[str]) -> str:
        """Return a human-readable label for a category ID."""
        labels = {
            "UPI_FRAUD": "UPI Fraud",
            "VISHING": "Vishing (Voice/Video Call Fraud)",
            "PHISHING": "Phishing",
            "INVESTMENT_SCAM": "Investment Scam",
            "SEXTORTION": "Sextortion / Sexual Blackmail",
        }
        return labels.get(category_id, category_id or "Unknown")


# Global dialogue manager instance
dialogue_manager = DialogueManager()
