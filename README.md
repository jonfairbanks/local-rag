# 📚 Local RAG

![local-rag-demo](demo.gif)

![GitHub commit activity](https://img.shields.io/github/commit-activity/t/jonfairbanks/local-rag)
![GitHub last commit](https://img.shields.io/github/last-commit/jonfairbanks/local-rag)
![GitHub License](https://img.shields.io/github/license/jonfairbanks/local-rag)

Offline, Open-Source RAG

Ingest files for retrieval augmented generation (RAG) with open-source Large Language Models (LLMs), all without 3rd parties or sensitive data leaving your network.

- Offline Embeddings & LLMs Support (No OpenAI!)
- Streaming Responses
- Conversation Memory
- Chat Export

### Pre-Requisites

- A pre-existing Ollama instance
- Python 3.10+

### Setup

Local:
- `pip install pipenv && pipenv install`
- `pipenv shell && streamlit run main.py`

Docker:
- `docker compose up -d`

### Usage

- Set your Ollama endpoint and model under Settings
- Upload your documents for processing
- Once complete, ask questions based on your documents!

### To Do
- [x] Refactor into modules
- [ ] Refactor file processing logic
- [x] Migrate Chat Stream to Llama-Index
- [x] Implement Llama-Index Chat Engine with Memory
- [x] Swap to Llama-Index Chat Engine
- [x] Function to Handle File Embeddings
- [ ] Allow Users to Set LLM Settings
    - [x] System Prompt
    - [ ] Chat Mode
    - [x] top_k
    - [x] chunk_size
    - [ ] chunk_overlap
- [x] Allow Switching of Embedding Model & Settings
- [x] Delete Files after Index Created/Failed
- [x] Support Additional Import Options
    - [x] GitHub Repos
    - [ ] Websites
- [ ] Remove File Type Limitations for Uploads
- [x] Show Loaders in UI (File Uploads, Conversions, ...)
- [x] Export Data (Uploaded Files, Chat History, ...)
- [x] View and Manage Imported Files
- [x] About Tab in Sidebar
- [x] Docker Support
- [x] Implement Log Library
- [ ] Improve Logging
- [ ] Re-write Docstrings
- [ ] Additional Error Handling
    - [x] Starting a chat without an Ollama model set
    - [ ] Incorrect GitHub repos

### Known Issues & Bugs
- [ ] Refreshing the page loses all state (expected Streamlit behavior; need to implement local-storage)
- [x] Files can be uploaded before Ollama config is set, leading to embedding errors
- [ ] Assuming Ollama is hosted on localhost, Models are automatically loaded and selected, but the dropdown does not render the selected option
- [ ] Upon sending a Chat message, the File Processing expander appears to re-run itself (seems something is not using state correctly)

### Resources
- [Ollama](https://ollama.com/)
- [Llama-Index](https://docs.llamaindex.ai/en/stable/index.html)
- [Streamlit](https://docs.streamlit.io/library/api-reference)
- [Ollama w/ Llama-Index](https://docs.llamaindex.ai/en/stable/examples/llm/ollama.html)
- [RAG w/ Llama-Index](https://blog.streamlit.io/build-a-chatbot-with-custom-data-sources-powered-by-llamaindex/)
- [Llama-Index Chat Engine](https://docs.llamaindex.ai/en/stable/examples/chat_engine/chat_engine_context.html)
- [PoC Notebook](https://github.com/fairbanksio/notebooks/blob/main/llm/local/github-rag-prep.ipynb)