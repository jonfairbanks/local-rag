import unittest
from unittest.mock import patch

from components.page_state import (
    default_chat_model,
    ensure_valid_model_selections,
    set_initial_state,
)


class PageStateTests(unittest.TestCase):
    def test_default_chat_model_prefers_gemma4_latest(self):
        self.assertEqual(
            default_chat_model(["llama3:8b", "gemma4:latest"]),
            "gemma4:latest",
        )

    def test_ensure_valid_model_selections_repairs_inconsistent_chat_model(self):
        state = {
            "selected_model": "missing:latest",
            "ollama_models": ["gemma4:latest"],
            "embedding_backend": "Local Hugging Face",
        }

        ensure_valid_model_selections(state)

        self.assertEqual(state["selected_model"], "gemma4:latest")

    def test_ensure_valid_model_selections_clears_missing_ollama_embedding_model(self):
        state = {
            "selected_model": "gemma4:latest",
            "ollama_models": ["gemma4:latest"],
            "embedding_backend": "Ollama",
            "ollama_embedding_model": "embeddinggemma",
            "ollama_embedding_models": [],
        }

        ensure_valid_model_selections(state)

        self.assertIsNone(state["ollama_embedding_model"])

    def test_initial_state_uses_persisted_endpoint_before_model_discovery(self):
        state = {}

        def restore_from_local_storage():
            state.update(
                {
                    "browser_settings_restored": True,
                    "ollama_endpoint": "http://192.168.4.2:11434",
                    "selected_model": "gemma4:latest",
                    "embedding_backend": "Ollama",
                    "ollama_embedding_model": "embeddinggemma",
                }
            )

        with patch("components.page_state.st.session_state", state), patch(
            "components.page_state.restore_settings_from_browser_storage",
            side_effect=restore_from_local_storage,
        ), patch(
            "components.page_state.get_models", return_value=["gemma4:latest"]
        ) as get_models, patch(
            "components.page_state.get_embedding_models",
            return_value=["embeddinggemma"],
        ) as get_embedding_models:
            set_initial_state()

        get_models.assert_called_once()
        get_embedding_models.assert_called_once()
        self.assertEqual(state["ollama_endpoint"], "http://192.168.4.2:11434")
        self.assertEqual(state["ollama_models_endpoint"], "http://192.168.4.2:11434")
        self.assertEqual(
            state["ollama_embedding_models_endpoint"],
            "http://192.168.4.2:11434",
        )
        self.assertEqual(state["selected_model"], "gemma4:latest")
        self.assertEqual(state["ollama_embedding_model"], "embeddinggemma")


if __name__ == "__main__":
    unittest.main()
