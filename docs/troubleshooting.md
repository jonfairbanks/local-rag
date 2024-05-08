# Troubleshooting

In the event that an error occurs when using Local RAG, checking out the current application state and logfile can provide insights into what is happening behind the scenes.

Note: To better understand what is happening under the hood and aid in troubleshooting, checkout the [Pipeline documentation](pipeline.md) as well.

## Application State

Each stage of the RAG pipeline stores its data in the application state. 

In order for a successful RAG conversation to take place the following state values must NOT be null:
- `documents` - if null, there was an error processing your documents
- `llm` - if null, there was an error creating the Ollama LLM instance
- `query_engine` - if null, errors occurred when creating embeddings for your your documents

To view the current application state:
- Navigate to the Settings panel
- Toggle the Advanced Options slider
- State is now visible at the bottom of Settings
- Verify that the above state values are valid

## Log File

By default, Local RAG will create a `local-rag.log` file in the root application folder.

Each step of the RAG process is logged into this file whether the required step was successful or encountered an error. 

Reviewing this log can give you insights into what took place when processing your documents.