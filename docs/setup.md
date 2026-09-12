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

If Ollama is running on the host rather than inside the container, both sides must be configured: Ollama must listen on an address the container can reach, and Docker must provide a hostname for the host gateway. Ollama listens on loopback by default, so adding `host.docker.internal` alone is not sufficient.

Start Ollama with a container-reachable bind address:

```bash
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

Then add this to the `local-rag` service in your Compose override:

```yaml
extra_hosts:
  - 'host.docker.internal:host-gateway'
```

Then use `http://host.docker.internal:11434` as the Ollama endpoint.

> **Security:** binding Ollama to `0.0.0.0` can expose it to your local network. Restrict port `11434` with your host firewall and do not expose it to an untrusted network.

On Linux, an alternative is to add `network_mode: host` to the service and use `http://localhost:11434`. Remove the service's `ports` mapping when using host networking. This avoids rebinding Ollama, but gives the container access to the host network namespace and is therefore a broader trust choice.
