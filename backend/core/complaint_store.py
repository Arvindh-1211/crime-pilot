"""Shared in-memory complaint store accessible by both routes and dialogue manager."""
from typing import Dict, Any, Optional


class ComplaintStore:
    """In-memory store for completed complaints."""

    def __init__(self):
        self._complaints: Dict[str, Dict[str, Any]] = {}

    def save(self, complaint_id: str, complaint_data: Dict[str, Any]) -> None:
        """Save a complaint."""
        self._complaints[complaint_id] = complaint_data

    def get(self, complaint_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a complaint by ID."""
        return self._complaints.get(complaint_id)

    def list_all(self) -> list:
        """Return all complaints."""
        return list(self._complaints.values())

    def exists(self, complaint_id: str) -> bool:
        """Check if a complaint exists."""
        return complaint_id in self._complaints


# Global shared instance
complaint_store = ComplaintStore()
