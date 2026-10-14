import unittest
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import Mock, patch

from streamlit.testing.v1 import AppTest

import components.chatbox as chatbox_module
from utils.ollama import context_chat


class ChatboxTests(unittest.TestCase):
    def setUp(self):
        self.engine = Mock()
        self.state = {"messages": [], "query_engine": self.engine}
        self.visible_chunks = []
        self.st = Mock(session_state=self.state)
        self.st.chat_input.return_value = "Question"
        self.st.chat_message.side_effect = lambda role: nullcontext()
        self.st.spinner.side_effect = lambda label: nullcontext()
        self.st.write_stream.side_effect = self.consume_stream

    def consume_stream(self, stream):
        for chunk in stream:
            self.visible_chunks.append(chunk)

    def run_chat(self):
        with patch.object(chatbox_module, "st", self.st):
            chatbox_module.chatbox()

    def assert_no_completed_answer(self):
        self.assertEqual(self.state["messages"], [{"role": "user", "content": "Question"}])
        self.st.error.assert_called_once_with("Response failed. Check Ollama and retry.")
        self.st.button.assert_called_once()

    def test_failure_before_first_chunk_is_reported_and_can_be_retried(self):
        self.engine.query.side_effect = RuntimeError("Ollama unavailable")
        self.run_chat()
        self.assert_no_completed_answer()
        self.assertEqual(self.state["chat_failure"], {"prompt": "Question", "partial": ""})
        self.st.caption.assert_not_called()

    def test_partial_failure_remains_visible_and_is_labeled_incomplete(self):
        def failing_stream():
            yield "First chunk"
            raise RuntimeError("Connection lost")

        self.engine.query.return_value = SimpleNamespace(response_gen=failing_stream())
        self.run_chat()
        self.assert_no_completed_answer()
        self.assertEqual(self.visible_chunks, ["First chunk"])
        self.assertEqual(self.state["chat_failure"]["partial"], "First chunk")
        self.st.caption.assert_called_once_with("Incomplete Response")

        self.st.chat_input.return_value = None
        self.st.reset_mock()
        self.run_chat()
        self.st.markdown.assert_called_once_with("First chunk")
        self.st.caption.assert_called_once_with("Incomplete Response")
        self.engine.query.assert_called_once_with("Question")

    def test_success_adds_one_complete_assistant_response(self):
        self.engine.query.return_value = SimpleNamespace(response_gen=iter(["An ", "answer"]))
        self.run_chat()
        self.assertEqual(self.state["messages"], [
            {"role": "user", "content": "Question"},
            {"role": "assistant", "content": "An answer"},
        ])
        self.assertNotIn("chat_failure", self.state)
        self.st.error.assert_not_called()

    def test_retry_reuses_the_existing_user_message_and_clears_failure(self):
        self.engine.query.side_effect = RuntimeError("Connection lost")
        self.run_chat()
        retry_callback = self.st.button.call_args.kwargs["on_click"]
        with patch.object(chatbox_module, "st", self.st):
            retry_callback()
        self.st.chat_input.return_value = None
        self.engine.query.side_effect = None
        self.engine.query.return_value = SimpleNamespace(response_gen=iter(["Recovered answer"]))
        self.run_chat()
        self.assertEqual(self.engine.query.call_args_list, [(('Question',), {}), (('Question',), {})])
        self.assertEqual(self.state["messages"], [
            {"role": "user", "content": "Question"},
            {"role": "assistant", "content": "Recovered answer"},
        ])
        self.assertNotIn("chat_failure", self.state)
        self.assertNotIn("chat_retry_requested", self.state)

    def test_new_question_after_failure_can_succeed(self):
        self.engine.query.side_effect = RuntimeError("Connection lost")
        self.run_chat()
        self.st.chat_input.return_value = "Another question"
        self.engine.query.side_effect = None
        self.engine.query.return_value = SimpleNamespace(response_gen=iter(["Answer"]))
        self.run_chat()
        self.assertEqual(self.state["messages"][-2:], [
            {"role": "user", "content": "Another question"},
            {"role": "assistant", "content": "Answer"},
        ])
        self.assertNotIn("chat_failure", self.state)

    def test_empty_response_is_reported_without_a_completed_answer(self):
        self.engine.query.return_value = SimpleNamespace(response_gen=iter([]))
        self.run_chat()
        self.assert_no_completed_answer()

    def test_context_chat_propagates_query_and_stream_errors(self):
        error = RuntimeError("Connection lost")
        self.engine.query.side_effect = error
        with self.assertRaises(RuntimeError) as raised:
            list(context_chat("Question", self.engine))
        self.assertIs(raised.exception, error)

        def failing_stream():
            yield "Partial"
            raise error

        self.engine.query.side_effect = None
        self.engine.query.return_value = SimpleNamespace(response_gen=failing_stream())
        stream = context_chat("Question", self.engine)
        self.assertEqual(next(stream), "Partial")
        with self.assertRaises(RuntimeError) as raised:
            next(stream)
        self.assertIs(raised.exception, error)

    def test_streamlit_retry_button_preserves_partial_output_and_user_history(self):
        app = AppTest.from_string("""
import streamlit as st
from components.chatbox import chatbox
st.session_state.setdefault("messages", [])
st.session_state["query_engine"] = True
for message in st.session_state["messages"]:
    st.chat_message(message["role"]).write(message["content"])
chatbox()
""")

        def failed_response(**kwargs):
            yield "Partial answer"
            raise RuntimeError("Connection lost")

        with patch.object(chatbox_module, "context_chat", failed_response):
            app.run()
            app.chat_input[0].set_value("Question").run()
            self.assertFalse(app.exception)
            self.assertEqual(app.error[0].value, "Response failed. Check Ollama and retry.")
            self.assertEqual(app.caption[0].value, "Incomplete Response")
            app.run()
            self.assertIn("Partial answer", [element.value for element in app.markdown])

        with patch.object(chatbox_module, "context_chat", return_value=iter(["Complete answer"])):
            app.button[0].click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["messages"], [
            {"role": "user", "content": "Question"},
            {"role": "assistant", "content": "Complete answer"},
        ])
        self.assertFalse(app.error)
        self.assertFalse(app.caption)

if __name__ == "__main__":
    unittest.main()
