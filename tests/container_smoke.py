"""Check the image's native dependencies and Streamlit startup."""

import importlib
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

import torch
from torchvision.ops import nms


def main():
    assert os.getuid() != 0, "The image must run as a non-root user"
    subprocess.run([sys.executable, "-m", "pip", "check"], check=True)
    for module in (
        "triton",
        "sentence_transformers",
        "llama_index.embeddings.huggingface",
        "docx2txt",
        "pptx",
        "pyarrow",
        "sklearn",
    ):
        importlib.import_module(module)
    assert torch.tensor([2, 3]).sum().item() == 5
    boxes = torch.tensor([[0.0, 0.0, 1.0, 1.0], [0.0, 0.0, 1.0, 1.0]])
    assert nms(boxes, torch.tensor([0.9, 0.8]), 0.5).tolist() == [0]

    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "main.py",
            "--server.headless=true",
            "--server.address=127.0.0.1",
            "--server.port=8501",
            "--server.fileWatcherType=none",
        ]
    )
    try:
        for _ in range(30):
            if process.poll() is not None:
                raise RuntimeError("Streamlit exited before becoming healthy")
            try:
                with urllib.request.urlopen(
                    "http://127.0.0.1:8501/_stcore/health", timeout=1
                ) as response:
                    if response.read() == b"ok":
                        print("Image smoke checks passed", flush=True)
                        return
            except (urllib.error.URLError, TimeoutError):
                pass
            time.sleep(1)
        raise RuntimeError("Streamlit did not become healthy")
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


if __name__ == "__main__":
    main()
