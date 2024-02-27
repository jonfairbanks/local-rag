# Using Local RAG

## Quick Start

1. Set your Ollama endpoint and model under Settings
2. Upload your documents for processing
3. Once complete, ask questions based on your documents!

## Settings

All options within the RAG pipeline are exposed to users after toggling `Settings > Show Advanced Options`.

### Ollama

| Setting           | Description                                                            | Default                       |
|-------------------|------------------------------------------------------------------------|-------------------------------|
| Ollama Endpoint   | The location of your locally hosted Ollama API                         | http://localhost:11434        |
| Model             | Large language model to use what generating chat completions           |                               |
| System Prompt     | Initial system prompt used when initializing the LLM                   | (Please see source code)      |
| Top K             | Number of most similar documents to retrieve in response to a query    | 3                             |
| Chat Mode         | [Llama Index](#) chat mode to utilize during retrievals                | Best                          |

### Embeddings

| Setting           | Description                                                             | Default               |
|-------------------|-------------------------------------------------------------------------|-----------------------|
| Embedding Model   | Embedding model to be used for vectorize your files                     | bge-large-en-v1.5     |
| Chunk Size        | Improves embedding precision by focusing on smaller text portions       | 1024                  |