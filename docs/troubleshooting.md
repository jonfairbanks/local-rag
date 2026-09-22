# Troubleshooting

In the event that an error occurs when using Local RAG, checking out the current application state and logfile can provide insights into what is happening behind the scenes.

Note: To better understand what is happening under the hood and aid in troubleshooting, check out the [Pipeline documentation](pipeline.md) as well.

## Ingestion Is Disabled

Data import controls are disabled until Settings contains a valid Ollama chat model and, when the embedding backend is `Ollama`, a valid Ollama embedding model.

To fix this:

- Confirm Ollama is running.
- Confirm the endpoint in Settings, usually `http://localhost:11434`.
- Pull at least one chat-capable model, such as `gemma4:latest`.
- Pull at least one embedding-capable model, such as `embeddinggemma`, or switch the embedding backend to `Local Hugging Face`.
- Use the Refresh Models buttons after changing the endpoint or pulling new models.

## Settings Restore Problems

Settings are restored from browser `localStorage`. If a stale browser setting points to the wrong Ollama endpoint or a model you no longer have installed, update it in Settings and refresh the model lists. Empty Ollama endpoint values are ignored and the default endpoint is restored.

A saved endpoint outside the server allowlist remains in Settings with an error explaining `LOCAL_RAG_OLLAMA_ENDPOINTS`; it is not contacted. Allow the origin on the server or select an allowed endpoint.

## Diagnostics

Open Settings, enable Advanced Settings, and expand Diagnostics. The report shows whether documents, the LLM, and the index are ready. It excludes document content, conversations, endpoints, and paths.

Review anything you share in an issue. Remove credentials, prompts, document content, private URLs, filenames, and paths. Share only the relevant error text, not full application state or raw logs.

## Allowed Model Endpoints

By default, the server accepts `http://localhost:11434` and `http://127.0.0.1:11434`. To use a LAN or container-host Ollama server, set `LOCAL_RAG_OLLAMA_ENDPOINTS` to a comma-separated list of exact HTTP or HTTPS origins before starting Local RAG. For example:

```bash
LOCAL_RAG_OLLAMA_ENDPOINTS=http://192.168.4.2:11434 pipenv run streamlit run main.py
```

This replaces the default list. Include localhost explicitly if needed. Endpoints cannot contain credentials, paths, queries, or fragments. Redirects and environment proxies are disabled. Allowlisted hostnames and their DNS are trusted operator configuration; use stable IP addresses or egress controls where DNS is outside your control. Documents and prompts are sent to the selected server.

Compose publishes the UI only on `127.0.0.1`. Inside a container, localhost refers to that container. Configure and allow your reachable Ollama server explicitly. Broader UI exposure requires an authenticated reverse proxy and appropriate network controls.

## Ingestion Limits

Uploads and repository clones use private temporary directories, removed even when ingestion stops. The app no longer reads or deletes the legacy shared `data/` directory. Review and remove any old contents manually if upgrading from an earlier release.

Chunk Size accepts 256 through 8192 tokens. Chunk Overlap accepts 0 through 2048 and cannot exceed half of Chunk Size. Indexing stops before embedding more than 10,000 chunks. ZIP-based documents have entry-count, expanded-size, and compression-ratio limits before parsing.

Local Hugging Face embeddings offer two built-in models at pinned revisions and **Other** for a custom Hub model ID. Custom models use `main`; choose repositories you trust. Remote Python code is disabled and safetensors weights are required for every model. A model that requires custom Python code or only provides pickle weights will fail to load. The existing index remains available after a failed replacement.

Failed file imports do not retry on every rerun. Correct the model or chunk settings and select **Retry Import**, or upload changed files. A successful replacement updates the index; until then, chat continues to use the previous source and model settings.

## Import Errors

Common local file import errors:

- Unsupported file extension. Supported extensions are listed in [Usage](usage.md#local-files).
- Too many files, too large a single file, or too large a total upload.
- Filename contains unsupported characters or path separators.

Common GitHub import errors:

- Repository input is not `owner/repo` or `https://github.com/owner/repo`.
- URL is not on `github.com`.
- URL points to an issue, pull request, branch, or another extra path instead of the repository root.
- The repository cannot be validated or cloned.

Common website import errors:

- URL is not HTTPS.
- URL resolves to a blocked local, private, metadata, or otherwise unsafe network address.
- The response is not HTML or plain text.
- The response is larger than the website ingestion limit.
- The URL redirects too many times.

## Log File

By default, Local RAG will create a `local-rag.log` file in the root application folder.

Each step of the RAG process is logged into this file whether the required step was successful or encountered an error. 

Reviewing this log can give you insights into what took place when processing your documents.
