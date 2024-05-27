import os

import streamlit as st

import utils.logs as logs

from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import StorageContext, load_index_from_storage

from typing import Sequence
from llama_index.core.schema import Document

# This is not used but required by llama-index and must be set FIRST
os.environ["OPENAI_API_KEY"] = "sk-abc123"

from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    Settings,
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
    try:
        from torch import cuda
        device = "cpu" if not cuda.is_available() else "cuda"
    except:
        device = "cpu"
    finally:
        logs.log.info(f"Using {device} to generate embeddings")

    try:
        Settings.embed_model = HuggingFaceEmbedding(
            model_name=model,
            device=device,
        )

        logs.log.info(f"Embedding model created successfully")
        
        return
    except Exception as err:
        print(f"Failed to setup the embedding model: {err}")


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
        raise Exception(f"Error creating data index: {err}")
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


@st.cache_resource(show_spinner=False)
def create_index(_documents):
    """
    Creates an index from the provided documents and service context.

    Args:
        documents (list[str]): A list of strings representing the content of the documents to be indexed.

    Returns:
        An instance of `VectorStoreIndex`, containing the indexed data.

    Raises:
        Exception: If there is an error creating the index.

    Notes:
        The `documents` parameter should be a list of strings representing the content of the documents to be indexed.
    """

    try:
        index = VectorStoreIndex.from_documents(
            documents=_documents, show_progress=True
        )

        logs.log.info("Index created from loaded documents successfully")

        return index
    except Exception as err:
        logs.log.error(f"Index creation failed: {err}")
        raise Exception(f"Index creation failed: {err}")


def get_persisted_index(
    index_id: str, persist_dir: str, _documents: Sequence[Document]
):
    try:
        # Rebuild storage context
        storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
        # Load index
        index = load_index_from_storage(storage_context, index_id=index_id)
        logs.log.info("Index loaded from persisted storage successfully")

        st.caption("✔️ Loaded Persisted Index")

        # Check if all upload documents are present in the index
        if _documents is not None:
            document_hashes = index.docstore.get_all_document_hashes()

            for doc in _documents:
                if doc.hash not in document_hashes:
                    logs.log.info(
                        "Document {} not found in index. Adding it...".format(
                            doc.get_doc_id()
                        )
                    )
                    index.insert(doc)

    except Exception as e:
        logs.log.error(f"Error loading persisted index: {e}")

        if _documents is not None:
            index = create_index(_documents)
            index.set_index_id(index_id)
            index.storage_context.persist(persist_dir=persist_dir)
            st.caption("✔️ Created Persisted Index")
        else:
            raise Exception(f"Cannot create persisted index without documents.")

    return index


###################################
#
# Create Query Engine
#
###################################


# @st.cache_resource(show_spinner=False)
def create_query_engine(_documents):
    """
    Creates a query engine from the provided documents and service context.

    Args:
        documents (list[str]): A list of strings representing the content of the documents to be indexed.

    Returns:
        An instance of `QueryEngine`, containing the indexed data and allowing for querying of the data using a variety of parameters.

    Raises:
        Exception: If there is an error creating the query engine.

    Notes:
        The `documents` parameter should be a list of strings representing the content of the documents to be indexed.

        This function uses the `create_index` function to create an index from the provided documents and service context, and then creates a query engine from the resulting index. The `query_engine` parameter is used to specify the parameters of the query engine, including the number of top-ranked items to return (`similarity_top_k`) and the response mode (`response_mode`).
    """
    try:
        if st.session_state["persisted_index_id"]:
            index = get_persisted_index(
                index_id=st.session_state["persisted_index_id"],
                persist_dir=os.getcwd() + "/indices",
                _documents=_documents,
            )
        else:
            index = create_index(_documents)
            st.caption("✔️ Created File Index")

        query_engine = index.as_query_engine(
            similarity_top_k=st.session_state["top_k"],
            response_mode=st.session_state["chat_mode"],
            streaming=True,
        )

        st.session_state["query_engine"] = query_engine

        logs.log.info("Query Engine created successfully")

        return query_engine
    except Exception as e:
        logs.log.error(f"Error when creating Query Engine: {e}")
        raise Exception(f"Error when creating Query Engine: {e}")
