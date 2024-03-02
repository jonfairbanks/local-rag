# To Do

Below is a rough outline of proposesd features and outstanding issues that are being tracked.

Although not final, items are generally sorted from highest to lowest priority.

### Core

- [x] Migrate Chat Stream to Llama-Index
- [x] Implement Llama-Index Chat Engine with Memory
- [x] Swap Chatbox UI to Llama-Index Chat Engine
- [x] Function to Handle File Embeddings
- [x] Allow Switching of Embedding Model & Settings
- [x] Delete Files after Index Created/Failed
- [x] Support Additional Import Options
    - [x] GitHub Repos
    - [x] Websites
- [x] Export Data (Chat History, ...)
- [x] Docker Support
    - [x] Windows Support
- [ ] Extract Metadata and Load into Index
- [ ] Parallelize Document Embeddings
- [ ] Swap to OpenAI compatible endpoints
- [ ] Allow Usage of Ollama hosted embeddings
- [ ] Enable support for additional LLM backends
    - [ ] Local AI
    - [ ] TabbyAPI
- [ ] Remove File Type Limitations for Uploads

### User Experience

- [x] Show Loaders in UI (File Uploads, Conversions, ...)
- [x] View and Manage Imported Files
- [x] About Tab in Sidebar w/ Resources
- [x] Enable Caching
- [ ] Swap Repo & Website input to [Streamlit-Tags](https://gagan3012-streamlit-tags-examplesapp-7aiy65.streamlit.app)
- [ ] Allow Users to Set LLM Settings
    - [x] System Prompt
    - [x] Chat Mode
    - [ ] Temperature
    - [x] top_k
    - [x] chunk_size
    - [ ] chunk_overlap (needs to be proportional to chunk_size?)
- [ ] Additional Error Handling
    - [x] Starting a chat without an Ollama model set
    - [ ] Non-existent GitHub repos
    - [ ] Non-existent Embedding models
    - [ ] Non-existent Websites
    - [ ] System Level Errors (CUDA OOM, Hugging Face downtime, ...)

### Code Quality

- [x] Refactor main.py into submodules
- [x] Refactor file processing logic
- [x] Refactor README
- [x] Implement Log Library
- [x] Improve Logging
- [ ] Re-write Docstrings
- [ ] Tests

### Known Issues & Bugs

- [x] Upon sending a Chat message, the File Processing expander appears to re-run itself (seems something is not using state correctly)
- [ ] Refreshing the page loses all state (expected Streamlit behavior; need to implement local-storage)
- [x] Files can be uploaded before Ollama config is set, leading to embedding errors
- [x] Assuming Ollama is hosted on localhost, Models are automatically loaded and selected, but the dropdown does not render the selected option

### Other

- [ ] Investigate [R2R](https://github.com/SciPhi-AI/R2R) backend support/migration
- [ ] ROCm Support -- Wanted: AMD Testers! 🔍🔴