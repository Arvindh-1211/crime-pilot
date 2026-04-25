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
from routes.complaint import route_to_station


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
    ANSWERING_SCENARIOS = "ANSWERING_SCENARIOS"
    DUPLICATE_CHECK = "DUPLICATE_CHECK"
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
        elif state == DialogueState.ANSWERING_SCENARIOS:
            return self._handle_answering_scenarios(session, user_text)
        elif state == DialogueState.DUPLICATE_CHECK:
            return self._handle_duplicate_check(session, user_text)
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
            # Fallback for robustness
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

        category_label = llm_handler._get_category_label(session["category_id"])

        next_slot = slot_engine.get_next_empty_slot(
            session["slot_queue"], session.get("filled_slots", {})
        )
        if next_slot is None:
            return self._transition_to_review(
                session, session["category_id"], session.get("filled_slots", {})
            )

        # Build dynamic intro and fetch dynamic scenario questions
        scenario_questions = llm_handler.get_scenario_questions(session["category_id"])
        
        intro_context = {
            "current_state": "CATEGORY_IDENTIFIED",
            "category_label": category_label,
            "raw_description": accumulated,
            "conversation_history": session.get("conversation_history", []),
        }
        intro = llm_handler.generate_response(intro_context)
        
        if scenario_questions:
            # Shift flow to scenario verification
            first_q = scenario_questions[0]
            bot_response = f"{intro}\n\n**Quick Question:** {first_q}"
            session["scenario_questions"] = scenario_questions
            session["scenario_index"] = 0
            session["scenario_answers"] = {}
            session["state"] = "ANSWERING_SCENARIOS" # New transient state handled by router
        else:
            # Direct to slot filling
            first_question = self._ask_next_slot(session)
            bot_response = f"{intro}\n\n{first_question}"

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

    def _handle_answering_scenarios(self, session: Dict[str, Any], user_text: str) -> Dict[str, Any]:
        """Process scenario answers and move to slot filling when done."""
        questions = session.get("scenario_questions", [])
        idx = session.get("scenario_index", 0)
        
        # Save the answer
        if idx < len(questions):
            q = questions[idx]
            answers = session.get("scenario_answers", {})
            answers[q] = user_text
            session["scenario_answers"] = answers
            # Append to raw description for better context
            existing = session.get("raw_description", "")
            session["raw_description"] = f"{existing}\nUser answered '{q}': {user_text}"
            
        # Move to next question
        idx += 1
        session["scenario_index"] = idx
        
        if idx < len(questions):
            # Ask the next scenario question
            next_q = questions[idx]
            bot_response = f"**Quick Question:** {next_q}"
            session["conversation_history"].append(f"Assistant: {bot_response}")
            return {
                "bot_response": bot_response,
                "progress": self._get_progress(session),
                "category_id": session.get("category_id"),
                "filled_slots": session.get("filled_slots", {}),
            }
        
        # Scenarios finished, extract any newly mentioned slots
        self._prefill_slots_from_description(session)
        
        # Transition to standard slot filling
        session["state"] = DialogueState.FILLING_SLOTS
        
        # Ask the first empty slot
        first_question = self._ask_next_slot(session)
        if not first_question:
            # Everything filled!
            return self._transition_to_review(session, session["category_id"], session.get("filled_slots", {}))
            
        bot_response = f"Thank you for those details. Now, let's gather a few specific points:\n\n{first_question}"
        session["conversation_history"].append(f"Assistant: {bot_response}")
        
        return {
            "bot_response": bot_response,
            "progress": self._get_progress(session),
            "category_id": session.get("category_id"),
            "filled_slots": session.get("filled_slots", {}),
        }

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

    def _transition_to_duplicate_check(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Run duplicate detection before review."""
        raw_description = session.get("raw_description", "")
        filled_slots = session.get("filled_slots", {})
        
        # Phone number simulation (in real app, from auth or initial prompt)
        phone_number = session.get("phone_number", "unknown_user")
        
        # Layer 1 & 2 Duplicate Check
        dup_result = duplicate_checker.check(phone_number, filled_slots, raw_description)
        
        if dup_result["is_duplicate"]:
            session["state"] = DialogueState.DUPLICATE_CHECK
            session["matched_complaint_id"] = dup_result["matched_complaint_id"]
            bot_response = (
                f"⚠️ **Duplicate Detected**\n\n"
                f"It looks like this incident was already reported (Ticket ID: {dup_result['matched_complaint_id']}). "
                f"Do you want to update that complaint, or file a new one?"
            )
            session["conversation_history"].append(f"Assistant: {bot_response}")
            return {
                "bot_response": bot_response,
                "progress": self._get_progress(session),
                "category_id": session.get("category_id"),
                "filled_slots": filled_slots,
            }
            
        return self._transition_to_review(session, session["category_id"], filled_slots)

    def _handle_duplicate_check(self, session: Dict[str, Any], user_text: str) -> Dict[str, Any]:
        """Handle response to duplicate detection prompt."""
        text = user_text.lower()
        if "new" in text or "file a new" in text or "no" in text:
            # Proceed to review as a new complaint
            return self._transition_to_review(session, session["category_id"], session.get("filled_slots", {}))
        else:
            # Update existing (mocking behavior for now)
            session["state"] = DialogueState.SUBMITTED
            bot_response = f"Got it. I will append this new information to your existing Ticket {session['matched_complaint_id']}."
            return {
                "bot_response": bot_response,
                "progress": 100,
                "category_id": session.get("category_id"),
                "filled_slots": session.get("filled_slots", {}),
                "is_complete": True,
            }

    def _calculate_severity(self, category_id: str, filled_slots: Dict[str, Any]) -> str:
        """Calculate severity score based on amount lost and category."""
        amount_lost = 0
        try:
            amt_str = filled_slots.get("amount_lost", "") or filled_slots.get("amount_invested", "0")
            # Strip non-numeric
            amt_num = "".join(filter(str.isdigit, str(amt_str)))
            if amt_num:
                amount_lost = float(amt_num)
        except:
            pass
            
        if amount_lost > 500000 or category_id == "SEXTORTION":
            return "Critical 🔴"
        elif amount_lost > 50000 or category_id in ["RANSOMWARE", "SIM_SWAP_FRAUD"]:
            return "High 🟠"
        elif amount_lost > 5000:
            return "Medium 🟡"
        return "Low 🟢"

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
        desc_snippet = (raw_desc[:120] + "...") if len(raw_desc) > 120 else raw_desc

        severity = self._calculate_severity(category_id, filled_slots)

        summary_parts = [
            f"📋 **Complaint Review & Summary**",
            f"**Complaint Type**: {category_label}",
            f"**Severity Rating**: {severity}",
            f"**Your Description**: {desc_snippet}",
        ]
        if lines:
            summary_parts.append("\n**Details collected:**")
            summary_parts.extend(lines)

        summary = "\n".join(summary_parts)
        bot_response = (
            f"{summary}\n\n"
            "Please review the details above.\n"
            "If everything is correct, say **'Submit Complaint'** to generate your official ticket.\n"
            "If you need to change anything, simply tell me what to update (e.g., 'Change the amount to 5000')."
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

        # Compute severity
        filled_slots = session.get("filled_slots", {})
        severity_score = complaint_builder.compute_severity(
            filled_slots,
            session.get("category_id")
        )
        complaint_json["severity_score"] = severity_score
        
        # Add metadata for Officer Dashboard
        complaint_json["complaint_id"] = complaint_id
        complaint_json["ncrp_number"] = complaint_id
        complaint_json["status"] = "pending"
        complaint_json["fir_number"] = None
        phone = session.get("phone_number", "unknown")
        complaint_json["phone_number"] = phone
        
        # Location routing
        user_location = filled_slots.get("location") or filled_slots.get("city") or filled_slots.get("state") or "Unknown"
        station = route_to_station(user_location)
        complaint_json["user_location"] = user_location
        complaint_json["assigned_station"] = station["name"]
        complaint_json["station_jurisdiction"] = station["jurisdiction"]

        # Store in shared complaint store
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

        edu_summary = llm_handler.generate_educational_summary(session.get("category_id", ""))
        
        station_name = station["name"] if "name" in station else str(station)
        
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
            f"✅ **Your complaint has been successfully submitted.**\n\n"
            f"🎫 **Tracking ID**: `{complaint_id}`\n"
            f"📍 **Routed To**: {station_name} Cyber Cell\n"
            f"🚨 **Severity Rating**: {severity_score}\n"
            f"⏳ **Status**: Received — Under Review\n\n"
            f"An acknowledgement has been sent to **{victim_email}**. "
            f"You can track your complaint at `/track/{complaint_id}`.\n\n"
            f"**Next Steps:**\n"
            f"You do not need to create an account. Simply enter your Tracking ID (`{complaint_id}`) on our homepage to check the status of your complaint at any time.\n"
            f"{edu_summary}"
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
