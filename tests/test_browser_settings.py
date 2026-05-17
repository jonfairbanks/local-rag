import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from utils.browser_settings import (
    apply_persisted_settings,
    browser_storage_payload,
    deserialize_persisted_settings,
    option_index,
    persist_settings_to_browser_storage,
    restore_settings_from_browser_storage,
    should_refresh_models_for_endpoint,
    serialize_persisted_settings,
)


class BrowserSettingsTests(unittest.TestCase):
    def test_apply_persisted_settings_coerces_supported_values(self):
        state = {}
        apply_persisted_settings(
            state,
            {
                "ollama_endpoint": "http://192.168.4.2:11434",
                "embedding_backend": "Local Hugging Face",
                "embedding_model": "Higher Quality (Qwen3-Embedding-0.6B)",
                "other_embedding_model": "custom/model",
                "ollama_embedding_model": "embeddinggemma",
                "top_k": "5",
                "chunk_size": "2048",
                "chunk_overlap": "256",
                "advanced": "true",
            },
        )

        self.assertEqual(state["ollama_endpoint"], "http://192.168.4.2:11434")
        self.assertEqual(state["top_k"], 5)
        self.assertEqual(state["chunk_size"], 2048)
        self.assertEqual(state["chunk_overlap"], 256)
        self.assertTrue(state["advanced"])

    def test_apply_persisted_settings_ignores_invalid_values(self):
        state = {}
        apply_persisted_settings(state, {"top_k": "not-a-number", "advanced": "maybe"})

        self.assertNotIn("top_k", state)
        self.assertNotIn("advanced", state)

    def test_apply_persisted_settings_ignores_empty_ollama_endpoint(self):
        state = {}
        apply_persisted_settings(state, {"ollama_endpoint": ""})

        self.assertNotIn("ollama_endpoint", state)

    def test_serialize_persisted_settings_only_includes_supported_keys(self):
        payload = serialize_persisted_settings(
            {
                "ollama_endpoint": "http://192.168.4.2:11434",
                "top_k": 4,
                "messages": ["do not persist"],
            }
        )

        self.assertEqual(
            payload,
            {
                "ollama_endpoint": "http://192.168.4.2:11434",
                "top_k": 4,
            },
        )

    def test_serialize_persisted_settings_omits_empty_ollama_endpoint(self):
        payload = serialize_persisted_settings(
            {
                "ollama_endpoint": "",
                "top_k": 4,
            }
        )

        self.assertEqual(payload, {"top_k": 4})

    def test_deserialize_persisted_settings_requires_json_object(self):
        self.assertEqual(deserialize_persisted_settings("not-json"), {})
        self.assertEqual(deserialize_persisted_settings("[1, 2, 3]"), {})

    def test_browser_storage_payload_writes_json_for_local_storage(self):
        payload = browser_storage_payload({"advanced": True, "top_k": 4})

        self.assertEqual(deserialize_persisted_settings(payload)["top_k"], 4)
        self.assertIn('"advanced": true', payload)
        self.assertNotIn("query_params", payload)

    def test_restore_hydrates_ollama_endpoint_and_model_settings_from_browser_storage(self):
        state = {}
        stored_settings = browser_storage_payload(
            {
                "ollama_endpoint": "http://192.168.4.2:11434",
                "selected_model": "gemma4:latest",
                "embedding_backend": "Ollama",
                "ollama_embedding_model": "embeddinggemma",
            }
        )
        storage_component = Mock(return_value={"value": stored_settings})

        with patch("utils.browser_settings.st", SimpleNamespace(session_state=state)), patch(
            "utils.browser_settings._browser_storage_component", storage_component
        ):
            restore_settings_from_browser_storage()

        self.assertTrue(state["browser_settings_restored"])
        self.assertEqual(state["ollama_endpoint"], "http://192.168.4.2:11434")
        self.assertEqual(state["selected_model"], "gemma4:latest")
        self.assertEqual(state["embedding_backend"], "Ollama")
        self.assertEqual(state["ollama_embedding_model"], "embeddinggemma")

    def test_persist_writes_ollama_endpoint_and_model_settings_after_restore(self):
        state = {
            "browser_settings_restored": True,
            "ollama_endpoint": "http://192.168.4.2:11434",
            "selected_model": "gemma4:latest",
            "embedding_backend": "Ollama",
            "ollama_embedding_model": "embeddinggemma",
            "embedding_model": "Default (gte-modernbert-base)",
            "messages": ["do not persist"],
        }
        storage_component = Mock()

        with patch("utils.browser_settings.st", SimpleNamespace(session_state=state)), patch(
            "utils.browser_settings._browser_storage_component", storage_component
        ):
            persist_settings_to_browser_storage()

        storage_component.assert_called_once()
        persisted_payload = storage_component.call_args.kwargs["value"]
        persisted_settings = deserialize_persisted_settings(persisted_payload)
        self.assertEqual(
            persisted_settings,
            {
                "ollama_endpoint": "http://192.168.4.2:11434",
                "embedding_backend": "Ollama",
                "ollama_embedding_model": "embeddinggemma",
                "embedding_model": "Default (gte-modernbert-base)",
                "selected_model": "gemma4:latest",
            },
        )

    def test_restore_stops_until_browser_local_storage_payload_is_available(self):
        state = {}
        storage_component = Mock(return_value=None)
        streamlit = SimpleNamespace(session_state=state, stop=Mock(side_effect=RuntimeError("stopped")))

        with patch("utils.browser_settings.st", streamlit), patch(
            "utils.browser_settings._browser_storage_component", storage_component
        ):
            with self.assertRaisesRegex(RuntimeError, "stopped"):
                restore_settings_from_browser_storage()

        streamlit.stop.assert_called_once()
        self.assertNotIn("browser_settings_restored", state)

    def test_persist_does_not_write_local_storage_before_browser_restore(self):
        state = {
            "ollama_endpoint": "http://localhost:11434",
            "selected_model": "gemma4:latest",
        }
        storage_component = Mock()

        with patch("utils.browser_settings.st", SimpleNamespace(session_state=state)), patch(
            "utils.browser_settings._browser_storage_component", storage_component
        ):
            persist_settings_to_browser_storage()

        storage_component.assert_not_called()

    def test_option_index_returns_persisted_model_position(self):
        self.assertEqual(option_index(["llama3", "qwen2"], "qwen2"), 1)

    def test_option_index_falls_back_to_first_option(self):
        self.assertEqual(option_index(["llama3", "qwen2"], "missing"), 0)
        self.assertIsNone(option_index([], "missing"))

    def test_should_refresh_models_for_endpoint_when_lists_missing(self):
        state = {"ollama_endpoint": "http://192.168.4.2:11434"}

        self.assertTrue(should_refresh_models_for_endpoint(state, "ollama_models"))

    def test_should_refresh_models_for_endpoint_when_endpoint_changed(self):
        state = {
            "ollama_endpoint": "http://192.168.4.2:11434",
            "ollama_models": [],
            "ollama_models_endpoint": "http://localhost:11434",
        }

        self.assertTrue(should_refresh_models_for_endpoint(state, "ollama_models"))

    def test_should_not_refresh_models_for_matching_endpoint(self):
        state = {
            "ollama_endpoint": "http://192.168.4.2:11434",
            "ollama_models": ["llama3"],
            "ollama_models_endpoint": "http://192.168.4.2:11434",
        }

        self.assertFalse(should_refresh_models_for_endpoint(state, "ollama_models"))


if __name__ == "__main__":
    unittest.main()
