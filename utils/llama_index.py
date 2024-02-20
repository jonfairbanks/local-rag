import os

import streamlit as st

# This is not used but required by llama-index and must be imported FIRST
os.environ["OPENAI_API_KEY"] = "sk-abc123"

from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    ServiceContext,
    set_global_service_context,
)
from llama_index.core.memory import ChatMemoryBuffer

###################################
#
# Create Service Context
#
###################################


def create_service_context(
    llm,  # TODO: Determine type
    embed_model: str = "local:BAAI/bge-large-en-v1.5", # TODO: Allow users to set this
    chunk_size: int = 1024 # TODO: Allow users to set this
):
    """
    Create a service context with the specified language model and embedding model.

    Parameters:
    - llm (TODO: Determine type): The language model to use for generation.
    - embed_model (str, optional): The embedding model to use for similarity search. Default is "local:BAAI/bge-large-en".
    - chunk_size (int, optional): The maximum number of tokens to consider at once. Default is 1024.

    Returns:
    - A `ServiceContext` object with the specified settings.
    """
    service_context = ServiceContext.from_defaults(
        llm=llm, 
        embed_model=embed_model, 
        chunk_size=chunk_size
    )

    set_global_service_context(service_context)

    return service_context


###################################
#
# Create Chat Memory
#
###################################


def create_chat_memory(token_limit: int = 2500):
    """
    Creates a memory buffer for storing chat interactions.

    Parameters:
        - token_limit (int, optional): The maximum number of tokens to store in the memory buffer. Defaults to 2500.

    Returns:
        - ChatMemoryBuffer: An instance of the memory buffer for chat interactions.
    """
    memory = ChatMemoryBuffer.from_defaults(token_limit=token_limit)
    return memory


###################################
#
# Load Documents
#
###################################


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
        data_dir = os.getcwd() + "/data"
        files = SimpleDirectoryReader(input_dir=data_dir, recursive=True)
        documents = files.load_data(files)
        print(f"Loaded {len(documents):,} documents")
        return documents
    except Exception as err:
        print(f"Error creating data index: {err}")
        return None

###################################
#
# Create Query Engine
#
###################################

def create_query_engine(documents, service_context):
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
            documents=documents, service_context=service_context, show_progress=True
        )

        # print(f"Index: {index}")
        # print()

        query_engine = index.as_query_engine(
            similarity_top_k = 5, # Return additional results
            service_context=service_context
        )

        # print(f"Query Engine: {query_engine}")
        # print()

        st.session_state["query_engine"] = query_engine

        return query_engine
    except Exception as e:
        print(f"Error when creating Query Engine: {e}")
        return


    
