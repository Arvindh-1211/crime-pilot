"""Intent Classifier using sentence-transformers for fraud category detection."""
import json
import os
from typing import Dict, Any, List, Optional
import numpy as np

# Imports deferred to initialize() to prevent blocking server startup
class IntentClassifier:
    """Classify incoming messages into fraud categories using semantic similarity."""

    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        """Initialize the classifier with the sentence-transformer model."""
        self.model = None
        self.category_embeddings: Dict[str, np.ndarray] = {}
        self.categories: Dict[str, Dict[str, Any]] = {}
        self._initialized = False
        self._load_fraud_taxonomy()

    def _load_fraud_taxonomy(self):
        """Load fraud taxonomy from data file."""
        taxonomy_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data", "fraud_taxonomy.json"
        )
        try:
            with open(taxonomy_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.categories = {cat["id"]: cat for cat in data["categories"]}
        except Exception as e:
            # Default fallback categories if taxonomy loading fails
            self.categories = {
                "UPI_FRAUD": {
                    "id": "UPI_FRAUD",
                    "label": "UPI Fraud",
                    "keywords": ["upi fraud", "upi transaction", "unauthorized"]
                },
                "VISHING": {
                    "id": "VISHING",
                    "label": "Vishing",
                    "keywords": ["phone call", "voice phishing", "call"]
                },
                "PHISHING": {
                    "id": "PHISHING",
                    "label": "Phishing",
                    "keywords": ["fake website", "email", "url"]
                }
            }

    def initialize(self):
        """Load and initialize the embedding model. Must be called before classify."""
        if self._initialized:
            return

        try:
            from sentence_transformers import SentenceTransformer
            global cosine_similarity
            from sklearn.metrics.pairwise import cosine_similarity
        except ImportError:
            raise RuntimeError("sentence-transformers package is not installed")

        try:
            self.model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
            self._build_category_embeddings()
            self._initialized = True
        except Exception as e:
            raise RuntimeError(f"Failed to initialize intent classifier: {e}")

    def _build_category_embeddings(self):
        """Create embeddings for each category using label and keywords."""
        for cat_id, cat_data in self.categories.items():
            # Combine label with keywords for richer embedding
            text = cat_data["label"] + " " + " ".join(cat_data.get("keywords", []))
            embedding = self.model.encode([text])[0]
            self.category_embeddings[cat_id] = embedding

    def classify(self, text: str) -> Dict[str, Any]:
        """Classify the input text into a fraud category.

        Args:
            text: The user's message or description

        Returns:
            Dict with keys:
                - category_id: The detected category ID
                - confidence: Confidence score (0-1)
                - needs_confirmation: True if confidence < 0.55
        """
        if not self._initialized or self.model is None:
            return {"category_id": None, "confidence": 0, "needs_confirmation": True}

        # Encode the input text
        text_embedding = self.model.encode([text])[0]

        # Calculate cosine similarity with each category
        category_ids = list(self.category_embeddings.keys())
        embeddings_matrix = np.array([self.category_embeddings[cat_id] for cat_id in category_ids])

        similarities = cosine_similarity([text_embedding], embeddings_matrix)[0]

        # Find best match
        best_idx = np.argmax(similarities)
        best_category_id = category_ids[best_idx]
        confidence = float(similarities[best_idx])

        # Needs confirmation if confidence is low
        needs_confirmation = confidence < 0.55

        return {
            "category_id": best_category_id,
            "confidence": round(confidence, 4),
            "needs_confirmation": needs_confirmation
        }

    def get_category_info(self, category_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific category."""
        return self.categories.get(category_id)

    def get_all_categories(self) -> List[Dict[str, Any]]:
        """Get all category definitions."""
        return list(self.categories.values())


# Global classifier instance
intent_classifier = IntentClassifier()
