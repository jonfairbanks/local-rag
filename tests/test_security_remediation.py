"""Bounded regression checks using harmless files and mocked network clients."""

from contextlib import nullcontext
import os
import inspect
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, Mock, patch
from zipfile import ZipFile

from llama_index.core import Document
from llama_index.core.embeddings import MockEmbedding
from llama_index.core.llms import MockLLM

from components.tabs import github_repo, settings
from utils import browser_settings, helpers, llama_index, ollama, rag_pipeline
from utils.settings_validation import (
    HF_MODEL_REVISIONS,
    validate_chunk_settings,
    validate_ollama_endpoint,
)


class StopSignal(BaseException):
    pass


def state():
    return {
        "selected_model": "chat",
        "ollama_endpoint": "http://localhost:11434",
        "system_prompt": "",
        "embedding_backend": "Ollama",
        "embedding_model": "Default (gte-modernbert-base)",
        "ollama_embedding_model": "embedding",
        "chunk_size": 1024,
        "chunk_overlap": 200,
        "top_k": 3,
        "chat_mode": "compact",
    }


class SettingsBoundaryTests(unittest.TestCase):
    def test_chunk_limits_and_ordinary_settings(self):
        self.assertEqual(validate_chunk_settings("1024", "200"), (1024, 200))
        self.assertEqual(validate_chunk_settings(8192, 2048), (8192, 2048))
        for size, overlap in [
            (255, 0),
            (8193, 0),
            (256, 129),
            (1024, -1),
            (True, 0),
            ("123456", 0),
        ]:
            with self.subTest(size=size, overlap=overlap), self.assertRaises(
                ValueError
            ):
                validate_chunk_settings(size, overlap)

    @patch.dict(os.environ, {}, clear=True)
    def test_endpoints_require_operator_allowlist(self):
        for endpoint in ["http://localhost:11434", "http://127.0.0.1:11434/"]:
            self.assertEqual(validate_ollama_endpoint(endpoint), endpoint.rstrip("/"))
        for endpoint in [
            "http://example.invalid:11434",
            "ftp://localhost:11434",
            "http://user@localhost:11434",
            "http://localhost:11434/path",
        ]:
            with self.subTest(endpoint=endpoint), self.assertRaises(ValueError):
                validate_ollama_endpoint(endpoint)
        with patch.dict(
            os.environ, {"LOCAL_RAG_OLLAMA_ENDPOINTS": "http://192.168.4.2:11434"}
        ):
            self.assertEqual(
                validate_ollama_endpoint("http://192.168.4.2:11434"),
                "http://192.168.4.2:11434",
            )

    def test_restored_options_cannot_bypass_validation(self):
        restored = {}
        browser_settings.apply_persisted_settings(
            restored,
            {
                "embedding_backend": "unsupported",
                "embedding_model": "Other",
                "chat_mode": "unsupported",
                "top_k": 99,
                "chunk_size": 256,
                "chunk_overlap": 200,
                "ollama_endpoint": "http://example.invalid:11434",
            },
        )
        self.assertEqual(restored, {
            "chunk_size": 1024, "chunk_overlap": 200,
            "embedding_model": "Other", "ollama_endpoint": "http://example.invalid:11434",
        })
        with patch.object(ollama.ollama, "Client") as client:
            self.assertFalse(ollama.create_client(restored["ollama_endpoint"]))
            client.assert_not_called()

    def test_diagnostics_exclude_sensitive_values(self):
        diagnostic = settings.sanitized_diagnostics(
            {
                "documents": ["private document"],
                "messages": ["private prompt"],
                "ollama_endpoint": "private endpoint",
                "llm": object(),
                "query_engine": object(),
            }
        )
        self.assertEqual(
            diagnostic,
            {"documents_loaded": True, "llm_ready": True, "index_ready": True},
        )

    def test_network_clients_disable_redirects_and_environment_proxies(self):
        with patch.object(ollama.ollama, "Client") as client:
            ollama.create_client("http://localhost:11434")
            self.assertFalse(client.call_args.kwargs["follow_redirects"])
            self.assertFalse(client.call_args.kwargs["trust_env"])
        with patch.object(ollama.ollama, "Client") as client:
            self.assertFalse(ollama.create_client("http://example.invalid:11434"))
            client.assert_not_called()


class ArchiveBoundaryTests(unittest.TestCase):
    def test_small_archive_passes_and_limits_reject_before_reader(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "book.epub"
            with ZipFile(path, "w") as archive:
                archive.writestr("mimetype", "application/epub+zip")
                archive.writestr("chapter.txt", "A small chapter.")
            self.assertEqual(helpers.validated_document_paths(directory), [path])
            for limit in [
                "MAX_ARCHIVE_MEMBERS",
                "MAX_ARCHIVE_EXPANDED_BYTES",
                "MAX_ARCHIVE_MEMBER_BYTES",
            ]:
                with self.subTest(limit=limit), patch.object(
                    helpers, limit, 1
                ), patch.object(llama_index, "SimpleDirectoryReader") as reader:
                    with self.assertRaisesRegex(Exception, "archive"):
                        llama_index.load_documents(directory)
                    reader.assert_not_called()

    def test_symbolic_links_are_not_parsed(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "source.txt").write_text("Ordinary document")
            (Path(directory) / "alias.txt").symlink_to(Path(directory) / "source.txt")
            with self.assertRaisesRegex(ValueError, "Symbolic"):
                helpers.validated_document_paths(directory)


class ModelIsolationTests(unittest.TestCase):
    def setUp(self):
        session_patch = patch.object(llama_index.st, "session_state", state())
        session_patch.start()
        self.addCleanup(session_patch.stop)

    def test_real_hugging_face_constructor_preserves_safe_loader_options(self):
        from llama_index.embeddings.huggingface import base
        from sentence_transformers import SentenceTransformer

        model = MagicMock()
        model.max_seq_length = 8192
        with patch.object(base, "SentenceTransformer", return_value=model) as loader:
            llama_index.setup_embedding_model("Alibaba-NLP/gte-modernbert-base")
        inspect.signature(SentenceTransformer.__init__).bind(
            None, *loader.call_args.args, **loader.call_args.kwargs
        )
        self.assertEqual(loader.call_args.kwargs["model_kwargs"], {"use_safetensors": True})
        self.assertFalse(loader.call_args.kwargs["trust_remote_code"])

    def test_two_query_engines_keep_their_own_models(self):
        first_embedding = MockEmbedding(embed_dim=4)
        second_embedding = MockEmbedding(embed_dim=8)
        first_llm, second_llm = MockLLM(), MockLLM()
        with patch.object(llama_index.st, "session_state", state()):
            first = llama_index.create_query_engine(
                [Document(text="First ordinary document.")],
                first_llm,
                first_embedding,
                1024,
                200,
            )
            second = llama_index.create_query_engine(
                [Document(text="Second ordinary document.")],
                second_llm,
                second_embedding,
                512,
                100,
            )
        self.assertIs(first._response_synthesizer._llm, first_llm)
        self.assertIs(second._response_synthesizer._llm, second_llm)
        self.assertIs(first.retriever._embed_model, first_embedding)
        self.assertIs(second.retriever._embed_model, second_embedding)
        self.assertTrue(str(first.query("What is the document about?")))

    def test_llm_creation_returns_independent_explicit_clients(self):
        with patch.object(ollama, "Ollama") as constructor, patch.object(
            ollama.ollama, "Client"
        ), patch.object(ollama.ollama, "AsyncClient"):
            ollama.create_ollama_llm("first", "http://localhost:11434", "First prompt")
            ollama.create_ollama_llm(
                "second", "http://127.0.0.1:11434", "Second prompt"
            )
        self.assertEqual(
            constructor.call_args_list[0].kwargs["base_url"], "http://localhost:11434"
        )
        self.assertEqual(
            constructor.call_args_list[1].kwargs["system_prompt"], "Second prompt"
        )

    def test_invalid_hugging_face_model_is_rejected_before_loading(self):
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding
        with patch("llama_index.embeddings.huggingface.HuggingFaceEmbedding", spec=HuggingFaceEmbedding) as loader:
            for model in ["../weights", "https://huggingface.co/org/model", "org/model/subdir", "/tmp/model"]:
                with self.subTest(model=model), self.assertRaises(ValueError):
                    llama_index.setup_embedding_model(model)
            loader.assert_not_called()

    def test_custom_model_reuse_is_scoped_to_session_and_configuration(self):
        first_state, second_state = {}, {}
        with patch("llama_index.embeddings.huggingface.HuggingFaceEmbedding", side_effect=lambda **kwargs: Mock()) as loader, patch("torch.cuda.is_available", return_value=False):
            with patch.object(llama_index.st, "session_state", first_state):
                first = llama_index.setup_embedding_model("sentence-transformers/all-MiniLM-L6-v2")
                self.assertIs(first, llama_index.setup_embedding_model("sentence-transformers/all-MiniLM-L6-v2"))
                loader.assert_called_once()
                self.assertEqual(loader.call_args.kwargs["revision"], "main")
                self.assertFalse(loader.call_args.kwargs["trust_remote_code"])
                self.assertEqual(loader.call_args.kwargs["model_kwargs"], {"use_safetensors": True})
                with patch("torch.cuda.is_available", return_value=True):
                    self.assertIsNot(first, llama_index.setup_embedding_model("sentence-transformers/all-MiniLM-L6-v2"))
                llama_index.setup_embedding_model("Alibaba-NLP/gte-modernbert-base")
                with patch.dict(HF_MODEL_REVISIONS, {"Alibaba-NLP/gte-modernbert-base": "different-revision"}):
                    llama_index.setup_embedding_model("Alibaba-NLP/gte-modernbert-base")
            with patch.object(llama_index.st, "session_state", second_state):
                self.assertIsNot(first, llama_index.setup_embedding_model("sentence-transformers/all-MiniLM-L6-v2"))
            self.assertEqual(loader.call_count, 5)

    def test_builtin_model_uses_safe_pinned_loader_options(self):
        loader = Mock()
        module = SimpleNamespace(HuggingFaceEmbedding=loader)
        with patch.dict(
            "sys.modules",
            {
                "llama_index.embeddings.huggingface": module,
                "torch": SimpleNamespace(
                    cuda=SimpleNamespace(is_available=lambda: False)
                ),
            },
        ):
            result = llama_index.setup_embedding_model(
                "Alibaba-NLP/gte-modernbert-base"
            )
        self.assertIs(result, loader.return_value)
        self.assertEqual(
            loader.call_args.kwargs["revision"],
            HF_MODEL_REVISIONS["Alibaba-NLP/gte-modernbert-base"],
        )
        self.assertFalse(loader.call_args.kwargs["trust_remote_code"])
        self.assertEqual(
            loader.call_args.kwargs["model_kwargs"], {"use_safetensors": True}
        )


class IngestionOwnershipTests(unittest.TestCase):
    def test_upload_cleanup_on_success_and_each_failure_stage(self):
        paths = []
        real_temporary_directory = tempfile.TemporaryDirectory

        def temporary_directory(**kwargs):
            temporary = real_temporary_directory(**kwargs)
            paths.append(Path(temporary.name))
            return temporary

        upload = SimpleNamespace(name="notes.txt", size=5, getbuffer=lambda: b"hello")
        for stage in [None, "llm", "embedding", "load", "index"]:
            session = state()
            previous = {"llm": object(), "query_engine": object(), "documents": [Document(text="Previous source")], "file_ingestion_stages": ["Index Ready"]}
            session.update(previous)
            streamlit = SimpleNamespace(
                session_state=session,
                spinner=lambda *args: nullcontext(),
                exception=Mock(),
                stop=Mock(side_effect=StopSignal),
            )
            with self.subTest(stage=stage), patch.object(
                rag_pipeline, "st", streamlit
            ), patch.object(
                rag_pipeline, "TemporaryDirectory", temporary_directory
            ), patch.object(
                ollama,
                "create_ollama_llm",
                side_effect=ValueError("test failure") if stage == "llm" else None,
            ), patch.object(
                llama_index,
                "setup_embedding_model",
                side_effect=(
                    ValueError("test failure") if stage == "embedding" else None
                ),
            ), patch.object(
                llama_index,
                "load_documents",
                side_effect=(
                    ValueError("test failure")
                    if stage == "load"
                    else lambda directory: [
                        Document(text=(Path(directory) / "notes.txt").read_text())
                    ]
                ),
            ), patch.object(
                llama_index,
                "create_query_engine",
                side_effect=ValueError("test failure") if stage == "index" else None,
            ):
                if stage is None:
                    self.assertIsNone(rag_pipeline.rag_pipeline([upload]))
                    self.assertEqual(session["documents"][0].text, "hello")
                else:
                    self.assertIsInstance(rag_pipeline.rag_pipeline([upload]), ValueError)
                    for key, value in previous.items():
                        self.assertIs(session[key], value)
            self.assertFalse(paths[-1].exists())
        self.assertEqual(len(paths), len(set(paths)))

    def test_control_flow_stop_keeps_previous_index_and_cleans_uploads(self):
        session = state()
        previous = {"llm": object(), "query_engine": object(), "documents": [Document(text="Previous source")]}
        session.update(previous)
        staged = []

        def stopped(**kwargs):
            staged.append(Path(kwargs["data_dir"]))
            raise StopSignal()

        upload = SimpleNamespace(name="notes.txt", size=5, getbuffer=lambda: b"hello")
        with patch.object(rag_pipeline.st, "session_state", session), patch.object(rag_pipeline, "_rag_pipeline", side_effect=stopped):
            with self.assertRaises(StopSignal):
                rag_pipeline.rag_pipeline([upload])
        for key, value in previous.items():
            self.assertIs(session[key], value)
        self.assertFalse(staged[0].exists())

    def test_real_index_with_progress_commits_after_cleanup_and_survives_bad_settings(self):
        session = state()
        session["embedding_backend"] = "Local Hugging Face"
        session["embedding_model"] = "Other"
        session["other_embedding_model"] = "sentence-transformers/all-MiniLM-L6-v2"
        upload = SimpleNamespace(name="notes.txt", size=5, getbuffer=lambda: b"hello")
        paths = []
        loader = llama_index.load_documents

        def load(directory):
            paths.append(Path(directory))
            self.assertIsNone(session.get("query_engine"))
            return loader(directory)

        with patch.object(rag_pipeline.st, "session_state", session), patch.object(ollama, "create_ollama_llm", return_value=MockLLM()), patch.object(llama_index, "setup_embedding_model", return_value=MockEmbedding(embed_dim=4)) as embedding, patch.object(llama_index, "load_documents", side_effect=load):
            self.assertIsNone(rag_pipeline.rag_pipeline([upload]))
            self.assertEqual(embedding.call_args.args[0], session["other_embedding_model"])
            self.assertFalse(paths[0].exists())
            engine = session["query_engine"]
            self.assertTrue(str(engine.query("What does the document say?")))
            session["chunk_size"] = 1
            self.assertIsInstance(rag_pipeline.rag_pipeline(documents=[Document(text="Replacement")]), ValueError)
            self.assertIs(session["query_engine"], engine)
            self.assertEqual(session["documents"][0].text, "hello")
            self.assertTrue(str(engine.query("Can I still query the previous document?")))

    def test_github_partial_clone_cleanup_on_stop(self):
        staged = []

        def failed_clone(repo, directory):
            staged.append(Path(directory))
            (Path(directory) / "partial.txt").write_text("temporary content")
            return False

        streamlit = MagicMock()
        streamlit.session_state = {"github_repo": "owner/repo"}
        streamlit.form_submit_button.return_value = True
        streamlit.stop.side_effect = StopSignal
        with patch.object(github_repo, "st", streamlit), patch.object(
            github_repo, "ingestion_is_configured", return_value=True
        ), patch.object(github_repo.rag, "render_pipeline_status"), patch.object(
            helpers, "validate_github_repo", return_value=True
        ), patch.object(
            helpers, "clone_github_repo", side_effect=failed_clone
        ):
            with self.assertRaises(StopSignal):
                github_repo.github_repo()
        self.assertFalse(staged[0].exists())


if __name__ == "__main__":
    unittest.main()
