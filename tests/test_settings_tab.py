import unittest
from types import SimpleNamespace
from unittest.mock import patch

from components.tabs import settings as settings_tab


class _Container:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


class _StreamlitStub:
    def __init__(self, state):
        self.session_state = state
        self.selectbox_calls = []

    def header(self, *args, **kwargs):
        pass

    def caption(self, *args, **kwargs):
        pass

    def subheader(self, *args, **kwargs):
        pass

    def container(self, *args, **kwargs):
        return _Container()

    def text_input(self, *args, **kwargs):
        pass

    def selectbox(self, label, options, **kwargs):
        self.selectbox_calls.append((label, kwargs))
        return self.session_state.get(kwargs.get("key"))

    def button(self, *args, **kwargs):
        pass

    def toggle(self, *args, **kwargs):
        pass

    def write(self, *args, **kwargs):
        pass

    def download_button(self, *args, **kwargs):
        pass


class SettingsTabTests(unittest.TestCase):
    def test_keyed_selectboxes_do_not_pass_explicit_default_indexes(self):
        state = {
            "advanced": False,
            "ollama_endpoint": "http://localhost:11434",
            "ollama_models": ["llama3:8b", "gemma4:latest"],
            "selected_model": "gemma4:latest",
            "embedding_backend": "Ollama",
            "ollama_embedding_models": ["nomic-embed-text", "embeddinggemma"],
            "ollama_embedding_model": "embeddinggemma",
            "messages": [],
        }
        streamlit = _StreamlitStub(state)

        with patch("components.tabs.settings.st", streamlit):
            settings_tab.settings()

        keyed_selectboxes = {
            kwargs["key"]: kwargs
            for _, kwargs in streamlit.selectbox_calls
            if "key" in kwargs
        }
        self.assertNotIn("index", keyed_selectboxes["selected_model"])
        self.assertNotIn("index", keyed_selectboxes["ollama_embedding_model"])


if __name__ == "__main__":
    unittest.main()
