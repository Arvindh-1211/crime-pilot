"""LLM Handler using Google Gemini for chat responses."""
import os
import json
from typing import Dict, Any, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FRAUD_CATEGORIES = [
    "UPI_FRAUD – Unauthorized UPI transactions, fake QR codes, UPI ID impersonation",
    "VISHING – Voice/video call fraud, impersonation of bank/govt officials over phone",
    "PHISHING – Fake websites, emails, or SMS stealing credentials or financial data",
    "INVESTMENT_SCAM – Fake high-return investment schemes (crypto, forex, stocks)",
    "SEXTORTION – Blackmail using intimate/explicit video or images",
]

# ---------------------------------------------------------------------------
# Per-category scenario question sets
# These are asked one by one to help the user realise what happened to them
# and to surface details they may not have volunteered.
# ---------------------------------------------------------------------------
SCENARIO_QUESTIONS: Dict[str, List[str]] = {
    "VISHING": [
        "Did you receive a call from someone who claimed to be a bank official, police officer, or government employee?",
        "Did they say your account would be blocked, or that there was suspicious activity — creating a sense of urgency?",
        "Did you share your OTP, CVV, debit/credit card number, or internet banking password with the caller?",
        "Did the caller ask you to install any remote access app such as AnyDesk, TeamViewer, or Quick Support?",
        "Did you transfer money to an account number they provided, thinking it was for 'verification' or 'reversal'?",
    ],
    "UPI_FRAUD": [
        "Did you scan a QR code that someone sent you, expecting to receive money — but money was deducted instead?",
        "Did someone send you a UPI 'collect request' that you approved, not realising it would deduct money from your account?",
        "Did you receive an SMS or WhatsApp message with a link asking you to enter your UPI PIN or bank details?",
        "Did you share your UPI PIN, OTP, or mPIN with anyone over call or message?",
        "Did someone ask you to do a small test transaction first, and then disappear after you sent a larger amount?",
    ],
    "PHISHING": [
        "Did you click on a link received via SMS, email, or WhatsApp — for example, about KYC update, prize money, or a refund?",
        "Did the website you landed on look exactly like your bank's website, or a government portal like IRCTC or EPFO?",
        "Did you enter your internet banking username, password, OTP, or card details on that website?",
        "Did you receive a message saying you won a lucky draw, or that your bank account will be closed unless you verify immediately?",
        "After you submitted your details, did you notice any unauthorised transactions from your account?",
    ],
    "INVESTMENT_SCAM": [
        "Were you added to a WhatsApp or Telegram group where people were sharing screenshots of high profits from stocks or crypto?",
        "Did someone show you proof of large returns — like ₹50,000 becoming ₹2 lakhs — to convince you to invest?",
        "Did you initially receive a small 'profit' payout to build your trust, before you invested a much larger amount?",
        "When you tried to withdraw your money, did the platform ask you to pay taxes, GST, or 'upgrade fees' first?",
        "Did the platform eventually stop responding, or did the Telegram/WhatsApp group disappear after you invested?",
    ],
    "SEXTORTION": [
        "Did you receive a video call from an unknown number where an explicit or nude video was played on screen?",
        "During that call, did you expose yourself — even briefly — not realising your video was being recorded?",
        "Did they contact you afterwards threatening to send this recording to your contacts, family, or on social media?",
        "Did they demand money — through UPI, bank transfer, or gift cards — in exchange for deleting the video?",
        "Have you already made any payment to them, even a small one, hoping they would stop?",
    ],
}

# ---------------------------------------------------------------------------
# Secondary fraud indicators — used to detect if a second fraud exists
# ---------------------------------------------------------------------------
SECONDARY_FRAUD_INDICATORS: Dict[str, List[str]] = {
    "UPI_FRAUD": ["otp", "qr", "phonepe", "gpay", "paytm", "upi", "transfer", "transaction"],
    "VISHING": ["call", "officer", "bank", "sbi", "kyc", "blocked", "otp shared"],
    "PHISHING": ["link", "website", "clicked", "email", "sms", "credentials", "password"],
    "INVESTMENT_SCAM": ["invest", "profit", "telegram group", "returns", "crypto", "trading"],
    "SEXTORTION": ["video call", "nude", "blackmail", "morphed", "threat", "send to family"],
}

# ---------------------------------------------------------------------------
# Per-category educational summaries shown after complaint is submitted
# ---------------------------------------------------------------------------
FRAUD_EDUCATION: Dict[str, Dict[str, str]] = {
    # Existing ones kept for speed, others will be generated by LLM
    "VISHING": {
        "label": "Vishing (Voice Call Fraud / Impersonation)",
        "what_it_is": (
            "Vishing is a type of cybercrime where fraudsters call you pretending to be bank officials, "
            "RBI employees, police officers, or government agents. They create panic — telling you your "
            "account will be blocked, you have a pending arrest warrant, or there is suspicious activity "
            "on your account. Once you are scared, they trick you into sharing your OTP, card details, "
            "or transferring money to 'safe' accounts they control."
        ),
        "how_to_protect": (
            "No bank, RBI, or government agency ever asks for your OTP, CVV, or PIN over a call. "
            "If you receive such a call, hang up immediately and call your bank's official number. "
            "Never install any app a caller asks you to install."
        ),
        "legal_section": "Section 66C and 66D of the IT Act, 2000 — Identity Theft and Cheating by Impersonation.",
    },
    "UPI_FRAUD": {
        "label": "UPI Payment Fraud",
        "what_it_is": (
            "UPI fraud involves tricking you into sending money or approving payment requests under the "
            "impression that you are receiving money. Common tactics include fake QR codes that deduct "
            "instead of credit, 'collect requests' that look like incoming payments, and fake OTP requests "
            "via SMS or WhatsApp links."
        ),
        "how_to_protect": (
            "Remember: You never need to enter your UPI PIN to receive money. If someone asks you to scan "
            "a QR code or enter your PIN to get a refund or prize, it is a scam. Always verify the payee "
            "name before approving any UPI transaction."
        ),
        "legal_section": "Section 66C of IT Act, 2000 and Section 420 of IPC — Fraud and Cheating.",
    },
}


class LLMHandler:
    """Handles LLM interactions using Google Gemini API."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = "gemini-3.1-flash"  # Using 3.1 as requested
        self._genai_client = None
        self._initialized = False
        self.taxonomy: Dict[str, Any] = {}
        self._load_taxonomy()
        self._init_llm()

    def _load_taxonomy(self):
        """Load the large-scale taxonomy from data file."""
        taxonomy_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data", "fraud_taxonomy.json"
        )
        try:
            with open(taxonomy_path, "r", encoding="utf-8") as f:
                self.taxonomy = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load taxonomy: {e}")
            self.taxonomy = {"categories": []}

    def _get_category_label(self, category_id: Optional[str]) -> str:
        if not category_id:
            return "Unknown Category"
        for cat in self.taxonomy.get("categories", []):
            if cat["id"] == category_id:
                return cat["label"]
        return category_id.replace("_", " ").title()

    def _init_llm(self):
        if self.api_key is None:
            logger.warning("GEMINI_API_KEY not set. Using fallback mode.")
            self._initialized = False
            return
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._genai_client = genai
            self._initialized = True
        except ImportError:
            logger.warning("google-generativeai not installed. Using fallback mode.")
            self._initialized = False
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini: {e}. Using fallback mode.")
            self._initialized = False

    def _make_model(self, system_instruction: str):
        return self._genai_client.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_instruction
        )

    # ------------------------------------------------------------------
    # Fallback helpers
    # ------------------------------------------------------------------

    def _get_fallback_response(self, context: Dict[str, Any]) -> str:
        state = context.get("current_state", "")
        slot_being_asked = context.get("slot_being_asked", "")
        validation_error = context.get("validation_error", "")
        category_label = context.get("category_label", "")

        if validation_error:
            return f"Let me help you with that. {validation_error} Please try again."
        if slot_being_asked:
            return "Could you please provide the details I asked for?"
        if state == "GREETING":
            return "Hello! I'm your NCRP Cybercrime Assistant. Please describe what happened to you."
        if category_label:
            return f"Understood, this appears to be a {category_label} case. Let's collect the details."
        return "I'm here to help you file your cybercrime complaint. Please tell me what happened."

    # ------------------------------------------------------------------
    # Description assessment
    # ------------------------------------------------------------------

    def assess_description(
        self,
        accumulated_description: str,
        conversation_history: List[str],
    ) -> Dict[str, Any]:
        """Decide whether we have enough to classify, or ask a follow-up."""
        if not self._initialized:
            if len(accumulated_description.strip()) > 60:
                return {"sufficient": True}
            return {
                "sufficient": False,
                "follow_up": "Could you describe what happened in more detail? For example, how were you contacted and what did they ask you to do?",
            }

        categories_list = [f"{c['id']} – {c['description']}" for c in self.taxonomy.get("categories", [])]
        categories_str = "\n".join(f"- {c}" for c in categories_list)
        recent_history = "\n".join(conversation_history[-6:]) if conversation_history else ""

        prompt = f"""You are an intake officer for India's National Cybercrime Reporting Portal.

Your job: decide whether the user's description contains ENOUGH information to confidently classify 
their complaint into one of these categories:
{categories_str}

Conversation so far:
{recent_history}

Latest description: "{accumulated_description}"

Rules:
1. If the description clearly indicates what type of cyber fraud occurred (even if brief but specific), return {{"sufficient": true}}
2. If it is too vague (e.g. "I was scammed", "something happened online", platform name only), return {{"sufficient": false, "follow_up": "<one specific question>"}}
3. The follow-up must be SHORT (1 sentence), empathetic, and designed to determine the fraud TYPE only.
4. Never ask for personal data at this stage — only ask what is needed to understand the fraud TYPE.
5. Return ONLY valid JSON, no markdown.

Sufficient examples: "Someone called pretending to be my bank and I gave them my OTP", 
"I received a nude video call and they are blackmailing me", "I sent money to a fake investment app on Telegram"
Insufficient: "I was scammed on Instagram", "online fraud happened", "someone cheated me", "blackmail"

Return JSON only."""

        try:
            model = self._make_model("You are a cybercrime intake classifier. Return JSON only.")
            response = model.generate_content(prompt)
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            return json.loads(text)
        except Exception as e:
            logger.warning(f"assess_description failed: {e}")
            if len(accumulated_description.strip()) > 80:
                return {"sufficient": True}
            return {
                "sufficient": False,
                "follow_up": "Could you tell me more? For example, were you asked to pay money, share your OTP, or was someone threatening you?",
            }

    # ------------------------------------------------------------------
    # LLM-based classification
    # ------------------------------------------------------------------

    def classify_with_llm(self, description: str) -> Optional[str]:
        """Classify complaint into a fraud category. Returns category ID or None."""
        if not self._initialized:
            return None

        categories_list = [f"{c['id']}: {c['description']}" for c in self.taxonomy.get("categories", [])]
        categories_str = "\n".join(f"- {c}" for c in categories_list)
        valid_ids = [c["id"] for c in self.taxonomy.get("categories", [])]
        
        prompt = f"""Classify this cybercrime complaint into exactly ONE category from the list below.

Categories:
{categories_str}

Complaint: "{description}"

Return ONLY the category ID — one of: {', '.join(valid_ids)}
No explanation, no punctuation, just the ID."""

        try:
            model = self._make_model("You are a cybercrime classifier. Output only the category ID.")
            response = model.generate_content(prompt)
            result = response.text.strip().upper()
            for k in valid_ids:
                if k in result:
                    return k
            return None
        except Exception as e:
            logger.warning(f"LLM classification failed: {e}")
            return None

    # ------------------------------------------------------------------
    # NEW: Secondary fraud detection
    # ------------------------------------------------------------------

    def detect_secondary_frauds(
        self,
        description: str,
        primary_category: str,
        scenario_answers: Dict[str, str],
    ) -> List[str]:
        """Check if the description + scenario answers hint at additional fraud types
        beyond the primary category. Returns list of secondary category IDs."""
        if not self._initialized:
            return self._keyword_secondary_detect(description, primary_category)

        all_input = description + " " + " ".join(scenario_answers.values())
        other_categories = [c for c in ["UPI_FRAUD", "VISHING", "PHISHING", "INVESTMENT_SCAM", "SEXTORTION"]
                            if c != primary_category]

        prompt = f"""A cybercrime victim's primary complaint is: {primary_category}

Their full description and answers to follow-up questions:
"{all_input}"

Analyze if this description also contains clear evidence of any of these OTHER fraud types:
{', '.join(other_categories)}

Rules:
- Only flag a secondary fraud if there is EXPLICIT evidence in the text, not just possibility
- Example: Primary is VISHING but they also mention clicking a link and entering credentials = secondary PHISHING
- Example: Primary is INVESTMENT_SCAM but they also sent money via UPI after being scammed = secondary UPI_FRAUD
- Return ONLY a JSON array of category IDs that are clearly present, e.g. ["UPI_FRAUD"] or []
- If none, return []

Return JSON array only."""

        try:
            model = self._make_model("You are a cybercrime analyst. Return JSON array only.")
            response = model.generate_content(prompt)
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            result = json.loads(text)
            valid = ["UPI_FRAUD", "VISHING", "PHISHING", "INVESTMENT_SCAM", "SEXTORTION"]
            return [r for r in result if r in valid and r != primary_category]
        except Exception as e:
            logger.warning(f"Secondary fraud detection failed: {e}")
            return self._keyword_secondary_detect(description, primary_category)

    def _keyword_secondary_detect(self, description: str, primary: str) -> List[str]:
        """Fallback keyword-based secondary fraud detection."""
        desc_lower = description.lower()
        secondaries = []
        for cat, keywords in SECONDARY_FRAUD_INDICATORS.items():
            if cat == primary:
                continue
            if sum(1 for kw in keywords if kw in desc_lower) >= 2:
                secondaries.append(cat)
        return secondaries

    # ------------------------------------------------------------------
    # NEW: Scenario-based questioning
    # ------------------------------------------------------------------

    def get_scenario_questions(self, category_id: str) -> List[str]:
        """Return the list of scenario questions for a given fraud category."""
        # Use hardcoded ones if available for speed
        if category_id in SCENARIO_QUESTIONS:
            return SCENARIO_QUESTIONS[category_id]
        
        # Otherwise, generate them using Gemini 3.1
        if not self._initialized:
            return []
            
        try:
            label = self._get_category_label(category_id)
            model = self._make_model("You are a cybercrime expert. Return ONLY a JSON list of strings.")
            response = model.generate_content(
                f"Generate 5 specific yes/no scenario-based questions for a victim of '{label}'. "
                "These questions should help verify the fraud type and surface key details. "
                "Keep them short and empathetic. Return ONLY a JSON array of strings."
            )
            text = response.text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            return json.loads(text)
        except Exception as e:
            logger.warning(f"Failed to generate scenario questions: {e}")
            return [f"Did the incident involve {category_id.replace('_', ' ').lower()}?"]

    def generate_educational_summary(self, category_id: str) -> str:
        """Generate an educational message about the fraud category after submission."""
        # Use hardcoded ones if available
        edu = FRAUD_EDUCATION.get(category_id)
        if edu:
            return (
                f"\n\n---\n"
                f"📚 **Understanding Your Case: {edu['label']}**\n\n"
                f"**What happened to you:**\n{edu['what_it_is']}\n\n"
                f"**How to protect yourself in the future:**\n{edu['how_to_protect']}\n\n"
                f"**Applicable Law:** {edu['legal_section']}\n\n"
                f"**Remember:** You are the victim. Filing this complaint is the right thing to do."
            )

        # Otherwise, generate with Gemini
        if not self._initialized:
            return ""

        try:
            label = self._get_category_label(category_id)
            model = self._make_model("You are a helpful cybercrime legal assistant. English only.")
            response = model.generate_content(
                f"Generate a brief educational summary for a victim of '{label}'. "
                "Include: 1. A short explanation of what the fraud is. 2. Three specific tips for future protection. "
                "3. Mention the relevant section of the IT Act 2000 or IPC if applicable. "
                "Use Markdown formatting with emojis."
            )
            return f"\n\n---\n📚 **Understanding Your Case: {label}**\n\n{response.text.strip()}"
        except Exception:
            return ""

    # ------------------------------------------------------------------
    # Core response generation
    # ------------------------------------------------------------------

    def generate_response(self, context: Dict[str, Any]) -> str:
        """Generate a conversational response based on current dialogue context."""
        if not self._initialized:
            return self._get_fallback_response(context)

        system_prompt = """You are a compassionate, professional cybercrime complaint assistant for NCRP India 
(National Cybercrime Reporting Portal). You help Indian citizens file complaints for cyber incidents.

Your rules:
- Respond strictly in English only
- Be warm, empathetic, and patient — victims are often distressed
- Keep each message SHORT (2-3 sentences max)
- Ask ONE question at a time — never bundle multiple questions
- Acknowledge what the user has already told you; do NOT ask for information already provided
- Never fabricate or assume complaint data
- If the user has described their incident in detail, extract relevant info and only ask for what is missing
- When asking about location, ask for their city and state in India"""

        user_message = self._build_user_message(context)

        try:
            model = self._make_model(system_prompt)
            response = model.generate_content(user_message)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return self._get_fallback_response(context)

    def _build_user_message(self, context: Dict[str, Any]) -> str:
        state = context.get("current_state", "COLLECTING_DESC")
        slot_being_asked = context.get("slot_being_asked", "")
        validation_error = context.get("validation_error", "")
        category_label = context.get("category_label", "")
        raw_description = context.get("raw_description", "")
        already_provided = context.get("already_provided", {})

        parts = []
        if raw_description:
            parts.append(f"User's incident description: \"{raw_description}\"")
        if category_label:
            parts.append(f"Detected fraud category: {category_label}")
        parts.append(f"Current dialogue state: {state}")
        if already_provided:
            filled_summary = ", ".join(f"{k}={v}" for k, v in already_provided.items())
            parts.append(f"Information already collected from user: {filled_summary}")
        if slot_being_asked:
            parts.append(f"Next piece of information needed: {slot_being_asked}")
        if validation_error:
            parts.append(f"Validation error for previous answer: {validation_error}")
        history = context.get("conversation_history", [])
        if history:
            recent = history[-4:]
            parts.append("Recent conversation:\n" + "\n".join(recent))
        return "\n\n".join(parts)

    # ------------------------------------------------------------------
    # Slot extraction from free-text
    # ------------------------------------------------------------------

    def extract_slots_from_description(
        self,
        description: str,
        slots_needed: List[str],
        slot_definitions: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Extract slot values from a free-text description. Only extracts explicit values."""
        if not self._initialized or not description.strip():
            return {}

        slot_descriptions = []
        for slot in slots_needed:
            defn = slot_definitions.get(slot, {})
            question = defn.get("question", slot)
            hint = defn.get("hint", "")
            slot_descriptions.append(f'  "{slot}": {question} (e.g. {hint})')

        slots_json = "\n".join(slot_descriptions)

        prompt = f"""Given this cybercrime incident description:
\"\"\"{description}\"\"\"

Extract ONLY the following fields if a SPECIFIC, CONCRETE value is EXPLICITLY stated.

Rules:
- Dates: only if actual date/day mentioned (e.g. "24th April", "yesterday", "last Tuesday")
- Phone numbers: only if digits explicitly written
- UPI IDs: only if @id format explicitly written
- URLs: only if starts with http/https
- Platform/app names: only if specific app named (e.g. "WhatsApp", "Instagram", "Telegram")
- Amounts: only if number with currency context explicitly stated
- Location: extract city/state only if explicitly mentioned
- For ALL other fields: if not stated explicitly, OMIT

Fields to extract:
{slots_json}

Return ONLY a raw JSON object. Example: {{"incident_date": "24-05-2026", "platform_used": "WhatsApp"}}
If nothing meets strict criteria, return {{}}"""

        try:
            model = self._make_model(
                "You are a strict data extraction assistant. "
                "Only extract values explicitly stated. When in doubt, omit. Return only valid JSON."
            )
            response = model.generate_content(prompt)
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            extracted = json.loads(text)
            return {k: v for k, v in extracted.items() if k in slots_needed and v}
        except Exception as e:
            logger.warning(f"Slot extraction failed: {e}")
            return {}

    # ------------------------------------------------------------------
    # Category confirmation / slot request / error re-ask
    # ------------------------------------------------------------------

    def generate_category_confirmation(self, category: str, confidence: float) -> str:
        if not self._initialized:
            return f"Based on your description, this appears to be a case of {category}. Is that correct?"
        try:
            model = self._make_model(
                "You are a helpful cybercrime assistant. Confirm a detected fraud category. "
                "Be warm, brief (1-2 sentences), mention the category name clearly. English only."
            )
            response = model.generate_content(
                f"I classified the user's complaint as '{category}' with {confidence*100:.0f}% confidence. "
                "Generate a short, empathetic confirmation question asking if this is correct."
            )
            return response.text.strip()
        except Exception:
            return f"Based on your description, this looks like a case of **{category}**. Does that sound right to you?"

    def generate_slot_request(self, slot_name: str, slot_info: Dict[str, Any]) -> str:
        if not self._initialized:
            return slot_info.get("question", f"Please tell me about {slot_name}.")
        try:
            model = self._make_model(
                "You are a helpful complaint assistant. Ask ONE clear, friendly question to collect "
                "a specific piece of information. Keep it to 1-2 sentences. English only."
            )
            question = slot_info.get("question", f"Please tell me about {slot_name}")
            hint = slot_info.get("hint", "")
            prompt = f"Ask the user: {question}"
            if hint:
                prompt += f" (Example format: {hint})"
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception:
            return slot_info.get("question", f"Please tell me about {slot_name}.")

    def generate_error_reask(self, slot_name: str, error_message: str, slot_info: Dict[str, Any]) -> str:
        if not self._initialized:
            return f"That doesn't look quite right. {error_message} Please try again."
        try:
            model = self._make_model(
                "You are a helpful complaint assistant. When user input is invalid, politely explain "
                "what's wrong and ask them to try again. 1-2 sentences. English only."
            )
            question = slot_info.get("question", f"Please tell me about {slot_name}")
            hint = slot_info.get("hint", "")
            response = model.generate_content(
                f"The user's input was invalid: {error_message}. "
                f"The question was: {question}. "
                f"Hint for correct format: {hint}. "
                "Politely ask them to provide the correct information."
            )
            return response.text.strip()
        except Exception:
            return f"{error_message} Please try again with a valid input."

    # ------------------------------------------------------------------
    # NEW: Location-based routing
    # ------------------------------------------------------------------

    def get_nearest_cybercrime_office(self, city: str, state: str) -> Dict[str, str]:
        """Return the nearest cybercrime office details based on city/state.
        In production this would query a live database. This is a static lookup for demo."""
        office_map = {
            "bengaluru": {"city": "Bengaluru", "office": "Bengaluru City Police Cyber Crime Division", "address": "Carlton House, 1 Palace Road, Bengaluru – 560001", "phone": "080-22094480", "email": "cybercrime.blr@ksp.gov.in"},
            "bangalore": {"city": "Bengaluru", "office": "Bengaluru City Police Cyber Crime Division", "address": "Carlton House, 1 Palace Road, Bengaluru – 560001", "phone": "080-22094480", "email": "cybercrime.blr@ksp.gov.in"},
            "chennai": {"city": "Chennai", "office": "Tamil Nadu Police Cyber Crime Cell", "address": "Commissioner's Office, Vepery, Chennai – 600007", "phone": "044-28512774", "email": "cybercrime@tnpolice.gov.in"},
            "mumbai": {"city": "Mumbai", "office": "Mumbai Police Cyber Crime Cell", "address": "Bandra Kurla Complex, Mumbai – 400051", "phone": "022-26570827", "email": "cyberps@mumbaipolice.gov.in"},
            "delhi": {"city": "Delhi", "office": "Delhi Police Cyber Crime Unit", "address": "CGO Complex, Lodhi Road, New Delhi – 110003", "phone": "011-23490001", "email": "cybercrime@delhipolice.nic.in"},
            "hyderabad": {"city": "Hyderabad", "office": "Telangana State Cyber Security Bureau", "address": "Hyderabad – 500004", "phone": "040-27852274", "email": "tscsb@tspolice.gov.in"},
            "coimbatore": {"city": "Coimbatore", "office": "Coimbatore City Police Cyber Crime Cell", "address": "Commissioner's Office, Race Course Road, Coimbatore – 641018", "phone": "0422-2302200", "email": "cbepolice@tnpolice.gov.in"},
            "kolkata": {"city": "Kolkata", "office": "Kolkata Police Cyber Crime Division", "address": "Lalbazar, Kolkata – 700001", "phone": "033-22143004", "email": "cybercrime@kolkatapolice.gov.in"},
        }
        city_lower = city.lower().strip()
        for key, value in office_map.items():
            if key in city_lower or city_lower in key:
                return value
        # Default fallback
        return {
            "city": city,
            "office": f"{state} State Cyber Crime Cell",
            "address": f"Contact your nearest police station in {city}, {state}",
            "phone": "1930 (National Cybercrime Helpline)",
            "email": "cybercrime.gov.in",
        }

    def refine_speech(self, raw_text: str) -> str:
        """Refines raw speech-to-text transcript into clear, grammatically correct text without changing meaning."""
        if not self._initialized or not raw_text.strip():
            return raw_text

        prompt = f"""You are an assistant helping a victim refine their voice-transcribed cybercrime report.
Raw transcript: "{raw_text}"

Task: Correct grammar, fix speech-to-text errors (like homophones), and make the sentence clear and concise. 
DO NOT change the core meaning, add new facts, or change the tone significantly.
Return ONLY the refined text. No introductory words, no quotes."""

        try:
            model = self._make_model("You are a text refinement assistant. Return only refined text.")
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.warning(f"Speech refinement failed: {e}")
            return raw_text


# Global LLM handler instance
llm_handler = LLMHandler()