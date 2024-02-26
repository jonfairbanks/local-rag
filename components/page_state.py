import streamlit as st

from utils.ollama import get_models


def set_initial_state():

    ###########
    # General #
    ###########

    if "ollama_endpoint" not in st.session_state:
        st.session_state["ollama_endpoint"] = "http://localhost:11434"

    if "embedding_model" not in st.session_state:
        st.session_state["embedding_model"] = None

    if "ollama_models" not in st.session_state:
        try:
            models = get_models()
            st.session_state["ollama_models"] = models
        except Exception as err:
            print(
                f"Warning: Initial loading of Ollama models failed. You might be hosting Ollama somewhere other than localhost. -- {err}"
            )
            st.session_state["ollama_models"] = []
            pass

    if "selected_model" not in st.session_state:
        st.session_state["selected_model"] = None

    if "messages" not in st.session_state:
        st.session_state["messages"] = [
            {
                "role": "assistant",
                "content": "Hello! Import some files or ingest a GitHub repo and we can get started.",
            }
        ]

    ######################
    #  Files & Documents #
    ######################

    if "file_list" not in st.session_state:
        st.session_state["file_list"] = []

    if "github_repo" not in st.session_state:
        st.session_state["github_repo"] = None

    ###############
    # Llama-Index #
    ###############

    if "documents" not in st.session_state:
        st.session_state["documents"] = None

    if "query_engine" not in st.session_state:
        st.session_state["query_engine"] = None

    #####################
    # Advanced Settings #
    #####################

    if "advanced" not in st.session_state:
        st.session_state["advanced"] = False

    if "system_prompt" not in st.session_state:
        st.session_state["system_prompt"] = (
            "You are a sophisticated virtual assistant designed to assist users in comprehensively understanding and extracting insights from a wide range of documents at their disposal. Your expertise lies in tackling complex inquiries and providing insightful analyses based on the information contained within these documents."
        )

    if "top_k" not in st.session_state:
        st.session_state["top_k"] = (
            3  # Default is 2; increasing to 5 will result in more documents being retrieved
        )

    if "embedding_model" not in st.session_state:
        st.session_state["embedding_model"] = None

    if "other_embedding_model" not in st.session_state:
        st.session_state["other_embedding_model"] = None

    if "chunk_size" not in st.session_state:
        st.session_state["chunk_size"] = 1024
