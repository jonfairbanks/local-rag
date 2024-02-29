import os

import streamlit as st

import utils.logs as logs


# This is not used but required by llama-index and must be imported FIRST
os.environ["OPENAI_API_KEY"] = "sk-abc123"

from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    ServiceContext,
    set_global_service_context,
)

###################################
#
# Create Service Context
#
###################################


@st.cache_resource(show_spinner=False)
def create_service_context(
    _llm,  # TODO: Determine type
    system_prompt: str = None,  # TODO: What are the implications of no system prompt being passed?
    embed_model: str = "BAAI/bge-large-en-v1.5",
    chunk_size: int = 1024,  # Llama-Index default is 1024
    chunk_overlap: int = 20,  # Llama-Index default is 1024
):
    """
    Create a service context with the specified language model and embedding model.

    Parameters:
    - llm (TODO: Determine type): The Llama-Index LLM instance to use for generation.
    - system_prompt (str, optional): System prompt to use when creating the LLM.
    - embed_model (str, optional): The embedding model to use for similarity search. Default is `BAAI/bge-large-en-v1.5`.
    - chunk_size (int, optional): The maximum number of tokens to consider at once. Default is 1024.
    - chunk_overlap (int, optional): The amount of shared content between two consecutive chunks of data. Smaller = more precise. Default is 20.

    Returns:
    - A `ServiceContext` object with the specified settings.
    """
    formatted_embed_model = f"local:{embed_model}"
    try:
        service_context = ServiceContext.from_defaults(
            llm=_llm,
            system_prompt=system_prompt,
            embed_model=formatted_embed_model,
            chunk_size=int(chunk_size),
            # chunk_overlap=int(chunk_overlap),
        )
        logs.log.info(f"Service Context created successfully")
        st.session_state["service_context"] = service_context
        # Note: this may be redundant since service_context is returned
        set_global_service_context(service_context)
        return service_context
    except Exception as e:
        logs.log.error(f"Failed to create service_context: {e}")
        Exception(f"Failed to create service_context: {e}")  # TODO: Redundant?


###################################
#
# Load Documents
#
###################################


@st.cache_resource(show_spinner=False)
def load_documents(data_dir: str):
    """
    Creates a data index from documents stored in a directory.

    Parameters:
        - data_dir: Directory to load files from for embedding

    Returns:
        - TODO: FIX -- VectorStoreIndex: An index containing vector representations of documents in the specified directory.
        - None: If an exception occurs during the creation of the data index.
    """
    try:
        files = SimpleDirectoryReader(input_dir=data_dir, recursive=True)
        documents = files.load_data(files)
        logs.log.info(f"Loaded {len(documents):,} documents from files")
        return documents
    except Exception as err:
        logs.log.error(f"Error creating data index: {err}")
        return None
    finally:
        for file in os.scandir(data_dir):
            if file.is_file() and not file.name.startswith(".gitkeep"): # TODO: Confirm syntax here
                os.remove(file.path)
        logs.log.info(f"Document loading complete; removing local file(s)")


###################################
#
# Create Query Engine
#
###################################


@st.cache_resource(show_spinner=False)
def create_query_engine(_documents, _service_context):
    """
    Create a query engine from a set of documents.

    This function creates a vector database index using the given documents and
    service context, and then returns a query engine that can be used to perform
    natural language queries on the index.

    Parameters:
        - documents (VectorStoreIndex): A list of Document objects containing the
        raw text data to be indexed.
        - service_context (ServiceContext): A ServiceContext object providing any
        necessary configuration or authentication information for the underlying
        index implementation.

    Returns:
        - query_engine (QueryEngine): A QueryEngine instance that can be used to
        perform natural language queries on the indexed documents.
    """
    try:
        index = VectorStoreIndex.from_documents(
            documents=_documents, service_context=_service_context, show_progress=True
        )

        logs.log.info("Index created from loaded documents successfully")

        query_engine = index.as_query_engine(
            similarity_top_k=st.session_state["top_k"],
            service_context=_service_context,
            streaming=True,
        )

        logs.log.info("Query Engine created successfully")

        st.session_state["query_engine"] = query_engine

        return query_engine
    except Exception as e:
        logs.log.error(f"Error when creating Query Engine: {e}")
        return
