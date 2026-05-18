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
| Ollama Endpoint | Ollama API base URL. Empty values are ignored and fall back to `http://localhost:11434`. | `http://localhost:11434` |
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
| Other HuggingFace Model | Custom Hugging Face model id used when Local Hugging Face model is `Other`. | |
| Chunk Size | Maximum chunk size for indexed source text. Advanced setting. | `1024` |
| Chunk Overlap | Text overlap between consecutive chunks. Must be less than Chunk Size. Advanced setting. | `200` |

## Data Sources

### Local Files

Supported upload extensions are `csv`, `docx`, `epub`, `ipynb`, `json`, `md`, `pdf`, `ppt`, `pptx`, and `txt`.

Upload limits:

- Up to 10 files per upload
- 25 MB per file
- 100 MB total per upload

Uploaded files are written to a temporary `data/` directory for ingestion, indexed, then deleted after indexing completes. Re-uploading the same files reuses the existing index; changed file contents trigger reprocessing.

### GitHub Repositories

The GitHub source accepts either:

- `owner/repo`
- `https://github.com/owner/repo`

Only `github.com` repository URLs are supported. URLs must point directly to a repository; issue, pull request, branch, or other extra path URLs are rejected. Repositories are cloned with `--depth 1` into the temporary `data/` directory, indexed, then removed after indexing completes.

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
