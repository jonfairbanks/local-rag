"""Correct the platform tag in NVIDIA's cuSPARSELt 0.8.1 ARM64 wheel."""

import base64
import csv
import hashlib
from importlib.metadata import distribution
import platform


def repair_metadata(dist):
    if dist.version != "0.8.1":
        return
    wheel_entry = next(p for p in dist.files if p.name == "WHEEL")
    wheel_path = dist.locate_file(wheel_entry)
    content = wheel_path.read_bytes()
    old_tag = b"Tag: py3-none-manylinux2014_sbsa\n"
    if old_tag not in content:
        return

    library = dist.locate_file("nvidia/cusparselt/lib/libcusparseLt.so.0")
    with library.open("rb") as stream:
        header = stream.read(20)
    if header[:6] != b"\x7fELF\x02\x01" or header[18:20] != b"\xb7\x00":
        raise RuntimeError("Expected an ARM64 cuSPARSELt library")

    record_path = wheel_path.with_name("RECORD")
    with record_path.open(newline="") as stream:
        records = list(csv.reader(stream))
    row = next(row for row in records if row[0] == str(wheel_entry))
    content = content.replace(old_tag, b"Tag: py3-none-manylinux2014_aarch64\n")
    digest = base64.urlsafe_b64encode(hashlib.sha256(content).digest()).rstrip(b"=")
    row[1:] = ["sha256=" + digest.decode(), str(len(content))]
    wheel_path.write_bytes(content)
    with record_path.open("w", newline="") as stream:
        csv.writer(stream).writerows(records)


if __name__ == "__main__":
    if platform.system() == "Linux" and platform.machine() == "aarch64":
        repair_metadata(distribution("nvidia-cusparselt-cu13"))
