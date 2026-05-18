import streamlit as st

import utils.logs as logs

from utils.ollama import default_embedding_model, get_models, get_embedding_models
from utils.browser_settings import (
    ensure_ollama_endpoint,
    restore_settings_from_browser_storage,
    should_refresh_models_for_endpoint,
)


def default_chat_model(models):
    """Return the preferred default chat model from discovered Ollama models."""
    preferred_models = (
        "gemma4:latest",
        "llama3:8b",
        "llama2:7b",
    )

    for model in preferred_models:
        if model in models:
            return model

    if models:
        return models[0]

    return None


def ensure_valid_model_selections(state):
    """Keep selected model values consistent with discovered model lists."""
    chat_models = state.get("ollama_models", [])
    if state.get("selected_model") not in chat_models:
        state["selected_model"] = default_chat_model(chat_models)

    if state.get("embedding_backend") == "Ollama":
        embedding_models = state.get("ollama_embedding_models", [])
        if state.get("ollama_embedding_model") not in embedding_models:
            state["ollama_embedding_model"] = default_embedding_model(embedding_models)


def set_initial_state():
    restore_settings_from_browser_storage()

    ###########
    # General #
    ###########

    if "sidebar_state" not in st.session_state:
        st.session_state["sidebar_state"] = "expanded"

    ensure_ollama_endpoint(st.session_state)

    if "embedding_backend" not in st.session_state:
        st.session_state["embedding_backend"] = "Ollama"

    if "ollama_embedding_model" not in st.session_state:
        st.session_state["ollama_embedding_model"] = "embeddinggemma:latest"

    if "embedding_model" not in st.session_state:
        st.session_state["embedding_model"] = "Default (gte-modernbert-base)"

    if should_refresh_models_for_endpoint(st.session_state, "ollama_models"):
        try:
            models = get_models()
            st.session_state["ollama_models"] = models
        except Exception:
            st.session_state["ollama_models"] = []
            pass
        st.session_state["ollama_models_endpoint"] = st.session_state["ollama_endpoint"]

    if should_refresh_models_for_endpoint(st.session_state, "ollama_embedding_models"):
        try:
            models = get_embedding_models()
            st.session_state["ollama_embedding_models"] = models
        except Exception:
            st.session_state["ollama_embedding_models"] = []
            pass
        st.session_state["ollama_embedding_models_endpoint"] = st.session_state["ollama_endpoint"]

    if "selected_model" not in st.session_state:
        st.session_state["selected_model"] = default_chat_model(
            st.session_state.get("ollama_models", [])
        )

    ensure_valid_model_selections(st.session_state)

    if "messages" not in st.session_state:
        st.session_state["messages"] = [
            {
                "role": "assistant",
                "content": "Welcome to Local RAG! To begin, please either import some files or ingest a GitHub repo. Once you've completed those steps, we can continue the conversation and explore how I can assist you further.",
            }
        ]

    ################################
    #  Files, Documents & Websites #
    ################################

    if "file_list" not in st.session_state:
        st.session_state["file_list"] = []

    if "processed_file_signature" not in st.session_state:
        st.session_state["processed_file_signature"] = None

    if "processing_file_signature" not in st.session_state:
        st.session_state["processing_file_signature"] = None

    if "file_ingestion_stages" not in st.session_state:
        st.session_state["file_ingestion_stages"] = []

    if "github_ingestion_stages" not in st.session_state:
        st.session_state["github_ingestion_stages"] = []

    if "website_ingestion_stages" not in st.session_state:
        st.session_state["website_ingestion_stages"] = []

    if "github_repo" not in st.session_state:
        st.session_state["github_repo"] = ""
    elif st.session_state["github_repo"] is None:
        st.session_state["github_repo"] = ""

    if "processed_github_repo" not in st.session_state:
        st.session_state["processed_github_repo"] = None

    if "websites" not in st.session_state:
        st.session_state["websites"] = []

    if "new_website" not in st.session_state:
        st.session_state["new_website"] = ""

    if "website_input_error" not in st.session_state:
        st.session_state["website_input_error"] = None

    ###############
    # Llama-Index #
    ###############

    if "llm" not in st.session_state:
        st.session_state["llm"] = None

    if "documents" not in st.session_state:
        st.session_state["documents"] = None

    if "query_engine" not in st.session_state:
        st.session_state["query_engine"] = None

    if "chat_mode" not in st.session_state:
        st.session_state["chat_mode"] = "compact"

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
        st.session_state["top_k"] = 3

    if "embedding_model" not in st.session_state:
        st.session_state["embedding_model"] = None

    if "other_embedding_model" not in st.session_state:
        st.session_state["other_embedding_model"] = None

    if "chunk_size" not in st.session_state:
        st.session_state["chunk_size"] = 1024

    if "chunk_overlap" not in st.session_state:
        st.session_state["chunk_overlap"] = 200
