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

Blocked endpoints stay visible in Settings. Add the address to `LOCAL_RAG_OLLAMA_ENDPOINTS` on the server or choose an allowed endpoint.

## Diagnostics

Open Settings, enable Advanced Settings, and expand Diagnostics to check whether documents, the LLM, and the index are ready. No document content or chat history is shown.

Remove private data before sharing screenshots or logs in an issue.

## Allowed Model Endpoints

Local RAG allows `http://localhost:11434` and `http://127.0.0.1:11434` by default. To use another Ollama server, set a comma-separated list of HTTP or HTTPS addresses before starting the app:

```bash
LOCAL_RAG_OLLAMA_ENDPOINTS=http://192.168.4.2:11434 pipenv run streamlit run main.py
```

This replaces the defaults, so include localhost if needed. Use a scheme, host, and optional port, without credentials or a path, query, or fragment. Redirects and environment proxies are disabled. Use hosts and DNS you trust, since the selected server receives your documents and prompts.

For Docker host routing and remote UI access, see [Setup](setup.md#docker).

## Ingestion Limits

Uploads and clones use private temporary directories that are cleaned up after ingestion. The old shared `data/` directory is no longer used; review and remove its contents yourself when upgrading.

Chunk Size accepts 256 to 8192 tokens. Chunk Overlap accepts 0 to 2048, up to half of Chunk Size. Indexing stops at 10,000 chunks. ZIP-based documents are checked for excessive entries, expanded size, and compression ratios before parsing.

Hugging Face models must provide safetensors weights and work without remote Python code. Use **Other** for a custom model ID from a repository you trust. Built-in models use pinned revisions; custom models use `main`.

If an import fails, correct the settings and select **Retry Import**, or change the files. Chat keeps using the previous source and model until an import succeeds.

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
