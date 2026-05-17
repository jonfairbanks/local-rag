import unittest

from components.tabs.github_repo import (
    GITHUB_DOCUMENTS_LOADED_STAGE,
    should_show_github_ingestion_status,
)


class GitHubIngestionStatusTests(unittest.TestCase):
    def test_github_loaded_stage_refers_to_repository_files(self):
        self.assertEqual(GITHUB_DOCUMENTS_LOADED_STAGE, "Repository Files Loaded")

    def test_shows_status_for_processed_repo_with_query_engine(self):
        self.assertTrue(
            should_show_github_ingestion_status(
                current_repo="jonfairbanks/jonfairbanks",
                processed_repo="jonfairbanks/jonfairbanks",
                ingestion_stages=["Repository Validated", "Index Ready"],
                query_engine=object(),
            )
        )

    def test_shows_status_when_current_repo_is_full_github_url(self):
        self.assertTrue(
            should_show_github_ingestion_status(
                current_repo="https://github.com/jonfairbanks/jonfairbanks",
                processed_repo="jonfairbanks/jonfairbanks",
                ingestion_stages=["Repository Validated", "Index Ready"],
                query_engine=object(),
            )
        )

    def test_hides_status_when_input_no_longer_matches_processed_repo(self):
        self.assertFalse(
            should_show_github_ingestion_status(
                current_repo="other/repo",
                processed_repo="jonfairbanks/jonfairbanks",
                ingestion_stages=["Repository Validated", "Index Ready"],
                query_engine=object(),
            )
        )

    def test_hides_status_without_query_engine(self):
        self.assertFalse(
            should_show_github_ingestion_status(
                current_repo="jonfairbanks/jonfairbanks",
                processed_repo="jonfairbanks/jonfairbanks",
                ingestion_stages=["Repository Validated", "Index Ready"],
                query_engine=None,
            )
        )


if __name__ == "__main__":
    unittest.main()
