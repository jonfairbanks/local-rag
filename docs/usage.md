# Using Local RAG

## Quick Start

1. Open Settings and confirm the Ollama endpoint.
2. Select a valid chat model.
3. Select an embedding backend and model.
4. Import data from local files, a GitHub repository, or websites.
5. Once ingestion completes, ask questions in the chat box.

Data import controls stay disabled until the required model settings are valid.

## Settings

Settings are stored in browser `localStorage` and restored on the next visit from the same browser. Chat history is not persisted this way; use the Export Data section to download it.

### Ollama

| Setting | Description | Default |
| --- | --- | --- |
| Ollama Endpoint | API origin allowed by the server's `LOCAL_RAG_OLLAMA_ENDPOINTS`. Saved origins remain visible if blocked; Settings explains how to allow them. Empty values fall back to localhost. | `http://localhost:11434` |
| Chat Model | Installed Ollama model with `completion` capability. | Prefers `gemma4:latest`, then `llama3:8b`, then `llama2:7b`, then the first discovered chat model. |
| Refresh Models | Reloads chat and embedding model lists for the current endpoint. | |
| Top K | Number of most similar chunks to retrieve for each query. Advanced setting. | `3` |
| Chat Mode | LlamaIndex response mode used by the query engine. Advanced setting. Currently shown as disabled. | `compact` |

### Embeddings

| Setting | Description | Default |
| --- | --- | --- |
| Backend | Choose between Ollama embeddings and local Hugging Face embeddings. | `Ollama` |
| Ollama Embedding Model | Installed Ollama model with `embedding` capability. | `embeddinggemma`, when available |
| Local Hugging Face Model | Local embedding model used when Backend is `Local Hugging Face`. | `Alibaba-NLP/gte-modernbert-base` |
| Hugging Face Model ID | Custom Hub model ID used when Model is `Other`, such as `sentence-transformers/all-MiniLM-L6-v2`. | |
| Chunk Size | 256 to 8192 tokens per chunk. Advanced setting. | `1024` |
| Chunk Overlap | 0 to 2048 tokens, at most half of Chunk Size. Advanced setting. | `200` |

The two built-in Hugging Face models use pinned revisions. Custom models use their `main` revision. All models require safetensors weights and load with remote Python code disabled; models requiring custom code are unsupported. Choose custom repositories you trust. Downloads need network access on first use; offline use requires the selected revision and tokenizer files to be cached. Each browser session reuses its most recently loaded embedding model, without sharing model objects across sessions.

Model and chunk changes apply to the next successful import. A failed replacement keeps the previous index available. Failed file uploads wait for **Retry Import** or changed file contents instead of retrying on every page interaction.

## Data Sources

### Local Files

Supported upload extensions are `csv`, `docx`, `epub`, `ipynb`, `json`, `md`, `pdf`, `ppt`, `pptx`, and `txt`.

Upload limits:

- Up to 10 files per upload
- 25 MB per file
- 100 MB total per upload

Uploaded files are staged in a private temporary directory and removed after ingestion, including failures. Re-uploading the same files reuses the existing index; changed file contents trigger reprocessing. ZIP-based documents also have archive expansion limits, and indexing is limited to 10,000 chunks.

### GitHub Repositories

The GitHub source accepts either:

- `owner/repo`
- `https://github.com/owner/repo`

Only `github.com` repository URLs are supported. URLs must point directly to a repository; issue, pull request, branch, or other extra path URLs are rejected. Repositories are cloned with `--depth 1` into a private temporary directory and removed after ingestion, including failures. Sources are limited to 1,000 files, 25 MB per file and 100 MB total; symbolic links are rejected. Hidden paths, including `.git`, are excluded from document loading.

Compose provides a shared 512 MB `/tmp` for staging. Clone metadata and simultaneous imports also use that space. If legitimate imports exhaust it, increase the service's `/tmp` tmpfs size within the container memory budget.

### Websites

Website ingestion accepts up to 5 public HTTPS URLs at a time. If you enter a hostname without a scheme, Local RAG adds `https://`.

Guardrails:

- Only HTTPS URLs are allowed.
- Embedded URL credentials are rejected.
- Local, private, link-local, metadata, multicast, reserved, and unspecified network addresses are blocked.
- Redirects are followed up to 3 times.
- Responses must be HTML or plain text.
- Website response bodies are limited to 5 MB per URL.

## Export Data

Use `Settings > Export Data > Chat History` to download the current chat transcript as JSON.
