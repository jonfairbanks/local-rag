# 📚 Local RAG

![local-rag-logo](logo.png)

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
- Python 3.9+

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
- [x] Refactor
- [x] Migrate chat stream to llama-index
- [x] Implement llama-index Chat Engine with memory
- [x] Swap to llama-index Chat Engine
- [x] Function to handle file embeddings
- [ ] Allow Switching of Embedding Model
- [x] Delete Files after Index created/failed
- [ ] Ability to Remove Files from Index
- [ ] Function to handle GitHub repo ingestion
- [ ] Support for JSON files
- [x] Show Loaders in UI (file uploads, conversions, ...)
- [X] Export Data (uploaded files, chat history, ...)
- [x] View and Manage Imported Files
- [x] About Tab in Sidebar
- [x] Docker Support
- [ ] Implement Log Library

### Known Issues & Bugs
- [ ] Refreshing the page loses all state (expected Streamlit behavior; need to implement local-storage)
- [x] Files can be uploaded before Ollama config is set, leading to embedding errors
- [ ] Assuming Ollama is hosted on localhost, Models are automatically loaded and selected, but the dropdown does not render the selected option

### Resources
- [Ollama](https://ollama.com/)
- [Llama-Index](https://docs.llamaindex.ai/en/stable/index.html)
- [Streamlit](https://docs.streamlit.io/library/api-reference)
- [Ollama w/ Llama-Index](https://docs.llamaindex.ai/en/stable/examples/llm/ollama.html)
- [RAG w/ Llama-Index](https://blog.streamlit.io/build-a-chatbot-with-custom-data-sources-powered-by-llamaindex/)
- [Llama-Index Chat Engine](https://docs.llamaindex.ai/en/stable/examples/chat_engine/chat_engine_context.html)