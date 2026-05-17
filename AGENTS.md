# AGENTS.md

Guidance for AI coding agents working in this repository.

## Project Overview

Local RAG is a Streamlit application for offline retrieval augmented generation with Ollama, LlamaIndex, local files, GitHub repositories, and websites.

Primary entry points:

- `main.py`: Streamlit app bootstrap.
- `components/`: Streamlit UI pieces.
- `utils/`: ingestion, Ollama, browser settings, and RAG pipeline helpers.
- `tests/`: local unit tests.

## Setup

Use the project environment rather than the system Python:

```bash
pip install pipenv
pipenv install
pipenv run streamlit run main.py
```

The app expects Python 3.14+ and an Ollama instance. The default Ollama endpoint is `http://localhost:11434`.

## Verification

Run focused tests while iterating, then the full suite before handing off:

```bash
pipenv run python -m unittest discover -s tests
pipenv run python -m py_compile main.py components/page_state.py components/tabs/settings.py utils/browser_settings.py utils/ollama.py
```

For a Streamlit smoke test:

```bash
pipenv run streamlit run main.py --server.headless=true --server.port=8520 --server.address=127.0.0.1
curl -s http://127.0.0.1:8520/_stcore/health
```

Stop any smoke-test Streamlit process after checking it.

## Development Notes

- Prefer `rg` for search.
- Use `apply_patch` for manual edits.
- Do not revert unrelated local changes. This repo may have ongoing work in many files.
- Keep UI changes small and consistent with existing Streamlit patterns.
- Add or update tests for behavior changes, especially validation, persistence, ingestion safety, and model-selection state.

## Browser Settings

Settings persistence uses browser `localStorage` through the local Streamlit component in `utils/browser_storage_component/`.

Important details:

- Persisted settings are defined in `utils/browser_settings.py`.
- Do not reintroduce query-parameter persistence for settings.
- Model lists are endpoint-aware; if `ollama_endpoint` changes or is restored from localStorage, chat and embedding model lists should reload for that endpoint.
- Empty `ollama_endpoint` values should not be restored or saved; the default should remain `http://localhost:11434`.

## GitHub Repository Input

GitHub repo ingestion accepts both:

- `owner/repo`
- `https://github.com/owner/repo`

Normalize inputs with `utils.helpers.normalize_github_repo()` before validation or cloning. Reject non-GitHub URLs and URLs with extra path segments.

## Security-Sensitive Areas

Be careful when editing:

- File uploads and path handling in `utils.helpers`.
- Website ingestion and URL validation.
- GitHub cloning and subprocess calls.
- Ollama endpoint handling.
- Any code that writes to disk or fetches remote content.

Tests in `tests/test_security_controls.py` cover several of these guardrails.
