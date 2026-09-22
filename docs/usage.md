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
| Ollama Endpoint | Ollama URL allowed by `LOCAL_RAG_OLLAMA_ENDPOINTS`. Blocked URLs remain editable; an empty value restores the default. | `http://localhost:11434` |
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

Built-in Hugging Face models use pinned revisions; custom models use `main`. Choose repositories you trust. Models must provide safetensors weights and work without remote Python code. Download the model and tokenizer before going offline. Each browser session caches its latest embedding model.

Model and chunk changes apply to the next successful import. If an import fails, chat keeps using the previous index. Correct the settings or files, then select **Retry Import**.

## Data Sources

### Local Files

Supported upload extensions are `csv`, `docx`, `epub`, `ipynb`, `json`, `md`, `pdf`, `ppt`, `pptx`, and `txt`.

Upload limits:

- Up to 10 files per upload
- 25 MB per file
- 100 MB total per upload

Uploads use a private temporary directory, cleaned up after each import. Unchanged files reuse the existing index. Archive expansion is limited, and an index can contain up to 10,000 chunks.

### GitHub Repositories

The GitHub source accepts either:

- `owner/repo`
- `https://github.com/owner/repo`

Use the repository URL on `github.com`, without a branch, issue, or pull request path. Repositories are cloned with `--depth 1` into a private temporary directory, then removed after ingestion. Imports allow up to 1,000 files, 25 MB per file and 100 MB total. Symbolic links are rejected; hidden paths such as `.git` are skipped.

Compose gives `/tmp` 512 MB, shared by imports and clone metadata. Increase its tmpfs size if needed, within the container's memory limit.

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
