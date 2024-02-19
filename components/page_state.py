import streamlit as st


def set_initial_state():
    if "ollama_endpoint" not in st.session_state:
        st.session_state["ollama_endpoint"] = "http://localhost:11434"  # Revert to None

    if "embedding_model" not in st.session_state:
        st.session_state["embedding_model"] = None

    if "ollama_models" not in st.session_state:
        st.session_state["ollama_models"] = []

    if "selected_model" not in st.session_state:
        st.session_state["selected_model"] = None

    if "top_k" not in st.session_state:
        st.session_state["top_k"] = 5

    if "github_repo" not in st.session_state:
        st.session_state["github_repo"] = None

    if "file_list" not in st.session_state:
        st.session_state["file_list"] = []

    if "embedding_model" not in st.session_state:
        st.session_state["embedding_model"] = None

    if "chunk_size" not in st.session_state:
        st.session_state["chunk_size"] = None

    if "documents" not in st.session_state:
        st.session_state["documents"] = None

    if "query_engine" not in st.session_state:
        st.session_state["query_engine"] = None

    if "messages" not in st.session_state:
        st.session_state["messages"] = [
            {
                "role": "assistant",
                "content": "Hello! Import some files or ingest a GitHub repo and we can get started.",
            }
        ]
