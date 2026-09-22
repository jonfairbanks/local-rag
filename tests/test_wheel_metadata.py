import base64
import csv
import hashlib
from importlib.metadata import PathDistribution
from pathlib import Path
import tempfile
import unittest

from scripts.fix_cusparselt_metadata import repair_metadata


class WheelMetadataTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.info = self.root / "nvidia_cusparselt_cu13-0.8.1.dist-info"
        self.info.mkdir()
        (self.info / "METADATA").write_text(
            "Name: nvidia-cusparselt-cu13\nVersion: 0.8.1\n"
        )
        self.wheel = self.info / "WHEEL"
        self.wheel.write_text("Wheel-Version: 1.0\nTag: py3-none-manylinux2014_sbsa\n")
        self.record = self.info / "RECORD"
        self.record.write_text(
            f"{self.info.name}/WHEEL,sha256=old,0\n{self.info.name}/RECORD,,\n"
        )
        self.library = self.root / "nvidia/cusparselt/lib/libcusparseLt.so.0"
        self.library.parent.mkdir(parents=True)
        self.library.write_bytes(b"\x7fELF\x02\x01" + bytes(12) + b"\xb7\x00")
        self.dist = PathDistribution(self.info)

    def test_corrects_tag_and_record_without_changing_library(self):
        library = self.library.read_bytes()
        repair_metadata(self.dist)
        content = self.wheel.read_bytes()
        self.assertIn(b"manylinux2014_aarch64", content)
        with self.record.open(newline="") as stream:
            rows = list(csv.reader(stream))
        digest = base64.urlsafe_b64encode(hashlib.sha256(content).digest()).rstrip(b"=")
        self.assertEqual(rows[0][1:], ["sha256=" + digest.decode(), str(len(content))])
        self.assertEqual(rows[1][1:], ["", ""])
        self.assertEqual(self.library.read_bytes(), library)
        before = self.record.read_bytes()
        repair_metadata(self.dist)
        self.assertEqual(self.record.read_bytes(), before)

    def test_rejects_wrong_library_architecture(self):
        self.library.write_bytes(b"\x7fELF\x02\x01" + bytes(12) + b"\x3e\x00")
        before = self.wheel.read_bytes()
        with self.assertRaisesRegex(RuntimeError, "ARM64"):
            repair_metadata(self.dist)
        self.assertEqual(self.wheel.read_bytes(), before)

    def test_other_versions_and_tags_are_unchanged(self):
        for version, tag in (("0.9.1", "sbsa"), ("0.8.1", "x86_64")):
            with self.subTest(version=version, tag=tag):
                (self.info / "METADATA").write_text(
                    f"Name: nvidia-cusparselt-cu13\nVersion: {version}\n"
                )
                self.wheel.write_text(f"Tag: py3-none-manylinux2014_{tag}\n")
                before = self.wheel.read_bytes()
                repair_metadata(self.dist)
                self.assertEqual(self.wheel.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
