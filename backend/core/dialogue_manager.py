"""Dialogue Manager for orchestrating the cybercrime complaint chat flow."""
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional

from .intent_classifier import intent_classifier
from .slot_engine import slot_engine
from .validator import validator
from .llm_handler import llm_handler
from .duplicate_checker import duplicate_checker
from .complaint_builder import complaint_builder
from .complaint_store import complaint_store


# Minimal station routing data (mirrors routes/complaint.py)
_CYBER_STATIONS = [
    {"keywords": ["mumbai", "thane", "navi mumbai", "maharashtra"],
     "name": "Mumbai Cyber Crime Police Station", "jurisdiction": "Mumbai Metropolitan Region"},
    {"keywords": ["delhi", "new delhi", "noida", "gurgaon", "gurugram"],
     "name": "Delhi Cyber Crime Unit – Dwarka", "jurisdiction": "NCR Delhi Region"},
    {"keywords": ["bangalore", "bengaluru", "karnataka", "mysore"],
     "name": "Bengaluru CID Cyber Crime Division", "jurisdiction": "Karnataka State"},
    {"keywords": ["chennai", "tamil nadu", "coimbatore", "madurai"],
     "name": "Chennai Cyber Crime Cell – Egmore", "jurisdiction": "Tamil Nadu State"},
    {"keywords": ["hyderabad", "telangana", "secunderabad"],
     "name": "Hyderabad Cyber Crime Police Station", "jurisdiction": "Telangana State"},
    {"keywords": ["kolkata", "west bengal", "howrah"],
     "name": "Kolkata Cyber Crime Police Station – Lalbazar", "jurisdiction": "West Bengal State"},
    {"keywords": ["ahmedabad", "gujarat", "surat", "vadodara"],
     "name": "Gujarat CID Cyber Crime Cell", "jurisdiction": "Gujarat State"},
    {"keywords": ["pune", "nagpur"],
     "name": "Pune Cyber Crime Cell", "jurisdiction": "Pune Division"},
    {"keywords": ["lucknow", "uttar pradesh", "kanpur", "varanasi"],
     "name": "UP Cyber Crime Cell – Lucknow", "jurisdiction": "Uttar Pradesh State"},
    {"keywords": ["jaipur", "rajasthan", "jodhpur"],
     "name": "Rajasthan Cyber Crime Cell – Jaipur", "jurisdiction": "Rajasthan State"},
]


def _route_to_station(location: str) -> dict:
    if not location:
        return {"name": "Central Cyber Crime Coordination Centre (I4C)", "jurisdiction": "National – India"}
    loc = location.lower().strip()
    for s in _CYBER_STATIONS:
        if any(kw in loc for kw in s["keywords"]):
            return {"name": s["name"], "jurisdiction": s["jurisdiction"]}
    return {"name": "Central Cyber Crime Coordination Centre (I4C)", "jurisdiction": "National – India"}


class DialogueState(str, Enum):
    """Dialogue states for the complaint filing process."""
    GREETING = "GREETING"
    COLLECTING_DESC = "COLLECTING_DESC"
    CONFIRMING_CAT = "CONFIRMING_CAT"
    FILLING_SLOTS = "FILLING_SLOTS"
    REVIEWING = "REVIEWING"
    SUBMITTED = "SUBMITTED"


# Universal slots are now handled via the frontend form, 
# so the chatbot will NOT ask for them.
UNIVERSAL_SLOTS = []


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
        """Process a user message and return a structured response."""
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
            # is_complete = True when in REVIEWING (show panel) or SUBMITTED
            "is_complete": session["state"] in (DialogueState.REVIEWING, DialogueState.SUBMITTED),
            "complaint_id": response.get("complaint_id"),
            "email_preview": response.get("email_preview"),
            "tracking_url": response.get("tracking_url"),
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
        """Handle GREETING state."""
        user_text_stripped = user_text.strip()
        is_descriptive = len(user_text_stripped) > 20

        if is_descriptive:
            session["raw_description"] = user_text_stripped
            session["state"] = DialogueState.COLLECTING_DESC
            return self._handle_collecting_desc(session, user_text_stripped)

        session["state"] = DialogueState.COLLECTING_DESC
        context = {
            "current_state": "GREETING",
            "conversation_history": session.get("conversation_history", []),
        }
        bot_response = llm_handler.generate_response(context)
        session["conversation_history"].append(f"Assistant: {bot_response}")
        return {"bot_response": bot_response, "progress": self._get_progress(session)}

    def _handle_collecting_desc(self, session: Dict[str, Any], user_text: str) -> Dict[str, Any]:
        """Handle COLLECTING_DESC — gather enough context, then classify."""
        existing = session.get("raw_description") or ""
        if existing and user_text.strip() not in existing:
            session["raw_description"] = f"{existing} {user_text.strip()}"
        else:
            session["raw_description"] = user_text.strip()

        accumulated = session["raw_description"]

        assessment = llm_handler.assess_description(
            accumulated,
            session.get("conversation_history", [])
        )

        if not assessment.get("sufficient", False):
            bot_response = assessment.get(
                "follow_up",
                "Could you tell me more about what happened? What exactly did the scammer do or ask you to do?"
            )
            session["conversation_history"].append(f"Assistant: {bot_response}")
            return {
                "bot_response": bot_response,
                "progress": self._get_progress(session),
                "category_id": session.get("category_id"),
                "filled_slots": session.get("filled_slots", {}),
            }

        # Classify
        llm_category = llm_handler.classify_with_llm(accumulated)
        if llm_category:
            session["category_id"] = llm_category
        else:
            classification = intent_classifier.classify(accumulated)
            session["category_id"] = classification["category_id"]

        session["category_detected"] = True
        session["state"] = DialogueState.FILLING_SLOTS

        # Build slot queue: category-specific slots only
        category_slots = slot_engine.load_slots(session["category_id"])
        # Deduplicate while preserving order
        seen = set()
        merged = []
        for s in category_slots:
            if s not in seen:
                seen.add(s)
                merged.append(s)
        session["slot_queue"] = merged

        # Pre-fill what we can extract from the description
        self._prefill_slots_from_description(session)

        category_label = self._get_category_label(session["category_id"])

        next_slot = slot_engine.get_next_empty_slot(
            session["slot_queue"], session.get("filled_slots", {})
        )
        if next_slot is None:
            return self._transition_to_review(
                session, session["category_id"], session.get("filled_slots", {})
            )

        first_question = self._ask_next_slot(session)
        bot_response = (
            f"I've identified this as a case of **{category_label}**. "
            f"I'll now collect the details needed for your complaint.\n\n{first_question}"
        )
        session["conversation_history"].append(f"Assistant: {bot_response}")
        return {
            "bot_response": bot_response,
            "progress": self._get_progress(session),
            "category_id": session["category_id"],
            "filled_slots": session.get("filled_slots", {}),
        }

    def _handle_confirming_cat(self, session: Dict[str, Any], user_text: str) -> Dict[str, Any]:
        """Deprecated — redirect to collecting desc."""
        session["state"] = DialogueState.COLLECTING_DESC
        return self._handle_collecting_desc(session, user_text)

    def _handle_filling_slots(self, session: Dict[str, Any], user_text: str) -> Dict[str, Any]:
        """Handle FILLING_SLOTS — validate and save answer, ask next slot."""
        category_id = session["category_id"]
        slot_queue = session.get("slot_queue", [])
        filled_slots = session.get("filled_slots", {})

        # Try to extract any values from this answer that match unfilled slots
        self._prefill_from_current_answer(session, user_text)
        filled_slots = session.get("filled_slots", {})

        slot_name = slot_engine.get_next_empty_slot(slot_queue, filled_slots)

        if slot_name is None:
            return self._transition_to_review(session, category_id, filled_slots)

        # Validate user's answer for the current slot
        slot_type = slot_engine.get_slot_type(slot_name)
        validation = validator.validate(slot_name, user_text, slot_type)

        if validation["valid"]:
            filled_slots[slot_name] = validation["cleaned_value"]
            session["filled_slots"] = filled_slots

            next_slot = slot_engine.get_next_empty_slot(slot_queue, filled_slots)
            if next_slot is None:
                return self._transition_to_review(session, category_id, filled_slots)

            bot_response = self._ask_next_slot(session)
        else:
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
        """Handle REVIEWING — user confirms or edits."""
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
            f"Your complaint (**{complaint_id}**) has already been submitted. "
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
        """Use Gemini to extract slot values from the raw incident description."""
        raw_description = session.get("raw_description", "")
        slot_queue = session.get("slot_queue", [])
        filled_slots = session.get("filled_slots", {})

        if not raw_description or not slot_queue:
            return

        unfilled = [s for s in slot_queue if s not in filled_slots]
        if not unfilled:
            return

        extracted = llm_handler.extract_slots_from_description(
            raw_description,
            unfilled,
            slot_engine.slot_definitions
        )

        for slot_name, raw_value in extracted.items():
            slot_type = slot_engine.get_slot_type(slot_name)
            try:
                validation = validator.validate(slot_name, str(raw_value), slot_type)
                if validation["valid"]:
                    filled_slots[slot_name] = validation["cleaned_value"]
            except Exception:
                pass

        session["filled_slots"] = filled_slots

    def _prefill_from_current_answer(self, session: Dict[str, Any], user_text: str) -> None:
        """Try to extract multiple slot values from a single user answer.
        
        This prevents asking repeated questions — if the user volunteers
        extra info, we capture it immediately.
        """
        slot_queue = session.get("slot_queue", [])
        filled_slots = session.get("filled_slots", {})

        # Only look at unfilled slots (except the current one being answered)
        current_slot = slot_engine.get_next_empty_slot(slot_queue, filled_slots)
        unfilled_others = [s for s in slot_queue if s not in filled_slots and s != current_slot]

        if not unfilled_others or not user_text.strip():
            return

        # Combine with recent conversation for better extraction context
        recent_context = user_text
        history = session.get("conversation_history", [])
        if history:
            recent_context = "\n".join(history[-3:]) + "\n" + user_text

        extracted = llm_handler.extract_slots_from_description(
            recent_context,
            unfilled_others,
            slot_engine.slot_definitions
        )

        for slot_name, raw_value in extracted.items():
            if slot_name in filled_slots:
                continue
            slot_type = slot_engine.get_slot_type(slot_name)
            try:
                validation = validator.validate(slot_name, str(raw_value), slot_type)
                if validation["valid"]:
                    filled_slots[slot_name] = validation["cleaned_value"]
            except Exception:
                pass

        session["filled_slots"] = filled_slots

    def _ask_next_slot(self, session: Dict[str, Any]) -> str:
        """Generate the question for the next unfilled slot."""
        slot_queue = session.get("slot_queue", [])
        filled_slots = session.get("filled_slots", {})
        category_id = session.get("category_id", "")
        raw_description = session.get("raw_description", "")

        slot_name = slot_engine.get_next_empty_slot(slot_queue, filled_slots)
        if slot_name is None:
            return self._transition_to_review(
                session, session.get("category_id", ""), filled_slots
            )["bot_response"]

        slot_info = slot_engine.get_slot_definition(slot_name) or {}

        context = {
            "current_state": "FILLING_SLOTS",
            "slot_being_asked": slot_name,
            "category_label": self._get_category_label(category_id),
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
        """Move to REVIEWING state and show a structured complaint summary."""
        session["state"] = DialogueState.REVIEWING
        category_label = self._get_category_label(category_id)

        # Build structured key-value summary lines
        lines = []
        for slot, value in filled_slots.items():
            label = complaint_builder.SLOT_LABELS.get(slot, slot.replace("_", " ").title())
            if value == "true":
                display = "Yes"
            elif value == "false":
                display = "No"
            else:
                display = value
            lines.append(f"• **{label}**: {display}")

        raw_desc = session.get("raw_description", "")
        desc_snippet = (raw_desc[:120] + "…") if len(raw_desc) > 120 else raw_desc

        summary_parts = [
            "📋 **Complaint Summary**",
            f"**Complaint Type**: {category_label}",
            f"**Your Description**: {desc_snippet}",
        ]
        if lines:
            summary_parts.append("\n**Details collected:**")
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

        complaint_json = complaint_builder.build_complaint(session, complaint_id)
        severity_score = complaint_builder.compute_severity(
            session.get("filled_slots", {}),
            session.get("category_id")
        )
        complaint_json["severity_score"] = severity_score
        complaint_json["status"] = "pending"
        complaint_json["fir_number"] = None

        # Location routing (uses inline helper, no circular import)
        user_location = session.get("filled_slots", {}).get("incident_location", "")
        station = _route_to_station(user_location)
        complaint_json["assigned_station"] = station["name"]
        complaint_json["station_jurisdiction"] = station["jurisdiction"]

        complaint_store.save(complaint_id, complaint_json)

        try:
            phone = session.get("filled_slots", {}).get("victim_phone") or session.get("phone_number", "unknown")
            duplicate_checker.register(
                phone,
                complaint_id,
                session.get("filled_slots", {}),
                session.get("raw_description", "")
            )
        except Exception:
            pass

        victim_email = session.get("filled_slots", {}).get("victim_email", "")
        victim_name = session.get("filled_slots", {}).get("victim_name", "the complainant")
        category_label = self._get_category_label(session.get("category_id"))
        date_filed = datetime.now().strftime("%d %B %Y, %I:%M %p")

        # Generate email preview
        tracking_url = f"http://localhost:5173/track/{complaint_id}"
        email_preview = {
            "to": victim_email,
            "subject": f"NCRP Complaint Registered — {complaint_id}",
            "body": (
                f"Dear {victim_name},\n\n"
                f"Your cybercrime complaint has been successfully registered on the National Cybercrime Reporting Portal.\n\n"
                f"Complaint ID   : {complaint_id}\n"
                f"Complaint Type : {category_label}\n"
                f"Date Filed     : {date_filed}\n"
                f"Assigned To    : {station['name']}\n\n"
                f"You can track the status of your complaint at:\n{tracking_url}\n\n"
                f"Please save your Complaint ID — you will need it to follow up.\n"
                f"For urgent matters, call the National Cybercrime Helpline: 1930\n\n"
                f"Regards,\nNational Cybercrime Reporting Portal (NCRP)\ncybercrime.gov.in"
            )
        }

        bot_response = (
            f"✅ **Complaint submitted successfully!**\n\n"
            f"**Complaint ID: {complaint_id}**\n\n"
            f"An acknowledgement has been sent to **{victim_email}**. "
            f"You can track your complaint at `/track/{complaint_id}`.\n\n"
            f"Authorities at **{station['name']}** will review your complaint. "
            f"National Cybercrime Helpline: **1930**"
        )
        session["conversation_history"].append(f"Assistant: {bot_response}")
        session["email_preview"] = email_preview
        session["tracking_url"] = tracking_url

        return {
            "bot_response": bot_response,
            "progress": self._get_progress(session),
            "category_id": session.get("category_id"),
            "filled_slots": session.get("filled_slots", {}),
            "complaint_id": complaint_id,
            "email_preview": email_preview,
            "tracking_url": tracking_url,
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
            category_slots = slot_engine.load_slots(session["category_id"])
            seen = set()
            merged = []
            for s in category_slots:
                if s not in seen:
                    seen.add(s)
                    merged.append(s)
            slot_queue = merged

        return slot_engine.get_progress(slot_queue, filled_slots)

    def _get_category_label(self, category_id: Optional[str]) -> str:
        """Return a human-readable label for a category ID."""
        labels = {
            "UPI_FRAUD": "UPI / Bank Fraud",
            "VISHING": "Vishing (Fake Call / Voice Fraud)",
            "PHISHING": "Phishing (Fake Link / Website)",
            "INVESTMENT_SCAM": "Investment / Trading Scam",
            "SEXTORTION": "Sextortion / Sexual Blackmail",
            "JOB_FRAUD": "Job / Part-Time Work Fraud",
            "OTP_SIM_SWAP": "OTP Fraud / SIM Swap",
            "SOCIAL_MEDIA_FRAUD": "Social Media / Romance Scam",
            "LOTTERY_SCAM": "Lottery / Prize / Lucky Draw Scam",
            "ONLINE_SHOPPING_FRAUD": "Online Shopping / E-Commerce Fraud",
            "IDENTITY_THEFT": "Identity Theft / Document Misuse",
        }
        return labels.get(category_id, category_id or "Unknown")


# Global dialogue manager instance
dialogue_manager = DialogueManager()
