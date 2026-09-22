# Setup

Before you get started with Local RAG, ensure you have:

- A local [Ollama](https://github.com/ollama/ollama/) instance
- At least one chat-capable model available in Ollama
  - `gemma4:latest`, `llama3:8b`, or `llama2:7b` are supported starter choices when installed locally
- At least one embedding-capable model if you use the default Ollama embedding backend
  - `embeddinggemma` is the default expected Ollama embedding model name
- Python 3.14+

**WARNING:** This application is `untested` on Windows Subsystem for Linux. For best results, please utilize a Linux host if possible.

## Local

```bash
pip install pipenv
pipenv install
pipenv run streamlit run main.py
```

Ollama defaults to `http://localhost:11434`; `http://127.0.0.1:11434` is also allowed. For another server, set `LOCAL_RAG_OLLAMA_ENDPOINTS` before starting the app, then select its URL in Settings. This comma-separated list replaces the defaults. Model lists refresh when the endpoint changes.

Useful Ollama commands:

```bash
ollama pull gemma4:latest
ollama pull embeddinggemma
ollama list
```

## Docker

```bash
docker compose up -d
```

Images support Linux AMD64 and ARM64; Docker selects the matching architecture. Compose serves the app at `http://127.0.0.1:8501`, with a read-only filesystem, tmpfs caches, and resource limits.

The default Compose file reserves an NVIDIA GPU. For CPU-only hosts, including Apple Silicon, use:

```bash
docker compose -f docker-compose.yml-cpu up -d
```

For AMD/ROCm, use `docker compose -f docker-compose.yml-rocm up -d`. All Compose files accept `LOCAL_RAG_OLLAMA_ENDPOINTS` from the environment or a Compose `.env` file. ARM64 image checks cover CPU execution; NVIDIA GPU operation requires compatible hardware and drivers.

If Ollama runs on the host, add its address to the Compose `.env` file:

```dotenv
LOCAL_RAG_OLLAMA_ENDPOINTS=http://host.docker.internal:11434
```

On Linux Docker, also add this under the `local-rag` service:

```yaml
extra_hosts:
  - 'host.docker.internal:host-gateway'
```

Recreate the app container, then select `http://host.docker.internal:11434` in Settings. Ollama must accept connections from the container; use your host firewall to restrict access. The allowlist only controls which addresses Local RAG can use.

For remote browser access, use an authenticated reverse proxy. Compose exposes the UI only on the local host.
