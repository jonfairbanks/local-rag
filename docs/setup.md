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

The default Ollama endpoint is `http://localhost:11434`. You can change it in the Settings tab. The app refreshes chat and embedding model lists for the configured endpoint.

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

The default Docker Compose file runs the published `jonfairbanks/local-rag` image on port `8501`, with a read-only container filesystem, tmpfs cache directories, resource limits, and an NVIDIA GPU reservation. For AMD/ROCm hosts, see `docker-compose.yml-rocm`.

If Ollama is running on the host rather than inside the container, point the app's Ollama endpoint at a host-reachable address. On Linux Docker, you may need this Compose setting:

```
extra_hosts:
- 'host.docker.internal:host-gateway'
```

Then use `http://host.docker.internal:11434` as the Ollama endpoint.
