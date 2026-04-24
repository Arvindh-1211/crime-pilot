"""Slot Engine for managing slot filling during complaint construction."""
import json
import os
from typing import Dict, Any, List, Optional


class SlotEngine:
    """Engine for managing slot filling state and progress."""

    def __init__(self):
        """Initialize the slot engine and load slot definitions."""
        self.slot_definitions: Dict[str, Dict[str, Any]] = {}
        self._load_slot_definitions()

    def _load_slot_definitions(self):
        """Load slot definitions from data file."""
        definitions_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data", "slot_definitions.json"
        )
        try:
            with open(definitions_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.slot_definitions = data["slots"]
        except Exception as e:
            # Fallback minimal slot definitions
            self.slot_definitions = {}

    def load_slots(self, category_id: str) -> List[str]:
        """Load ordered list of slots for a given category.

        Returns mandatory slots first, then optional slots.
        """
        if category_id is None:
            return []

        # Load taxonomy to get category info
        taxonomy_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data", "fraud_taxonomy.json"
        )
        try:
            with open(taxonomy_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for cat in data["categories"]:
                    if cat["id"] == category_id:
                        # Return mandatory slots first, then optional
                        mandatory = cat.get("mandatory_slots", [])
                        optional = cat.get("optional_slots", [])
                        return mandatory + optional
        except Exception:
            pass

        return []

    def get_next_empty_slot(self, slot_queue: List[str], filled_slots: Dict[str, Any]) -> Optional[str]:
        """Get the next unfilled slot from the queue.

        Args:
            slot_queue: Ordered list of slot names to fill
            filled_slots: Dict of already filled slots

        Returns:
            Name of next unfilled slot, or None if all filled
        """
        for slot in slot_queue:
            if slot not in filled_slots or filled_slots[slot] is None:
                return slot
        return None

    def get_progress(self, slot_queue: List[str], filled_slots: Dict[str, Any]) -> Dict[str, Any]:
        """Get progress information for the slot filling process.

        Args:
            slot_queue: Ordered list of slot names to fill
            filled_slots: Dict of already filled slots

        Returns:
            Dict with keys:
                - filled_count: Number of filled slots
                - total_count: Total number of slots in queue
                - percentage: Percentage complete (0-100)
                - checklist: List of slot status objects
        """
        total_count = len(slot_queue)
        filled_count = sum(1 for slot in slot_queue if slot in filled_slots and filled_slots[slot] is not None)

        # Build checklist
        checklist = []
        for slot in slot_queue:
            is_filled = slot in filled_slots and filled_slots[slot] is not None
            slot_info = self.slot_definitions.get(slot, {})
            checklist.append({
                "slot": slot,
                "label": slot_info.get("question", f"Fill {slot}"),
                "filled": is_filled
            })

        percentage = int((filled_count / total_count) * 100) if total_count > 0 else 0

        return {
            "filled_count": filled_count,
            "total_count": total_count,
            "percentage": percentage,
            "checklist": checklist
        }

    def get_slot_definition(self, slot_name: str) -> Optional[Dict[str, Any]]:
        """Get definition for a specific slot."""
        return self.slot_definitions.get(slot_name)

    def is_slot_required(self, slot_name: str) -> bool:
        """Check if a slot is required."""
        slot_def = self.slot_definitions.get(slot_name, {})
        return slot_def.get("required", False)

    def get_slot_type(self, slot_name: str) -> str:
        """Get the validation type for a slot."""
        slot_def = self.slot_definitions.get(slot_name, {})
        return slot_def.get("type", "text")


# Global slot engine instance
slot_engine = SlotEngine()
