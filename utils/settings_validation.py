"""Shared validation for browser settings and server-side model clients."""

import os
from urllib.parse import urlsplit, urlunsplit

MIN_CHUNK_SIZE = 256
MAX_CHUNK_SIZE = 8192
MAX_CHUNK_OVERLAP = 2048
HF_MODELS = {
    "Default (gte-modernbert-base)": "Alibaba-NLP/gte-modernbert-base",
    "Higher Quality (Qwen3-Embedding-0.6B)": "Qwen/Qwen3-Embedding-0.6B",
}
HF_MODEL_REVISIONS = {
    "Alibaba-NLP/gte-modernbert-base": "e7f32e3c00f91d699e8c43b53106206bcc72bb22",
    "Qwen/Qwen3-Embedding-0.6B": "97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3",
}
CHAT_MODES = {
    "compact",
    "refine",
    "tree_summarize",
    "simple_summarize",
    "accumulate",
    "compact_accumulate",
}


def bounded_integer(value, minimum, maximum, label):
    # Check representation size before converting browser-controlled integers.
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ValueError(f"{label} must be an integer.")
    if isinstance(value, str) and (
        len(value) > 5 or not value.isascii() or not value.isdecimal()
    ):
        raise ValueError(f"{label} must be an integer.")
    number = int(value)
    if not minimum <= number <= maximum:
        raise ValueError(f"{label} must be between {minimum} and {maximum}.")
    return number


def validate_chunk_settings(chunk_size, chunk_overlap):
    size = bounded_integer(chunk_size, MIN_CHUNK_SIZE, MAX_CHUNK_SIZE, "Chunk Size")
    overlap = bounded_integer(chunk_overlap, 0, MAX_CHUNK_OVERLAP, "Chunk Overlap")
    if overlap > size // 2:
        raise ValueError("Chunk Overlap must be at most half of Chunk Size.")
    return size, overlap


def canonical_ollama_endpoint(value):
    if not isinstance(value, str) or len(value) > 2048:
        raise ValueError("Ollama endpoint must be an HTTP or HTTPS URL.")
    value = value.strip()
    if not value.isascii() or any(ord(char) < 33 for char in value) or "\\" in value:
        raise ValueError("Invalid Ollama endpoint.")
    parsed = urlsplit(value)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(
            "Ollama endpoint must contain only a scheme, host, and optional port."
        )
    port = parsed.port
    host = parsed.hostname.lower()
    if ":" in host:
        host = f"[{host}]"
    if port is not None and port != (443 if parsed.scheme == "https" else 80):
        host = f"{host}:{port}"
    return urlunsplit((parsed.scheme, host, "", "", ""))


def allowed_ollama_endpoints():
    configured = os.environ.get(
        "LOCAL_RAG_OLLAMA_ENDPOINTS",
        "http://localhost:11434,http://127.0.0.1:11434",
    )
    return {
        canonical_ollama_endpoint(item)
        for item in configured.split(",")
        if item.strip()
    }


def validate_ollama_endpoint(value):
    endpoint = canonical_ollama_endpoint(value)
    if endpoint not in allowed_ollama_endpoints():
        raise ValueError(
            "Ollama endpoint is not allowed. Set LOCAL_RAG_OLLAMA_ENDPOINTS on the server."
        )
    return endpoint
