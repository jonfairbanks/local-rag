import unittest

from utils.browser_settings import (
    apply_persisted_settings,
    browser_storage_payload,
    deserialize_persisted_settings,
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

    def test_deserialize_persisted_settings_requires_json_object(self):
        self.assertEqual(deserialize_persisted_settings("not-json"), {})
        self.assertEqual(deserialize_persisted_settings("[1, 2, 3]"), {})

    def test_browser_storage_payload_writes_json_for_local_storage(self):
        payload = browser_storage_payload({"advanced": True, "top_k": 4})

        self.assertEqual(deserialize_persisted_settings(payload)["top_k"], 4)
        self.assertIn('"advanced": true', payload)
        self.assertNotIn("query_params", payload)


if __name__ == "__main__":
    unittest.main()
