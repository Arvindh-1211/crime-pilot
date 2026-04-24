"""Simple in-memory session store for chat sessions."""
import uuid
from typing import Optional, Dict, Any


class SessionStore:
    """In-memory dictionary-based session storage."""

    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def create_session(self, session_id: str = None, initial_data: Dict = None) -> str:
        """Create a new session with optional initial data."""
        if session_id is None:
            session_id = str(uuid.uuid4())

        if session_id in self._sessions:
            return session_id

        self._sessions[session_id] = {
            "created_at": str(uuid.uuid4())[:8],
            **(initial_data or {})
        }
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data by ID."""
        return self._sessions.get(session_id)

    def update_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """Update session data. Returns True if session exists."""
        if session_id not in self._sessions:
            return False
        self._sessions[session_id].update(data)
        return True

    def delete_session(self, session_id: str) -> bool:
        """Delete a session. Returns True if deleted."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def exists(self, session_id: str) -> bool:
        """Check if session exists."""
        return session_id in self._sessions


# Global session store instance
session_store = SessionStore()
