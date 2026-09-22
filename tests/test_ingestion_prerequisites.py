import unittest
from unittest.mock import patch

from components import ingestion_prerequisites


class IngestionPrerequisitesTests(unittest.TestCase):
    def test_custom_model_requires_valid_id_before_import(self):
        session = {
            "selected_model": "chat", "ollama_models": ["chat"],
            "embedding_backend": "Local Hugging Face", "embedding_model": "Other",
        }
        with patch.object(ingestion_prerequisites.st, "session_state", session):
            for model in [None, "", "../weights", "https://huggingface.co/org/model"]:
                session["other_embedding_model"] = model
                self.assertFalse(ingestion_prerequisites.ingestion_is_configured())
            session["other_embedding_model"] = "sentence-transformers/all-MiniLM-L6-v2"
            self.assertTrue(ingestion_prerequisites.ingestion_is_configured())

    def test_retained_model_names_do_not_enable_import_without_discovery(self):
        session = {"selected_model": "chat", "ollama_models": [], "embedding_backend": "Ollama", "ollama_embedding_model": "embedding", "ollama_embedding_models": []}
        with patch.object(ingestion_prerequisites.st, "session_state", session):
            self.assertFalse(ingestion_prerequisites.ingestion_is_configured())
