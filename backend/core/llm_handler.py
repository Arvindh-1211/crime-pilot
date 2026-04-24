"""LLM Handler using Google Gemini 1.5 Flash for chat responses."""
import os
from typing import Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMHandler:
    """Handles LLM interactions using Google Gemini API."""

    def __init__(self, api_key: str = None):
        """Initialize the LLM handler.

        Args:
            api_key: Gemini API key. If not provided, reads from GEMINI_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = "gemini-1.5-flash"
        self._genai_client = None
        self._initialized = False
        self._init_llm()

    def _init_llm(self):
        """Initialize the Gemini client."""
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
            logger.warning("google-generativeai package not installed. Using fallback mode.")
            self._initialized = False
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini: {e}. Using fallback mode.")
            self._initialized = False

    def _get_fallback_response(self, context: Dict[str, Any]) -> str:
        """Generate a fallback response when LLM is unavailable."""
        state = context.get("current_state", "")
        slot_being_asked = context.get("slot_being_asked", "")
        validation_error = context.get("validation_error", "")
        category_label = context.get("category_label", "")

        if validation_error:
            return f"Let me help you with that. {validation_error} Please try again with a different input."

        if slot_being_asked:
            return "I'm ready to help you file your cybercrime complaint. Could you please provide the details I asked for?"

        if state == "GREETING":
            return "Namaste! I'm your NCRP Cybercrime Assistant. I'll help you file a complaint for cyber incidents. What type of cybercrime did you experience?"

        if category_label:
            return f"Understood, this appears to be a {category_label} case. Let's collect some details about the incident."

        return "I'm here to help you with your cybercrime complaint. Please let me know what happened."

    def generate_response(self, context: Dict[str, Any]) -> str:
        """Generate a response using the LLM.

        Args:
            context: Dict containing:
                - current_state: Current dialogue state
                - slot_being_asked: Slot currently being asked
                - validation_error: Any validation error (optional)
                - category_label: Detected category (optional)
                - user_name: User's name (optional)
                - conversation_history: Previous messages (optional)

        Returns:
            Generated response string
        """
        # If LLM not initialized, return fallback
        if not self._initialized:
            return self._get_fallback_response(context)

        # Build the prompt
        system_prompt = """You are an empathetic cybercrime complaint assistant for NCRP India.
You are helping Indian citizens file complaints on the official National Cybercrime Portal.

Your role:
- Be warm, patient, and supportive
- Mix English and Hindi naturally (Hinglish) when appropriate
- Keep responses concise and helpful
- Never fabricate complaint data
- Ask one question at a time
- Be empathetic to victims

Generate a SINGLE short, warm, helpful message in the tone of a patient government helpline officer."""

        user_message = self._build_user_message(context)

        try:
            model = self._genai_client.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_prompt
            )

            response = model.generate_content(user_message)
            return response.text.strip()

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return self._get_fallback_response(context)

    def _build_user_message(self, context: Dict[str, Any]) -> str:
        """Build the user message from context."""
        state = context.get("current_state", "COLLECTING_DESC")
        slot_being_asked = context.get("slot_being_asked", "")
        validation_error = context.get("validation_error", "")
        category_label = context.get("category_label", "")

        parts = []

        if category_label:
            parts.append(f"Detected category: {category_label}")

        parts.append(f"Current state: {state}")

        if slot_being_asked:
            parts.append(f"Slot being asked: {slot_being_asked}")

        if validation_error:
            parts.append(f"Validation error: {validation_error}")

        # Add conversation history if available
        history = context.get("conversation_history", [])
        if history:
            parts.append(f"Previous conversation: {' | '.join(history[-3:])}")

        return " ".join(parts)

    def generate_category_confirmation(self, category: str, confidence: float) -> str:
        """Generate confirmation message for detected category."""
        if not self._initialized:
            return f"I understand this is about {category}. Let me confirm: Is this a case of {category}?"

        try:
            model = self._genai_client.GenerativeModel(
                model_name=self.model_name,
                system_instruction="You are a helpful assistant. Confirm the detected fraud category with the user. Keep it warm and brief."
            )

            response = model.generate_content(
                f"I detected this as {category} with {confidence*100:.1f}% confidence. "
                f"Please confirm: Is this accurate?"
            )
            return response.text.strip()

        except Exception:
            return f"I understand this is about {category}. Is this correct? Please confirm."

    def generate_slot_request(self, slot_name: str, slot_info: Dict[str, Any]) -> str:
        """Generate a request for a specific slot."""
        if not self._initialized:
            return slot_info.get("question", f"Please tell me about {slot_name}.")

        try:
            model = self._genai_client.GenerativeModel(
                model_name=self.model_name,
                system_instruction="You are a helpful complaint assistant. Ask one question at a time for complaint details. Keep it clear and brief."
            )

            question = slot_info.get("question", f"Please tell me about {slot_name}")
            hint = slot_info.get("hint", "")

            prompt = f"Ask the user: {question}"
            if hint:
                prompt += f" Example: {hint}"

            response = model.generate_content(prompt)
            return response.text.strip()

        except Exception:
            return slot_info.get("question", f"Please tell me about {slot_name}.")

    def generate_error_reask(self, slot_name: str, error_message: str, slot_info: Dict[str, Any]) -> str:
        """Generate message when slot validation fails."""
        if not self._initialized:
            return f"Oops! {error_message} Please try again."

        try:
            model = self._genai_client.GenerativeModel(
                model_name=self.model_name,
                system_instruction="You are a helpful complaint assistant. When user input is invalid, ask them to provide correct information in a friendly way."
            )

            question = slot_info.get("question", f"Please tell me about {slot_name}")
            hint = slot_info.get("hint", "")

            response = model.generate_content(
                f"User provided invalid input: {error_message}. "
                f"Original question was: {question}. "
                f"Helpful hint: {hint}. "
                f"Ask the user again politely to provide the correct information."
            )
            return response.text.strip()

        except Exception:
            return f"{error_message} Please try again with a valid input."


# Global LLM handler instance
llm_handler = LLMHandler()
