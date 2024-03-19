import os

import streamlit as st

import utils.logs as logs

from torch import cuda
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# This is not used but required by llama-index and must be set FIRST
os.environ["OPENAI_API_KEY"] = "sk-abc123"

from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    ServiceContext,
    set_global_service_context,
)


###################################
#
# Setup Embedding Model
#
###################################


@st.cache_resource(show_spinner=False)
def setup_embedding_model(
    model: str,
):
    """
    Sets up an embedding model using the Hugging Face library.

    Args:
        model (str): The name of the embedding model to use.

    Returns:
        An instance of the HuggingFaceEmbedding class, configured with the specified model and device.

    Raises:
        ValueError: If the specified model is not a valid embedding model.

    Notes:
        The `device` parameter can be set to 'cpu' or 'cuda' to specify the device to use for the embedding computations. If 'cuda' is used and CUDA is available, the embedding model will be run on the GPU. Otherwise, it will be run on the CPU.
    """
    device = "cpu" if not cuda.is_available() else "cuda"
    logs.log.info(f"Using {device} to generate embeddings")
    embed_model = HuggingFaceEmbedding(
        model_name=model,
        device=device,
    )
    logs.log.info(f"Embedding model created successfully")
    return embed_model


###################################
#
# Create Service Context
#
###################################

# TODO: Migrate to LlamaIndex.Settings: https://docs.llamaindex.ai/en/stable/module_guides/supporting_modules/service_context_migration.html


def create_service_context(
    llm,  # TODO: Determine type
    system_prompt: str = None,
    embed_model: str = "BAAI/bge-large-en-v1.5",
    chunk_size: int = 1024,  # Llama-Index default is 1024
    chunk_overlap: int = 200,  # Llama-Index default is 20
):
    """
    Creates a service context for the Llama language model.

    Args:
        llm (tbd): The Ollama language model to use.
        system_prompt (str): An optional string that can be used as the system prompt when generating text. If no system prompt is passed, the default value will be used.
        embed_model (str): The name of the embedding model to use. Can also be a path to a saved embedding model.
        chunk_size (int): The size of each chunk of text to generate. Defaults to 1024.
        chunk_overlap (int): The amount of overlap between adjacent chunks of text. Defaults to 200.

    Returns:
        A ServiceContext instance, configured with the specified Llama model, system prompt, and embedding model.

    Raises:
        ValueError: If the specified Llama model is not a valid Llama model.
        ValueError: If the specified embed_model is not a valid embedding model.

    Notes:
        The `embed_model` parameter can be set to a path to a saved embedding model, or to a string representing the name of the embedding model to use. If the `embed_model` parameter is set to a path, it will be loaded and used to create the service context. Otherwise, it will be created using the specified name.
        The `chunk_size` and `chunk_overlap` parameters can be adjusted to control how much text is generated in each chunk and how much overlap there is between chunks.
    """
    try:
        embedding_model = setup_embedding_model(embed_model)
        service_context = ServiceContext.from_defaults(
            llm=llm,
            system_prompt=system_prompt,
            embed_model=embedding_model,
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


def load_documents(data_dir: str):
    """
    Loads documents from a directory of files.

    Args:
        data_dir (str): The path to the directory containing the documents to be loaded.

    Returns:
        A list of documents, where each document is a string representing the content of the corresponding file.

    Raises:
        Exception: If there is an error creating the data index.

    Notes:
        The `data_dir` parameter should be a path to a directory containing files that represent the documents to be loaded. The function will iterate over all files in the directory, and load their contents into a list of strings.
    """
    try:
        files = SimpleDirectoryReader(input_dir=data_dir, recursive=True)
        documents = files.load_data(files)
        logs.log.info(f"Loaded {len(documents):,} documents from files")
        return documents
    except Exception as err:
        logs.log.error(f"Error creating data index: {err}")
    finally:
        for file in os.scandir(data_dir):
            if file.is_file() and not file.name.startswith(
                ".gitkeep"
            ):  # TODO: Confirm syntax here
                os.remove(file.path)
        logs.log.info(f"Document loading complete; removing local file(s)")


###################################
#
# Create Document Index
#
###################################


@st.cache_data(show_spinner=False)
def create_index(_documents, _service_context):
    """
    Creates an index from the provided documents and service context.

    Args:
        documents (list[str]): A list of strings representing the content of the documents to be indexed.
        service_context (ServiceContext): The service context to use when creating the index.

    Returns:
        An instance of `VectorStoreIndex`, containing the indexed data.

    Raises:
        Exception: If there is an error creating the index.

    Notes:
        The `documents` parameter should be a list of strings representing the content of the documents to be indexed. The `service_context` parameter should be an instance of `ServiceContext`, providing information about the Llama model and other configuration settings for the index.
    """

    try:
        index = VectorStoreIndex.from_documents(
            documents=_documents, service_context=_service_context, show_progress=True
        )

        logs.log.info("Index created from loaded documents successfully")

        return index
    except Exception as err:
        logs.log.error(f"Index creation failed: {err}")
        return False


###################################
#
# Create Query Engine
#
###################################


@st.cache_resource(show_spinner=False)
def create_query_engine(_documents, _service_context):
    """
    Creates a query engine from the provided documents and service context.

    Args:
        documents (list[str]): A list of strings representing the content of the documents to be indexed.
        service_context (ServiceContext): The service context to use when creating the index.

    Returns:
        An instance of `QueryEngine`, containing the indexed data and allowing for querying of the data using a variety of parameters.

    Raises:
        Exception: If there is an error creating the query engine.

    Notes:
        The `documents` parameter should be a list of strings representing the content of the documents to be indexed. The `service_context` parameter should be an instance of `ServiceContext`, providing information about the Llama model and other configuration settings for the index.

        This function uses the `create_index` function to create an index from the provided documents and service context, and then creates a query engine from the resulting index. The `query_engine` parameter is used to specify the parameters of the query engine, including the number of top-ranked items to return (`similarity_top_k`), the response mode (`response_mode`), and the service context (`service_context`).
    """
    try:
        index = create_index(_documents, _service_context)

        query_engine = index.as_query_engine(
            similarity_top_k=st.session_state["top_k"],
            response_mode=st.session_state["chat_mode"],
            service_context=_service_context,
            streaming=True,
            # verbose=True, # Broken?
        )

        st.session_state["query_engine"] = query_engine

        logs.log.info("Query Engine created successfully")

        return query_engine
    except Exception as e:
        logs.log.error(f"Error when creating Query Engine: {e}")
