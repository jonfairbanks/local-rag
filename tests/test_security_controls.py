import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock

from utils import helpers
from utils.rag_pipeline import validate_ingested_documents


class FakeUpload:
    def __init__(self, name, payload):
        self.name = name
        self.size = len(payload)
        self._payload = payload

    def getbuffer(self):
        return self._payload


class UploadSafetyTests(unittest.TestCase):
    def test_safe_upload_destination_stays_inside_save_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            destination = helpers.upload_destination(tmpdir, "notes.txt")

        self.assertEqual(destination.name, "notes.txt")

    def test_upload_destination_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(ValueError):
                helpers.upload_destination(tmpdir, "../notes.txt")

    def test_upload_destination_rejects_backslash_separator(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(ValueError):
                helpers.upload_destination(tmpdir, "nested\\notes.txt")

    def test_validate_uploaded_files_enforces_count_limit(self):
        uploads = [
            FakeUpload(f"file-{index}.txt", b"x")
            for index in range(helpers.MAX_UPLOAD_FILES + 1)
        ]

        with self.assertRaises(ValueError):
            helpers.validate_uploaded_files(uploads)

    def test_validate_uploaded_files_enforces_size_limit(self):
        upload = FakeUpload("large.txt", b"x" * (helpers.MAX_UPLOAD_FILE_BYTES + 1))

        with self.assertRaises(ValueError):
            helpers.validate_uploaded_files([upload])


class WebsiteValidationTests(unittest.TestCase):
    def test_validate_website_urls_requires_https(self):
        with self.assertRaises(ValueError):
            helpers.validate_website_urls(["http://example.com"])

    def test_validate_website_urls_blocks_loopback(self):
        with self.assertRaises(ValueError):
            helpers.validate_website_urls(["https://127.0.0.1"])

    def test_validate_website_urls_blocks_metadata_hostname(self):
        with self.assertRaises(ValueError):
            helpers.validate_website_urls(["https://metadata.google.internal"])

    def test_validate_website_urls_enforces_count_limit(self):
        urls = [
            f"https://example-{index}.com"
            for index in range(helpers.MAX_WEBSITE_URLS + 1)
        ]

        with self.assertRaises(ValueError):
            helpers.validate_website_urls(urls)


class GitHubRepoValidationTests(unittest.TestCase):
    def test_normalize_github_repo_accepts_owner_repo(self):
        self.assertEqual(
            helpers.normalize_github_repo("TNTwise/REAL-Video-Enhancer"),
            "TNTwise/REAL-Video-Enhancer",
        )

    def test_normalize_github_repo_accepts_full_github_url(self):
        self.assertEqual(
            helpers.normalize_github_repo(
                "https://github.com/TNTwise/REAL-Video-Enhancer"
            ),
            "TNTwise/REAL-Video-Enhancer",
        )

    def test_normalize_github_repo_strips_git_suffix(self):
        self.assertEqual(
            helpers.normalize_github_repo(
                "https://github.com/TNTwise/REAL-Video-Enhancer.git"
            ),
            "TNTwise/REAL-Video-Enhancer",
        )

    def test_normalize_github_repo_rejects_non_github_url(self):
        with self.assertRaises(ValueError):
            helpers.normalize_github_repo("https://example.com/TNTwise/repo")

    def test_normalize_github_repo_rejects_extra_path_segments(self):
        with self.assertRaises(ValueError):
            helpers.normalize_github_repo(
                "https://github.com/TNTwise/REAL-Video-Enhancer/issues"
            )

    def test_clone_github_repo_returns_scoped_repo_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(helpers.os, "getcwd", return_value=tmpdir):
                with patch.object(helpers.subprocess, "run") as mock_run:
                    mock_run.return_value = Mock(returncode=0)

                    destination = helpers.clone_github_repo("owner/repo")

        self.assertEqual(destination, str(Path(tmpdir) / "data" / "owner" / "repo"))


class IngestionLimitTests(unittest.TestCase):
    def test_validate_ingested_documents_enforces_document_count(self):
        documents = ["x"] * (1001)

        with self.assertRaises(ValueError):
            validate_ingested_documents(documents)

    def test_validate_ingested_documents_enforces_text_size(self):
        documents = ["x" * (10 * 1024 * 1024 + 1)]

        with self.assertRaises(ValueError):
            validate_ingested_documents(documents)


if __name__ == "__main__":
    unittest.main()
