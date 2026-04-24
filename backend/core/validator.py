"""Validator for slot values with multiple validation rules."""
import re
from datetime import datetime, date
from typing import Dict, Any, Optional


class Validator:
    """Validates slot values according to their type and rules."""

    def __init__(self):
        """Initialize the validator."""
        self._today = date.today()

    def validate(self, slot_name: str, value: Any, slot_type: str) -> Dict[str, Any]:
        """Validate a slot value.

        Args:
            slot_name: Name of the slot being validated
            value: The value to validate
            slot_type: Type of validation (date, amount, upi_id, phone, url, text, boolean)

        Returns:
            Dict with keys:
                - valid: bool
                - cleaned_value: str or None
                - error: str or None
        """
        # Handle None/null values
        if value is None:
            return {"valid": False, "cleaned_value": None, "error": "Value cannot be empty"}

        # Convert to string for validation
        value_str = str(value).strip() if not isinstance(value, str) else value.strip()

        # Check if empty
        if not value_str:
            return {"valid": False, "cleaned_value": None, "error": "Value cannot be empty"}

        # Route to appropriate validator
        validators = {
            "date": self._validate_date,
            "amount": self._validate_amount,
            "upi_id": self._validate_upi_id,
            "phone": self._validate_phone,
            "url": self._validate_url,
            "text": self._validate_text,
            "boolean": self._validate_boolean
        }

        validator_fn = validators.get(slot_type, self._validate_text)
        return validator_fn(value_str, slot_name)

    def _validate_date(self, value: str, slot_name: str) -> Dict[str, Any]:
        """Validate date format and that it's not in the future."""
        # Try multiple date formats
        formats = [
            "%d-%m-%Y",      # DD-MM-YYYY
            "%Y-%m-%d",      # YYYY-MM-DD
            "%d/%m/%Y",      # DD/MM/YYYY
            "%m/%d/%Y",      # MM/DD/YYYY
            "%d %B %Y",      # DD Month YYYY
            "%B %d, %Y",     # Month DD, YYYY
        ]

        # Handle relative dates like "yesterday", "2 days ago", "today"
        value_lower = value.lower()
        if value_lower in ["today", "ajee", "aaj"]:
            return {"valid": True, "cleaned_value": self._today.strftime("%Y-%m-%d"), "error": None}

        if value_lower in ["yesterday", "kal"]:
            from datetime import timedelta
            yest = self._today - timedelta(days=1)
            return {"valid": True, "cleaned_value": yest.strftime("%Y-%m-%d"), "error": None}

        if "ago" in value_lower:
            # Extract number from "X days ago" or "2 days ago"
            match = re.search(r'(\d+)\s*days?\s*ago', value_lower)
            if match:
                days = int(match.group(1))
                from datetime import timedelta
                past_date = self._today - timedelta(days=days)
                return {"valid": True, "cleaned_value": past_date.strftime("%Y-%m-%d"), "error": None}

        # Try parsing date formats
        for fmt in formats:
            try:
                parsed = datetime.strptime(value, fmt).date()
                if parsed > self._today:
                    return {"valid": False, "cleaned_value": None, "error": "Date cannot be in the future"}
                return {"valid": True, "cleaned_value": parsed.strftime("%Y-%m-%d"), "error": None}
            except ValueError:
                continue

        # Last resort: try any format and catch
        try:
            parsed = datetime.strptime(value, "%Y-%m-%d").date()
            if parsed > self._today:
                return {"valid": False, "cleaned_value": None, "error": "Date cannot be in the future"}
            return {"valid": True, "cleaned_value": parsed.strftime("%Y-%m-%d"), "error": None}
        except ValueError:
            pass

        return {"valid": False, "cleaned_value": None, "error": "Invalid date format. Please use DD-MM-YYYY or YYYY-MM-DD"}

    def _validate_amount(self, value: str, slot_name: str) -> Dict[str, Any]:
        """Validate monetary amount."""
        # Remove currency symbols, commas, and Indian amount notation
        cleaned = re.sub(r'[₹\s,]', '', value)
        cleaned = re.sub(r'\s*(lakh|k|thousand)\s*', '000', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\s*lakh\s*', '00000', cleaned, flags=re.IGNORECASE)

        # Try to extract a number
        match = re.search(r'(\d+)', cleaned)
        if not match:
            return {"valid": False, "cleaned_value": None, "error": "Please enter a valid number"}

        try:
            amount = int(match.group(1))
            if amount <= 0:
                return {"valid": False, "cleaned_value": None, "error": "Amount must be positive"}
            return {"valid": True, "cleaned_value": str(amount), "error": None}
        except ValueError:
            return {"valid": False, "cleaned_value": None, "error": "Invalid amount format"}

    def _validate_upi_id(self, value: str, slot_name: str) -> Dict[str, Any]:
        """Validate UPI ID format."""
        # UPI ID format: alphanumeric@bankname
        pattern = r'^[a-zA-Z0-9._-]+@[a-zA-Z][a-zA-Z0-9]+$'
        if re.match(pattern, value):
            return {"valid": True, "cleaned_value": value.lower(), "error": None}
        return {"valid": False, "cleaned_value": None, "error": "Invalid UPI ID format. Example: name@bank"}

    def _validate_phone(self, value: str, slot_name: str) -> Dict[str, Any]:
        """Validate Indian phone number format."""
        # Remove common prefixes and spaces
        cleaned = re.sub(r'[+\s\-]', '', value)

        # Check if it's an Indian mobile number
        # Should be 10 digits starting with 6-9, or 11 digits starting with 91
        if len(cleaned) == 10 and cleaned[0] in '6789':
            return {"valid": True, "cleaned_value": cleaned, "error": None}

        if len(cleaned) == 11 and cleaned.startswith('91'):
            return {"valid": True, "cleaned_value": cleaned, "error": None}

        if len(cleaned) == 12 and cleaned.startswith('0'):
            # Remove leading 0 for STD code
            return {"valid": True, "cleaned_value": cleaned[1:], "error": None}

        return {"valid": False, "cleaned_value": None, "error": "Invalid phone number. Please enter 10-digit Indian mobile (6-9开头)"}

    def _validate_url(self, value: str, slot_name: str) -> Dict[str, Any]:
        """Validate URL format."""
        # URL must start with http:// or https://
        if re.match(r'^https?://', value, re.IGNORECASE):
            return {"valid": True, "cleaned_value": value, "error": None}

        return {"valid": False, "cleaned_value": None, "error": "URL must start with http:// or https://"}

    def _validate_text(self, value: str, slot_name: str) -> Dict[str, Any]:
        """Validate general text input."""
        # Just check for non-empty after stripping
        if value:
            return {"valid": True, "cleaned_value": value, "error": None}
        return {"valid": False, "cleaned_value": None, "error": "Text cannot be empty"}

    def _validate_boolean(self, value: str, slot_name: str) -> Dict[str, Any]:
        """Validate boolean input (yes/no/haan/nahi)."""
        value_lower = value.lower()

        if value_lower in ["yes", "haan", "hai", "hain", "true", "1"]:
            return {"valid": True, "cleaned_value": "true", "error": None}

        if value_lower in ["no", "nahi", "nahi hai", "false", "0"]:
            return {"valid": True, "cleaned_value": "false", "error": None}

        return {"valid": False, "cleaned_value": None, "error": "Please answer Yes or No"}


# Global validator instance
validator = Validator()
