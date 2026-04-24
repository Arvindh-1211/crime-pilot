"""Duplicate checker for detecting repeated complaints."""
import hashlib
import os
from typing import Dict, Any, List, Optional
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:
    SentenceTransformer = None
    cosine_similarity = None


class DuplicateChecker:
    """Checks for duplicate complaints using SHA-256 hash and semantic similarity."""

    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        """Initialize the duplicate checker."""
        self._model = None
        self._threshold = 0.85
        self._store: Dict[str, List[Dict[str, Any]]] = {}

    def initialize(self):
        """Initialize the embedding model."""
        if SentenceTransformer is None:
            raise RuntimeError("sentence-transformers package is not installed")

        if self._model is not None:
            return

        try:
            self._model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize embedding model: {e}")

    def _compute_hash(self, filled_slots: Dict[str, Any], raw_description: str) -> str:
        """Compute SHA-256 hash for exact duplicate detection.

        Creates fingerprint from key fields that would be identical in duplicates.
        """
        # Build fingerprint from incident-specific fields
        parts = []

        # Get incident date
        incident_date = filled_slots.get("incident_date", "")
        if incident_date:
            parts.append(str(incident_date))

        # Get amount
        amount = filled_slots.get("amount_lost", "") or filled_slots.get("amount_invested", "")
        if amount:
            parts.append(str(amount))

        # Get transaction/caller identifier
        txn_id = filled_slots.get("upi_transaction_id", "")
        if txn_id:
            parts.append(str(txn_id))

        caller = filled_slots.get("caller_number", "")
        if caller:
            parts.append(str(caller))

        suspect = filled_slots.get("suspect_upi_id", "") or filled_slots.get("suspect_contact", "")
        if suspect:
            parts.append(str(suspect))

        # Join and hash
        fingerprint = " | ".join(parts) + " | " + (raw_description or "").strip().lower()
        return hashlib.sha256(fingerprint.encode()).hexdigest()[:16]

    def _compute_embedding(self, filled_slots: Dict[str, Any], raw_description: str) -> Optional[np.ndarray]:
        """Compute embedding for semantic duplicate detection."""
        if self._model is None:
            return None

        # Build fingerprint from key fields
        parts = []

        incident_date = filled_slots.get("incident_date", "")
        if incident_date:
            parts.append(str(incident_date))

        amount = filled_slots.get("amount_lost", "") or filled_slots.get("amount_invested", "")
        if amount:
            parts.append(str(amount))

        raw_desc = (raw_description or "").strip().lower()
        if raw_desc:
            parts.append(raw_desc)

        fingerprint = " ".join(parts)

        if not fingerprint:
            return None

        return self._model.encode([fingerprint])[0]

    def check(self, phone_number: str, filled_slots: Dict[str, Any], raw_description: str) -> Dict[str, Any]:
        """Check if a complaint is a duplicate.

        Layer 1: SHA-256 hash comparison (exact match)
        Layer 2: Semantic embedding similarity (>= 0.85 threshold)

        Args:
            phone_number: User's phone number
            filled_slots: Currently filled slot values
            raw_description: Original user description

        Returns:
            Dict with keys:
                - is_duplicate: bool
                - matched_complaint_id: str or None
                - method: "exact" or "semantic" or None
        """
        # Initialize model if needed
        if self._model is None:
            try:
                self.initialize()
            except RuntimeError:
                return {"is_duplicate": False, "matched_complaint_id": None, "method": None}

        # Compute hash and embedding
        hash_value = self._compute_hash(filled_slots, raw_description)
        embedding = self._compute_embedding(filled_slots, raw_description)

        # Check phone number store for potential duplicates
        if phone_number not in self._store:
            return {"is_duplicate": False, "matched_complaint_id": None, "method": None}

        potential_matches = self._store[phone_number]

        # Layer 1: Exact hash match
        for match in potential_matches:
            if match.get("hash") == hash_value:
                return {
                    "is_duplicate": True,
                    "matched_complaint_id": match.get("complaint_id"),
                    "method": "exact"
                }

        # Layer 2: Semantic similarity
        if embedding is not None:
            for match in potential_matches:
                stored_embedding = match.get("embedding")
                if stored_embedding is not None:
                    # Reshape for cosine similarity
                    embedding_2d = embedding.reshape(1, -1)
                    stored_2d = np.array(stored_embedding).reshape(1, -1)

                    similarity = cosine_similarity(embedding_2d, stored_2d)[0][0]

                    if similarity >= self._threshold:
                        return {
                            "is_duplicate": True,
                            "matched_complaint_id": match.get("complaint_id"),
                            "method": "semantic"
                        }

        return {"is_duplicate": False, "matched_complaint_id": None, "method": None}

    def register(self, phone_number: str, complaint_id: str, filled_slots: Dict[str, Any], raw_description: str):
        """Register a new complaint in the duplicate checker store.

        Args:
            phone_number: User's phone number
            complaint_id: Generated complaint ID
            filled_slots: All filled slot values
            raw_description: Original user description
        """
        # Initialize model if needed
        if self._model is None:
            try:
                self.initialize()
            except RuntimeError:
                return

        # Compute hash and embedding
        hash_value = self._compute_hash(filled_slots, raw_description)
        embedding = self._compute_embedding(filled_slots, raw_description)

        # Store in phone number bucket
        if phone_number not in self._store:
            self._store[phone_number] = []

        entry = {
            "hash": hash_value,
            "complaint_id": complaint_id,
            "embedding": embedding.tolist() if embedding is not None else None
        }

        self._store[phone_number].append(entry)

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the store."""
        total_complaints = sum(len(complaints) for complaints in self._store.values())
        return {
            "phone_numbers": len(self._store),
            "total_complaints": total_complaints
        }

    def clear(self):
        """Clear all stored complaints."""
        self._store.clear()


# Global duplicate checker instance
duplicate_checker = DuplicateChecker()
