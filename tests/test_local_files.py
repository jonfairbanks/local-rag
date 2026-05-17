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
        self.assertFalse(should_process_uploads(("same",), ("same",), object()))

    def test_reprocesses_when_index_is_missing(self):
        self.assertTrue(should_process_uploads(("same",), ("same",), None))

    def test_reprocesses_when_uploads_change(self):
        self.assertTrue(should_process_uploads(("new",), ("old",), object()))


class UploadLimitHelpTextTests(unittest.TestCase):
    def test_describes_application_upload_limits(self):
        self.assertEqual(
            upload_limit_help_text(),
            "Up to 10 files. 25MB per file, 100MB total.",
        )


if __name__ == '__main__':
    unittest.main()
