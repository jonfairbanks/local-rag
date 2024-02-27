# RAG (Retriever-Augmented Generator) Pipeline in Local RAG

The RAG pipeline in Local RAG utilizes the `SimpleDirectoryReader()` function from the `llama-index` library, which allows us to pass a folder containing various files. The reader then iterates through each file and selects an appropriate handler and vectorizer based on the file type (e.g. PDF, MD, IPYNB, ...).

## File Processing and Embedding

For each file, the pipeline creates multiple documents from a single file. For instance, when given a multi-page PDF, it splits it into one document per page. The documents are then chunked and embedded using the default settings provided by `llama-index`. However, users have the flexibility to customize these settings via the user interface, allowing them to experiment with different configurations.

## Key Parameters for Customization

Users can manipulate a few key parameters in the pipeline:

1. **`chunk_size`**: This parameter determines the size of each text chunk. Smaller chunk sizes generally result in higher embedding quality, albeit at the cost of increased computation.
2. **`chunk_overlap`**: This parameter sets the amount of overlap between two consecutive chunks. A higher overlap value helps maintain continuity and context across chunks.

## Experimentation and Balancing Parameters

While experimenting with different `chunk_size` values, users should consider their system's capabilities and available resources. It is essential to find a balance between chunk size and other parameters like `chunk_overlap`. Although setting a higher overlap value does not have any strict limitations, it is generally recommended to maintain it as a proportion relative to the chunk size for optimal performance and continuity in the generated text.