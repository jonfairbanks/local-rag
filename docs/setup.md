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

The default Ollama endpoint is `http://localhost:11434`. The server allows that origin and `http://127.0.0.1:11434` by default. To use another server, set `LOCAL_RAG_OLLAMA_ENDPOINTS` before starting the app, then select its URL in Settings. This comma-separated list replaces the defaults. The app refreshes chat and embedding model lists for the configured endpoint.

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

The default Docker Compose file runs the published `jonfairbanks/local-rag` image at `http://127.0.0.1:8501`, with a read-only container filesystem, tmpfs cache directories, resource limits, and an NVIDIA GPU reservation. For AMD/ROCm hosts, use `docker compose -f docker-compose.yml-rocm up -d`. Both configurations bind the UI to loopback and accept `LOCAL_RAG_OLLAMA_ENDPOINTS` from the environment or Compose `.env` file.

Inside the app container, localhost refers to that container, not the host. If Ollama runs on the host, allow its host-reachable origin in a Compose `.env` file:

```dotenv
LOCAL_RAG_OLLAMA_ENDPOINTS=http://host.docker.internal:11434
```

On Linux Docker, also add this under the `local-rag` service:

```yaml
extra_hosts:
  - 'host.docker.internal:host-gateway'
```

Recreate the app container with your chosen Compose command, then use `http://host.docker.internal:11434` in Settings. Ollama must listen on an interface reachable from the container; protect that interface with your host firewall. Adding an origin to the allowlist does not configure routing or Ollama's listener.

For remote browser access, place an authenticated reverse proxy in front of the UI and configure network access explicitly. The default Compose port mapping does not accept direct LAN connections.
