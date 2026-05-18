import unittest

from components.tabs.local_files import (
    upload_limit_help_text,
    should_process_uploads,
    uploaded_files_signature,
)


class FakeUpload:
    def __init__(self, name, payload, mime_type='application/octet-stream'):
        self.name = name
        self.size = len(payload)
        self.type = mime_type
        self._payload = payload

    def getvalue(self):
        return self._payload


class UploadedFilesSignatureTests(unittest.TestCase):
    def test_same_uploads_have_same_signature_across_reruns(self):
        first = [FakeUpload('resume.pdf', b'abc')]
        second = [FakeUpload('resume.pdf', b'abc')]

        self.assertEqual(uploaded_files_signature(first), uploaded_files_signature(second))

    def test_changed_contents_change_signature_even_when_name_and_size_match(self):
        first = [FakeUpload('resume.pdf', b'abc')]
        second = [FakeUpload('resume.pdf', b'abd')]

        self.assertNotEqual(uploaded_files_signature(first), uploaded_files_signature(second))


class ShouldProcessUploadsTests(unittest.TestCase):
    def test_reuses_existing_index_for_same_uploads(self):
        self.assertFalse(
            should_process_uploads(
                current_signature=("same",),
                processed_signature=("same",),
                processing_signature=None,
                query_engine=object(),
            )
        )

    def test_reprocesses_when_index_is_missing(self):
        self.assertTrue(
            should_process_uploads(
                current_signature=("same",),
                processed_signature=("same",),
                processing_signature=None,
                query_engine=None,
            )
        )

    def test_reprocesses_when_uploads_change(self):
        self.assertTrue(
            should_process_uploads(
                current_signature=("new",),
                processed_signature=("old",),
                processing_signature=None,
                query_engine=object(),
            )
        )

    def test_skips_duplicate_run_while_same_upload_is_processing(self):
        self.assertFalse(
            should_process_uploads(
                current_signature=("same",),
                processed_signature=None,
                processing_signature=("same",),
                query_engine=None,
            )
        )

    def test_retries_same_upload_when_no_processing_run_is_active(self):
        self.assertTrue(
            should_process_uploads(
                current_signature=("same",),
                processed_signature=("same",),
                processing_signature=None,
                query_engine=None,
            )
        )


class UploadLimitHelpTextTests(unittest.TestCase):
    def test_describes_application_upload_limits(self):
        self.assertEqual(
            upload_limit_help_text(),
            "Up to 10 files. 25MB per file, 100MB total.",
        )


if __name__ == '__main__':
    unittest.main()
