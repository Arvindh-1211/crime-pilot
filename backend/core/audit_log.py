"""Audit trail — immutable log of all officer actions."""
from datetime import datetime
from typing import List, Dict, Any


class AuditLog:
    """In-memory append-only audit log.
    
    Production: replace with a DB-backed append-only table.
    """

    def __init__(self):
        self._entries: List[Dict[str, Any]] = []

    def record(
        self,
        officer_username: str,
        officer_badge: str,
        complaint_id: str,
        action: str,
        notes: str = "",
    ) -> Dict[str, Any]:
        """Append an audit entry and return it."""
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "officer_username": officer_username,
            "officer_badge": officer_badge,
            "complaint_id": complaint_id,
            "action": action,      # e.g. "ACCEPTED", "REJECTED", "FIR_ASSIGNED", "TRANSFERRED"
            "notes": notes,
        }
        self._entries.append(entry)
        return entry

    def get_for_complaint(self, complaint_id: str) -> List[Dict[str, Any]]:
        return [e for e in self._entries if e["complaint_id"] == complaint_id]

    def get_all(self) -> List[Dict[str, Any]]:
        return list(reversed(self._entries))   # newest first

    def get_summary(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for e in self._entries:
            counts[e["action"]] = counts.get(e["action"], 0) + 1
        return counts


# Global singleton
audit_log = AuditLog()
