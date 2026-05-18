import unittest
from types import SimpleNamespace
from unittest.mock import patch

from utils.ollama import get_embedding_models, get_models


class OllamaTests(unittest.TestCase):
    def test_get_embedding_models_prefers_embeddinggemma_latest(self):
        state = {
            "ollama_endpoint": "http://localhost:11434",
            "ollama_embedding_model": "missing:latest",
        }
        client = SimpleNamespace(
            list=lambda: {
                "models": [
                    {"model": "nomic-embed-text:latest"},
                    {"model": "embeddinggemma:latest"},
                    {"model": "gemma4:latest"},
                ]
            },
            show=lambda model_name: {
                "capabilities": (
                    ["completion"]
                    if model_name == "gemma4:latest"
                    else ["embedding"]
                )
            },
        )

        with patch("utils.ollama.st", SimpleNamespace(session_state=state)), patch(
            "utils.ollama.create_client", return_value=client
        ):
            models = get_embedding_models()

        self.assertEqual(
            models,
            ["nomic-embed-text:latest", "embeddinggemma:latest"],
        )
        self.assertEqual(state["ollama_embedding_model"], "embeddinggemma:latest")

    def test_get_models_clears_stale_models_when_discovery_fails(self):
        state = {
            "ollama_endpoint": "",
            "ollama_models": ["gemma4:latest"],
        }

        with patch("utils.ollama.st", SimpleNamespace(session_state=state)), patch(
            "utils.ollama.create_client", side_effect=RuntimeError("bad endpoint")
        ):
            models = get_models()

        self.assertEqual(models, [])
        self.assertEqual(state["ollama_models"], [])


if __name__ == "__main__":
    unittest.main()
