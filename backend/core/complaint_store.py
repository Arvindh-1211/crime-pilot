"""Shared in-memory complaint store accessible by both routes and dialogue manager, with disk persistence."""
from typing import Dict, Any, Optional
import json
import os
import threading

class ComplaintStore:
    """Persistent store for completed complaints."""

    def __init__(self):
        self._complaints: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        
        # Ensure data directory exists
        self._data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        os.makedirs(self._data_dir, exist_ok=True)
        self._file_path = os.path.join(self._data_dir, "complaints.json")
        
        self._load_from_disk()

    def _load_from_disk(self):
        """Load complaints from JSON file if it exists."""
        if os.path.exists(self._file_path):
            try:
                with open(self._file_path, "r", encoding="utf-8") as f:
                    self._complaints = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load complaints from disk: {e}")
                self._complaints = {}

    def _save_to_disk(self):
        """Save current complaints dictionary to JSON file."""
        try:
            with open(self._file_path, "w", encoding="utf-8") as f:
                json.dump(self._complaints, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save complaints to disk: {e}")

    def save(self, complaint_id: str, complaint_data: Dict[str, Any]) -> None:
        """Save a complaint and persist to disk."""
        with self._lock:
            self._complaints[complaint_id] = complaint_data
            self._save_to_disk()

    def get(self, complaint_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a complaint by ID."""
        with self._lock:
            return self._complaints.get(complaint_id)

    def list_all(self) -> list:
        """Return all complaints."""
        with self._lock:
            return list(self._complaints.values())

    def exists(self, complaint_id: str) -> bool:
        """Check if a complaint exists."""
        with self._lock:
            return complaint_id in self._complaints

# Global shared instance
complaint_store = ComplaintStore()
