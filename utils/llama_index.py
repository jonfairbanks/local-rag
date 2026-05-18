import os
from typing import Optional

# Transformers 5.x can emit a large volume of non-actionable alias warnings
# during startup. Keep app logs focused on failures we can act on.
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")

import streamlit as st
import ollama
from pydantic import Field

import utils.logs as logs

from llama_index.core.embeddings import BaseEmbedding

# This is not used but required by llama-index and must be set FIRST
os.environ["OPENAI_API_KEY"] = "sk-abc123"

from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    Settings,
)
from llama_index.core.ingestion import run_transformations


class ProgressReportingEmbedding(BaseEmbedding):
    """Delegate embeddings while reporting exact batch progress."""

    wrapped_model: BaseEmbedding
    progress_callback: object = Field(exclude=True)
    total_texts: int = Field(default=0)
    completed_texts: int = Field(default=0)

    def _get_query_embedding(self, query: str):
        return self.wrapped_model.get_query_embedding(query)

    async def _aget_query_embedding(self, query: str):
        return await self.wrapped_model.aget_query_embedding(query)

    def _get_text_embedding(self, text: str):
        return self.wrapped_model.get_text_embedding(text)

    def get_text_embedding_batch(self, texts, show_progress=False, **kwargs):
        self.total_texts = len(texts)
        result = []
        batch_size = self.wrapped_model.embed_batch_size
        for start in range(0, len(texts), batch_size):
            batch = texts[start:start + batch_size]
            result.extend(
                self.wrapped_model.get_text_embedding_batch(
                    batch,
                    show_progress=False,
                    **kwargs,
                )
            )
            self.completed_texts += len(batch)
            self.progress_callback(self.completed_texts, self.total_texts)
        return result


class OllamaEmbedding(BaseEmbedding):
    """LlamaIndex embedding adapter backed by an Ollama server."""

    base_url: str = Field(description="Ollama server base URL")

    def _client(self):
        return ollama.Client(host=self.base_url)

    def _get_query_embedding(self, query: str):
        return self._client().embed(model=self.model_name, input=query).embeddings[0]

    async def _aget_query_embedding(self, query: str):
        return self._get_query_embedding(query)

    def _get_text_embedding(self, text: str):
        return self._client().embed(model=self.model_name, input=text).embeddings[0]


###################################
#
# Setup Embedding Model
#
###################################


@st.cache_resource(show_spinner=False)
def setup_embedding_model(
    model: str,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
    backend: str = "Local Hugging Face",
    ollama_endpoint: Optional[str] = None,
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
        if backend == "Ollama":
            if not ollama_endpoint:
                raise ValueError("Ollama endpoint is required for Ollama embeddings")
            Settings.embed_model = OllamaEmbedding(
                model_name=model,
                base_url=ollama_endpoint,
            )
            logs.log.info(f"Using Ollama model {model} to generate embeddings")
        else:
            try:
                from torch import cuda
                device = "cpu" if not cuda.is_available() else "cuda"
            except Exception:
                device = "cpu"
            from llama_index.embeddings.huggingface import HuggingFaceEmbedding

            logs.log.info(f"Using {device} to generate embeddings")
            Settings.embed_model = HuggingFaceEmbedding(
                model_name=model,
                device=device,
            )

        if chunk_size is not None:
            Settings.chunk_size = chunk_size
        if chunk_overlap is not None:
            Settings.chunk_overlap = chunk_overlap

        logs.log.info(f"Embedding model created successfully")

        return
    except Exception as err:
        logs.log.error(f"Failed to setup the embedding model: {err}")
        raise


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
        documents = files.load_data()
        logs.log.info(f"Loaded {len(documents):,} documents from files")
        return documents
    except Exception as err:
        logs.log.error(f"Error creating data index: {err}")
        raise Exception(f"Error creating data index: {err}")


###################################
#
# Create Document Index
#
###################################


def create_index(documents, progress_callback=None):
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
        nodes = run_transformations(
            documents,
            Settings.transformations,
            show_progress=True,
        )

        if progress_callback is not None:
            progress_callback(0, len(nodes))
            embed_model = ProgressReportingEmbedding(
                wrapped_model=Settings.embed_model,
                progress_callback=progress_callback,
                model_name=Settings.embed_model.model_name,
                embed_batch_size=Settings.embed_model.embed_batch_size,
            )
        else:
            embed_model = Settings.embed_model

        index = VectorStoreIndex(
            nodes=nodes,
            embed_model=embed_model,
            show_progress=False,
        )

        logs.log.info("Index created from loaded documents successfully")

        return index
    except Exception as err:
        logs.log.error(f"Index creation failed: {err}")
        raise Exception(f"Index creation failed: {err}")


###################################
#
# Create Query Engine
#
###################################


# @st.cache_resource(show_spinner=False)
def create_query_engine(documents, progress_callback=None):
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
        index = create_index(documents, progress_callback=progress_callback)

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
