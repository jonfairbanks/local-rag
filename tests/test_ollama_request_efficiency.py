import unittest
from types import SimpleNamespace
from unittest.mock import Mock, call, patch

from llama_index.core.embeddings import MockEmbedding
from llama_index.core.schema import TextNode

import components.page_state as page_state
import components.tabs.settings as settings_tab
import utils.ollama as ollama
from utils.llama_index import OllamaEmbedding, ProgressReportingEmbedding, create_index


class ModelDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.state = {
            "browser_settings_restored": True,
            "ollama_endpoint": "http://localhost:11434",
        }
        self.client = Mock()
        self.client.list.return_value = {
            "models": [{"model": "chat"}, {"model": "embed"}]
        }
        self.client.show.side_effect = lambda name: {
            "capabilities": ["completion"] if name == "chat" else ["embedding"]
        }
        self.enterContext(patch.object(ollama.st, "session_state", self.state))
        self.create_client = self.enterContext(
            patch.object(ollama, "create_client", return_value=self.client)
        )
        self.enterContext(
            patch.object(page_state, "restore_settings_from_browser_storage")
        )

    def test_initial_discovery_scans_once_and_skips_cached_reruns(self):
        page_state.set_initial_state()
        page_state.set_initial_state()

        self.client.list.assert_called_once()
        self.assertEqual(self.client.show.call_args_list, [call("chat"), call("embed")])
        self.assertEqual(self.state["ollama_models"], ["chat"])
        self.assertEqual(self.state["ollama_embedding_models"], ["embed"])

    def test_changed_endpoint_replaces_both_lists_and_invalid_selections(self):
        page_state.set_initial_state()
        self.state["ollama_endpoint"] = "http://127.0.0.1:11434"
        self.client.list.return_value = {"models": [{"model": "new"}]}
        self.client.show.side_effect = lambda name: {
            "capabilities": ["completion", "embedding"]
        }

        page_state.set_initial_state()

        self.assertEqual(self.client.list.call_count, 2)
        self.create_client.assert_called_with("http://127.0.0.1:11434")
        for key in ("ollama_models", "ollama_embedding_models"):
            self.assertEqual(self.state[key], ["new"])
            self.assertEqual(self.state[f"{key}_endpoint"], "http://127.0.0.1:11434")
        self.assertEqual(self.state["selected_model"], "new")
        self.assertEqual(self.state["ollama_embedding_model"], "new")

    def test_failed_refresh_clears_lists_without_retrying_or_losing_preferences(self):
        page_state.set_initial_state()
        self.client.list.side_effect = RuntimeError("Fixture unavailable")

        settings_tab._refresh_models()

        self.assertEqual(self.client.list.call_count, 2)
        self.assertEqual(self.state["ollama_models"], [])
        self.assertEqual(self.state["ollama_embedding_models"], [])
        self.assertEqual(self.state["selected_model"], "chat")
        self.assertEqual(self.state["ollama_embedding_model"], "embed")

    def test_explicit_refresh_reads_current_models_once(self):
        page_state.set_initial_state()
        self.client.list.return_value = {"models": [{"model": "new"}]}
        self.client.show.side_effect = lambda name: {
            "capabilities": ["completion", "embedding"]
        }

        settings_tab._refresh_models()

        self.assertEqual(self.client.list.call_count, 2)
        self.assertEqual(self.state["ollama_models"], ["new"])
        self.assertEqual(self.state["ollama_embedding_models"], ["new"])
        self.assertEqual(self.state["selected_model"], "new")
        self.assertEqual(self.state["ollama_embedding_model"], "new")

    def test_refreshing_only_embedding_list_preserves_current_chat_list(self):
        page_state.set_initial_state()
        self.state["ollama_embedding_models_endpoint"] = "http://127.0.0.1:11434"
        self.client.list.return_value = {"models": [{"model": "replacement"}]}
        self.client.show.side_effect = lambda name: {"capabilities": ["embedding"]}

        page_state.set_initial_state()

        self.assertEqual(self.client.list.call_count, 2)
        self.assertEqual(self.state["ollama_models"], ["chat"])
        self.assertEqual(self.state["ollama_embedding_models"], ["replacement"])

    def test_capability_object_and_name_field_are_supported(self):
        self.client.list.return_value = {"models": [SimpleNamespace(name="both")]}
        self.client.show.side_effect = None
        self.client.show.return_value = SimpleNamespace(
            capabilities=["completion", "embedding"]
        )

        page_state.set_initial_state()

        self.assertEqual(self.state["ollama_models"], ["both"])
        self.assertEqual(self.state["ollama_embedding_models"], ["both"])
        self.client.show.assert_called_once_with("both")


class EmbeddingBatchTests(unittest.TestCase):
    def setUp(self):
        self.client = Mock()
        self.client.embed.side_effect = lambda model, input: SimpleNamespace(
            embeddings=[[float(len(text))] for text in input]
        )
        self.enterContext(
            patch.object(OllamaEmbedding, "_client", return_value=self.client)
        )
        self.model = OllamaEmbedding(
            model_name="fixture", base_url="http://localhost:11434", embed_batch_size=2
        )

    def test_batches_preserve_order_and_report_progress_including_partial_batch(self):
        progress = Mock()
        wrapped = ProgressReportingEmbedding(
            wrapped_model=self.model, progress_callback=progress, embed_batch_size=2,
            total_texts=5,
        )
        texts = ["a", "bb", "ccc", "dddd", "eeeee"]

        vectors = wrapped.get_text_embedding_batch(texts)

        self.assertEqual(vectors, [[1.0], [2.0], [3.0], [4.0], [5.0]])
        self.assertEqual(
            self.client.embed.call_args_list,
            [
                call(model="fixture", input=texts[:2]),
                call(model="fixture", input=texts[2:4]),
                call(model="fixture", input=texts[4:]),
            ],
        )
        self.assertEqual(progress.call_args_list, [call(2, 5), call(4, 5), call(5, 5)])

    def test_empty_batch_does_not_call_endpoint(self):
        self.assertEqual(self.model.get_text_embedding_batch([]), [])
        self.client.embed.assert_not_called()

    def test_wrong_vector_count_fails(self):
        self.client.embed.side_effect = None
        self.client.embed.return_value = SimpleNamespace(embeddings=[[1.0]])
        with self.assertRaisesRegex(ValueError, "unexpected number of embeddings"):
            self.model.get_text_embedding_batch(["first", "second"])

    def test_failed_batch_does_not_report_completion(self):
        progress = Mock()
        self.client.embed.side_effect = [
            SimpleNamespace(embeddings=[[1.0], [2.0]]),
            RuntimeError("Fixture unavailable"),
        ]
        wrapped = ProgressReportingEmbedding(
            wrapped_model=self.model, progress_callback=progress, embed_batch_size=2,
            total_texts=3,
        )

        with self.assertRaisesRegex(RuntimeError, "Fixture unavailable"):
            wrapped.get_text_embedding_batch(["a", "bb", "ccc"])

        progress.assert_called_once_with(2, 3)


class IndexProgressTests(unittest.TestCase):
    def test_progress_uses_full_total_across_index_insert_batches(self):
        for count in (2047, 2048, 2050):
            with self.subTest(count=count):
                nodes = [TextNode(text=f"Chunk {number}") for number in range(count)]
                progress = Mock()
                model = MockEmbedding(embed_dim=2, embed_batch_size=1024)
                with patch("utils.llama_index.run_transformations", return_value=nodes):
                    index = create_index([], model, 512, 64, progress)

                updates = [args.args for args in progress.call_args_list]
                self.assertEqual(updates[0], (0, count))
                self.assertEqual(updates[-1], (count, count))
                self.assertTrue(all(total == count for _, total in updates))
                completed = [done for done, _ in updates]
                self.assertEqual(completed, sorted(set(completed)))
                self.assertTrue(all(0 <= done <= count for done in completed))
                self.assertEqual(len(index.index_struct.nodes_dict), count)

    def test_failure_after_first_index_batch_never_reports_completion(self):
        nodes = [TextNode(text=f"Chunk {number}") for number in range(2050)]
        progress = Mock()
        model = MockEmbedding(embed_dim=2, embed_batch_size=1024)
        calls = 0

        def embed_text(instance, text):
            nonlocal calls
            calls += 1
            if calls == 2049:
                raise RuntimeError("Fixture unavailable")
            return [0.5, 0.5]

        with patch("utils.llama_index.run_transformations", return_value=nodes), patch.object(
            MockEmbedding, "_get_text_embedding", embed_text
        ):
            with self.assertRaisesRegex(Exception, "Fixture unavailable"):
                create_index([], model, 512, 64, progress)

        self.assertEqual(
            progress.call_args_list,
            [call(0, 2050), call(1024, 2050), call(2048, 2050)],
        )


if __name__ == "__main__":
    unittest.main()
