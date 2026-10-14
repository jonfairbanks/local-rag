import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

import requests

from components.tabs import website
from utils import helpers, rag_pipeline


def upload(name):
    return SimpleNamespace(name=name, size=1, getbuffer=lambda: b"x")


def response(*, redirect=False, headers=None, chunks=None):
    result = Mock(is_redirect=redirect, encoding="utf-8")
    result.headers = headers or {"Content-Type": "text/plain"}
    result.iter_content.return_value = [b"hello"] if chunks is None else chunks
    return result


class UploadCollisionTests(unittest.TestCase):
    def test_duplicate_and_case_variant_names_are_rejected_before_staging(self):
        for names in [("notes.txt", "notes.txt"), ("Notes.txt", "notes.TXT")]:
            previous_engine = object()
            previous_stages = ["Index Ready"]
            session = {"query_engine": previous_engine,
                       "file_ingestion_stages": previous_stages}
            with self.subTest(names=names), patch.object(
                rag_pipeline.st, "session_state", session
            ), patch.object(rag_pipeline, "TemporaryDirectory") as staging, patch.object(
                helpers, "save_uploaded_file"
            ) as save:
                error = rag_pipeline.rag_pipeline(uploaded_files=[upload(n) for n in names])
            self.assertIsInstance(error, ValueError)
            self.assertIn("filenames collide", str(error))
            staging.assert_not_called()
            save.assert_not_called()
            self.assertIs(session["query_engine"], previous_engine)
            self.assertEqual(session["file_ingestion_stages"], previous_stages)

    def test_distinct_names_remain_valid(self):
        helpers.validate_uploaded_files([upload("notes.txt"), upload("other.txt")])


class WebsiteStateTests(unittest.TestCase):
    def setUp(self):
        self.urls = [f"https://example.com/{i}" for i in range(5)]
        self.session = {"websites": list(self.urls), "new_website": "example.com/5"}
        self.state_patch = patch.object(website.st, "session_state", self.session)
        self.state_patch.start()
        self.addCleanup(self.state_patch.stop)

    def test_sixth_url_is_rejected_without_mutating_list_or_input(self):
        website.add_website_from_input()
        self.assertEqual(self.session["websites"], self.urls)
        self.assertEqual(self.session["new_website"], "example.com/5")
        self.assertIn("At most 5", self.session["website_input_error"])

    def test_duplicate_addition_validates_full_deduplicated_list(self):
        self.session["new_website"] = "example.com/2"
        with patch.object(helpers, "_validate_public_http_url", side_effect=lambda url: url) as validate:
            website.add_website_from_input()
        self.assertEqual(validate.call_count, 5)
        self.assertEqual(self.session["websites"], self.urls)
        self.assertEqual(self.session["new_website"], "")
        self.assertIsNone(self.session["website_input_error"])

    def test_invalid_existing_url_prevents_partial_list_update(self):
        self.session["websites"] = ["https://example.com", "https://localhost"]
        with patch.object(helpers, "_validate_public_http_url", side_effect=["https://example.com", ValueError("Blocked URL")]):
            website.add_website_from_input()
        self.assertEqual(self.session["websites"], ["https://example.com", "https://localhost"])
        self.assertEqual(self.session["new_website"], "example.com/5")
        self.assertEqual(self.session["website_input_error"], "Blocked URL")

    def test_remove_and_clear_allow_recovery_from_over_limit_state(self):
        self.session["websites"].append("https://example.com/5")
        self.session["website_input_error"] = "At most 5"
        website.remove_website("https://example.com/5")
        self.assertEqual(self.session["websites"], self.urls)
        self.assertIsNone(self.session["website_input_error"])
        website.clear_websites()
        self.assertEqual(self.session["websites"], [])
        self.assertIsNone(self.session["website_input_error"])

    def test_ui_registers_remove_and_clear_callbacks(self):
        ui = MagicMock(session_state=self.session)
        ui.columns.side_effect = lambda *args: (MagicMock(), MagicMock())
        ui.button.return_value = False
        with patch.object(website, "st", ui), patch.object(website, "ingestion_is_configured", return_value=True):
            website.website()
        callbacks = [call.kwargs for call in ui.button.call_args_list]
        remove = [kwargs for kwargs in callbacks if kwargs.get("on_click") is website.remove_website]
        self.assertEqual([kwargs["args"][0] for kwargs in remove], self.urls)
        self.assertTrue(any(kwargs.get("on_click") is website.clear_websites for kwargs in callbacks))


class WebsiteCleanupTests(unittest.TestCase):
    def fetch(self, responses):
        session = Mock()
        session.get.side_effect = responses
        with patch.object(helpers.requests, "Session", return_value=session), patch.object(
            helpers, "_validate_public_http_url", side_effect=lambda url: url
        ):
            try:
                return helpers.load_website_documents(["https://example.com"])
            finally:
                session.close.assert_called_once_with()
                for result in responses:
                    if not isinstance(result, Exception):
                        result.close.assert_called_once_with()

    def test_success_closes_response_and_session(self):
        documents = self.fetch([response(chunks=[b"", b"hello"])])
        self.assertEqual(documents[0].text, "hello")
        self.assertEqual(documents[0].metadata["source"], "https://example.com")

    def test_redirect_response_closes_before_next_request(self):
        redirect = response(redirect=True, headers={"Location": "/next"})
        success = response()
        session = Mock()

        def get(url, **kwargs):
            self.assertFalse(kwargs["allow_redirects"])
            self.assertTrue(kwargs["stream"])
            self.assertEqual(kwargs["timeout"], helpers.WEBSITE_REQUEST_TIMEOUT)
            if url.endswith("/next"):
                redirect.close.assert_called_once_with()
                return success
            return redirect

        session.get.side_effect = get
        with patch.object(helpers.requests, "Session", return_value=session), patch.object(
            helpers, "_validate_public_http_url", side_effect=lambda url: url
        ):
            documents = helpers.load_website_documents(["https://example.com"])
        self.assertEqual(documents[0].metadata["source"], "https://example.com/next")
        success.close.assert_called_once_with()
        session.close.assert_called_once_with()

    def test_http_type_size_iteration_and_missing_redirect_failures_close_resources(self):
        http_error = response()
        http_error.raise_for_status.side_effect = requests.HTTPError("Failed request")
        iteration_error = response()

        def broken_body():
            yield b"hello"
            raise requests.ConnectionError("Interrupted body")

        iteration_error.iter_content.return_value = broken_body()
        cases = [
            (http_error, requests.HTTPError),
            (response(headers={"Content-Type": "application/json"}), ValueError),
            (response(chunks=[b"123", b"456"]), ValueError),
            (iteration_error, requests.ConnectionError),
            (response(redirect=True, headers={"Other": "header"}), ValueError),
        ]
        with patch.object(helpers, "MAX_WEBSITE_RESPONSE_BYTES", 5):
            for result, error in cases:
                with self.subTest(error=error, headers=result.headers), self.assertRaises(error):
                    self.fetch([result])

    def test_request_failure_still_closes_session(self):
        with self.assertRaises(requests.ConnectionError):
            self.fetch([requests.ConnectionError("Failed connection")])

    def test_redirect_limit_closes_every_response(self):
        redirects = [response(redirect=True, headers={"Location": "/next"})
                     for _ in range(helpers.MAX_WEBSITE_REDIRECTS + 1)]
        with self.assertRaisesRegex(ValueError, "exceeded .* redirects"):
            self.fetch(redirects)

    def test_blocked_redirect_is_revalidated_after_response_cleanup(self):
        redirect = response(redirect=True, headers={"Location": "https://localhost"})
        session = Mock()
        session.get.return_value = redirect
        with patch.object(helpers.requests, "Session", return_value=session), patch.object(
            helpers, "_validate_public_http_url",
            side_effect=["https://example.com", "https://example.com", ValueError("Blocked redirect")],
        ), self.assertRaisesRegex(ValueError, "Blocked redirect"):
            helpers.load_website_documents(["https://example.com"])
        redirect.close.assert_called_once_with()
        session.close.assert_called_once_with()
        self.assertEqual(session.get.call_count, 1)


if __name__ == "__main__":
    unittest.main()
