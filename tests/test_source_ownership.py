import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from streamlit.testing.v1 import AppTest

from components.tabs import local_files
from components.tabs.github_repo import should_show_github_ingestion_status
from utils import rag_pipeline


class SourceOwnershipTests(unittest.TestCase):
    def setUp(self):
        self.upload = SimpleNamespace(
            name="notes.txt", size=5, type="text/plain",
            getvalue=lambda: b"hello", getbuffer=lambda: b"hello",
        )
        self.signature = local_files.uploaded_files_signature([self.upload])
        self.local_identity = ("local_files", self.signature)
        self.website_identity = ("website", ("https://example.com",))
        self.github_identity = ("github_repo", "owner/repo")
        self.local_engine = object()
        self.website_engine = object()
        self.state = {
            "processed_file_signature": self.signature,
            "processing_file_signature": None,
            "file_ingestion_stages": ["Index Ready"],
            "active_source": self.local_identity,
            "query_engine": self.local_engine,
            "documents": ["local"],
            "llm": object(),
        }

    def ingest(self, identity, engine, failure=None):
        result = {"query_engine": engine, "documents": [identity], "llm": object()}
        with patch.object(rag_pipeline.st, "session_state", self.state), patch.object(
            rag_pipeline, "_rag_pipeline", return_value=result, side_effect=failure
        ):
            return rag_pipeline.rag_pipeline(documents=["document"], source_identity=identity)

    def render_local_files(self, reimport=False):
        ui = MagicMock()
        ui.session_state = self.state
        ui.file_uploader.return_value = [self.upload]
        ui.button.return_value = reimport
        with patch.object(local_files, "st", ui), patch.object(
            local_files, "ingestion_is_configured", return_value=True
        ), patch.object(rag_pipeline.st, "session_state", self.state), patch.object(
            rag_pipeline, "_rag_pipeline",
            return_value={"query_engine": self.local_engine, "documents": ["local"], "llm": object()},
        ) as build, patch.object(rag_pipeline, "render_pipeline_status") as status:
            local_files.local_files()
        return ui, build, status

    def test_local_to_website_does_not_reimport_or_show_old_ready_status_on_rerun(self):
        self.assertIsNone(self.ingest(self.website_identity, self.website_engine))
        for _ in range(2):
            ui, build, status = self.render_local_files()
            build.assert_not_called()
            status.assert_not_called()
            ui.write.assert_not_called()
            ui.button.assert_called_once_with("Reimport Files", key="reimport_local_files")
            self.assertIs(self.state["query_engine"], self.website_engine)
            self.assertEqual(self.state["active_source"], self.website_identity)

    def test_explicit_reimport_restores_local_source_and_ready_status(self):
        self.ingest(self.website_identity, self.website_engine)
        ui, build, _ = self.render_local_files(reimport=True)
        build.assert_called_once()
        self.assertIs(self.state["query_engine"], self.local_engine)
        self.assertEqual(self.state["active_source"], self.local_identity)
        ui.write.assert_called_once_with("Your files are ready. Let's chat! 😎")

    def test_active_local_uploads_reuse_index_and_render_ready_status(self):
        ui, build, status = self.render_local_files()
        build.assert_not_called()
        status.assert_called_once()
        ui.button.assert_not_called()
        ui.write.assert_called_once()

    def test_retry_failed_reimport_processes_uploads_on_the_next_rerun(self):
        self.ingest(self.website_identity, self.website_engine)
        self.state["failed_file_signature"] = self.signature
        ui, build, _ = self.render_local_files(reimport=True)
        build.assert_not_called()
        ui.button.assert_called_once_with("Retry Import", key="retry_file_import")
        ui.rerun.assert_called_once()
        self.assertIs(self.state["query_engine"], self.website_engine)
        self.assertEqual(self.state["active_source"], self.website_identity)
        _, build, _ = self.render_local_files()
        build.assert_called_once()
        self.assertIs(self.state["query_engine"], self.local_engine)
        self.assertEqual(self.state["active_source"], self.local_identity)

    def test_github_status_disappears_when_local_files_replace_engine(self):
        self.ingest(self.github_identity, object())
        args = dict(current_repo="https://github.com/owner/repo", processed_repo="owner/repo",
                    ingestion_stages=["Index Ready"], query_engine=self.state["query_engine"],
                    active_source=self.state["active_source"])
        self.assertTrue(should_show_github_ingestion_status(**args))
        self.ingest(self.local_identity, self.local_engine)
        args.update(query_engine=self.state["query_engine"], active_source=self.state["active_source"])
        self.assertFalse(should_show_github_ingestion_status(**args))

    def test_failed_replacement_preserves_engine_source_and_stages(self):
        before = self.state.copy()
        error = self.ingest(self.website_identity, self.website_engine, ValueError("failed"))
        self.assertIsInstance(error, ValueError)
        self.assertEqual(self.state, before)

    def test_cleanup_failure_does_not_commit_new_source(self):
        before = self.state.copy()
        directory = MagicMock()
        directory.__enter__.return_value = "/private/tmp/unused-upload"
        directory.__exit__.side_effect = OSError("cleanup failed")
        with patch.object(rag_pipeline.st, "session_state", self.state), patch.object(
            rag_pipeline, "TemporaryDirectory", return_value=directory
        ), patch.object(rag_pipeline, "_rag_pipeline", return_value={"query_engine": object()}):
            error = rag_pipeline.rag_pipeline([self.upload], source_identity=self.local_identity)
        self.assertIsInstance(error, OSError)
        self.assertEqual(self.state, before)

    def test_streamlit_source_switch_rerenders_status_without_replacing_new_index(self):
        app = AppTest.from_string('''
import streamlit as st
from components.tabs.sources import sources
defaults = {
    "selected_model": "chat", "ollama_models": ["chat"],
    "embedding_backend": "Ollama", "ollama_embedding_model": "embed",
    "ollama_embedding_models": ["embed"], "query_engine": None,
    "active_source": None, "processed_file_signature": None,
    "processing_file_signature": None, "file_ingestion_stages": ["Index Ready"],
    "github_repo": "owner/repo", "processed_github_repo": None,
    "github_ingestion_stages": ["Index Ready"],
    "websites": ["https://example.com"], "new_website": "",
    "website_input_error": None, "website_ingestion_stages": ["Index Ready"],
}
for key, value in defaults.items():
    st.session_state.setdefault(key, value)
sources()
''')
        def build(**kwargs):
            if kwargs.get("status_state_key") == "website_ingestion_stages":
                engine = "website engine"
            elif kwargs.get("status_state_key") == "github_ingestion_stages":
                engine = "github engine"
            else:
                engine = "local engine"
            return {"query_engine": engine, "documents": [engine], "llm": "fixture"}

        with patch.object(local_files.st, "file_uploader", return_value=[self.upload]), patch.object(
            rag_pipeline, "_rag_pipeline", side_effect=build
        ), patch("utils.helpers.load_website_documents", return_value=["website"]), patch(
            "utils.helpers.validate_github_repo", return_value=True
        ), patch("utils.helpers.clone_github_repo", side_effect=lambda repo, directory: directory):
            app.run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state["active_source"], self.local_identity)
            app.button(key="process_website").click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state["query_engine"], "website engine")
            self.assertNotIn("Your files are ready. Let's chat! 😎", [item.value for item in app.markdown])
            self.assertIn("Site processing completed. Let's chat! 😎", [item.value for item in app.markdown])
            app.run()
            self.assertEqual(app.session_state["query_engine"], "website engine")
            app.button(key="reimport_local_files").click().run()
            self.assertEqual(app.session_state["query_engine"], "local engine")
            process_repo = next(button for button in app.button if button.label == "Process")
            process_repo.click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state["active_source"], self.github_identity)
            self.assertEqual(app.session_state["query_engine"], "github engine")
            self.assertEqual([item.value for item in app.markdown].count("Your files are ready. Let's chat! 😎"), 1)
            app.button(key="reimport_local_files").click().run()
            self.assertEqual(app.session_state["active_source"], self.local_identity)
            self.assertEqual([item.value for item in app.markdown].count("Your files are ready. Let's chat! 😎"), 1)


if __name__ == "__main__":
    unittest.main()
