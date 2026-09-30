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
    def test_blocked_endpoint_preserves_model_preferences_across_widget_reruns(self):
        from streamlit.testing.v1 import AppTest
        import json

        app = AppTest.from_string('''
import streamlit as st
from components.tabs.settings import settings
from components.page_state import ensure_valid_model_selections
from utils.browser_settings import restore_settings_from_browser_storage, serialize_persisted_settings
if "initialized" not in st.session_state:
    st.session_state.update(initialized=True, browser_settings_restored=True,
        ollama_endpoint="http://host.docker.internal:11434", ollama_models=[],
        selected_model="remember-chat", embedding_backend="Ollama", ollama_embedding_models=[],
        ollama_embedding_model="remember-embedding", embedding_model="Other",
        other_embedding_model="sentence-transformers/all-MiniLM-L6-v2", messages=[],
        advanced=False, top_k=3, chat_mode="compact", chunk_size=1024, chunk_overlap=200)
restore_settings_from_browser_storage()
ensure_valid_model_selections(st.session_state)
settings()
st.json(serialize_persisted_settings(st.session_state))
''').run()
        for _ in range(3):
            app.run()
            self.assertEqual(len(app.exception), 0)
            saved = json.loads(app.json[0].value)
            self.assertEqual(saved["selected_model"], "remember-chat")
            self.assertEqual(saved["ollama_embedding_model"], "remember-embedding")
            self.assertEqual(saved["other_embedding_model"], "sentence-transformers/all-MiniLM-L6-v2")
            self.assertIn("LOCAL_RAG_OLLAMA_ENDPOINTS", app.error[0].value)
        app.toggle(key="advanced").set_value(True).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.text_input(key="chunk_size").value, "1024")
        self.assertEqual(app.text_input(key="chunk_overlap").value, "200")

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
