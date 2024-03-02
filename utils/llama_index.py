import os

import streamlit as st

import utils.logs as logs

from numba import cuda
from llama_index.embeddings.huggingface import ( HuggingFaceEmbedding )

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
# Setup Embedding Model
#
###################################

@st.cache_resource(show_spinner=False)
def setup_embedding_model(
    model: str,
):
    device = 'cpu' if not cuda.is_available() else 'cuda'
    embed_model = HuggingFaceEmbedding(
        model_name=model,
        # embed_batch_size=25, // TODO: Turning this on creates chaos, but has the potential to improve performance
        device=device
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
    system_prompt: str = None,  # TODO: What are the implications of no system prompt being passed?
    embed_model: str = "BAAI/bge-large-en-v1.5",
    chunk_size: int = 1024,  # Llama-Index default is 1024
    chunk_overlap: int = 200,  # Llama-Index default is 200
):
    formatted_embed_model = f"local:{embed_model}"
    try:
        embedding_model = setup_embedding_model(embed_model)
        service_context = ServiceContext.from_defaults(
            llm=llm,
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


def load_documents(data_dir: str):
    try:
        files = SimpleDirectoryReader(input_dir=data_dir, recursive=True)
        documents = files.load_data(files)
        logs.log.info(f"Loaded {len(documents):,} documents from files")
        return documents
    except Exception as err:
        logs.log.error(f"Error creating data index: {err}")
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


@st.cache_data(show_spinner=False)
def create_query_engine(_documents, _service_context):
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

        st.session_state["query_engine"] = query_engine

        logs.log.info("Query Engine created successfully")

        return query_engine
    except Exception as e:
        logs.log.error(f"Error when creating Query Engine: {e}")
