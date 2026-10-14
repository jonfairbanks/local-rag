import os
from pathlib import Path
import subprocess
import sys
import textwrap
import unittest


class LocalModelInitializationTests(unittest.TestCase):
    def test_explicit_local_models_work_without_mutating_openai_key(self):
        script = textwrap.dedent("""
            import os
            import socket
            from types import SimpleNamespace
            from unittest.mock import Mock, patch

            expected_key = os.environ.get("OPENAI_API_KEY")
            with patch.object(socket.socket, "connect", side_effect=AssertionError("Unexpected network request")):
                from llama_index.core import Document
                from utils.llama_index import create_query_engine, setup_embedding_model
                from utils.ollama import create_ollama_llm

                assert os.environ.get("OPENAI_API_KEY") == expected_key
                client = Mock()
                client.embed.side_effect = lambda **kwargs: SimpleNamespace(
                    embeddings=[[1.0, 0.0] for _ in (
                        [kwargs["input"]] if isinstance(kwargs["input"], str) else kwargs["input"]
                    )]
                )
                client.show.return_value = SimpleNamespace(modelinfo={"fixture.context_length": 4096})
                client.chat.return_value = iter([
                    {"message": {"role": "assistant", "content": "Local "}},
                    {"message": {"role": "assistant", "content": "answer"}},
                ])
                with patch("ollama.Client", return_value=client), patch(
                    "utils.llama_index.st.session_state", {"top_k": 1, "chat_mode": "compact"}
                ):
                    embedding = setup_embedding_model("fixture-embed", "Ollama", "http://localhost:11434")
                    llm = create_ollama_llm("fixture-chat", "http://localhost:11434")
                    engine = create_query_engine(
                        [Document(text="The local fixture contains an answer.")],
                        llm, embedding, 512, 64,
                    )
                    retrieved = engine.retrieve("What does the fixture contain?")
                    assert len(retrieved) == 1
                    assert "local fixture" in retrieved[0].node.text
                    response = engine.query("What does the fixture contain?")
                    chunks = list(response.response_gen)
                    assert "".join(chunks) == "Local answer", repr(chunks)
                    assert response.source_nodes[0].node.node_id == retrieved[0].node.node_id
                    assert client.embed.call_count == 3
                    client.chat.assert_called_once()
                    assert client.chat.call_args.kwargs["stream"] is True
                    assert client.chat.call_args.kwargs["model"] == "fixture-chat"
                assert os.environ.get("OPENAI_API_KEY") == expected_key
                print("Local model initialization and streaming passed")
        """)
        for key in (None, "fixture-sentinel-key"):
            with self.subTest(key_is_set=key is not None):
                environment = os.environ.copy()
                environment.pop("OPENAI_API_KEY", None)
                if key is not None:
                    environment["OPENAI_API_KEY"] = key
                result = subprocess.run(
                    [sys.executable, "-c", script],
                    cwd=Path(__file__).resolve().parents[1],
                    env=environment,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("Local model initialization and streaming passed", result.stdout)


if __name__ == "__main__":
    unittest.main()
