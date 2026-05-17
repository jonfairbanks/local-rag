import json

import streamlit as st

import utils.ollama as ollama

from datetime import datetime


def _refresh_models():
    ollama.get_models()
    ollama.get_embedding_models()


def _refresh_embedding_models():
    ollama.get_embedding_models()


def settings():
    st.header("Settings")
    st.caption("Configure Local RAG settings and integrations")

    st.subheader("Chat")
    chat_settings = st.container(border=True)
    with chat_settings:
        st.text_input(
            "Ollama Endpoint",
            key="ollama_endpoint",
            placeholder="http://localhost:11434",
            on_change=_refresh_models,
        )
        st.selectbox(
            "Chat Model",
            st.session_state["ollama_models"],
            key="selected_model",
            disabled= len(st.session_state["ollama_models"])==0,
            placeholder= "Select Chat Model" if len(st.session_state["ollama_models"])>0 else "No Models Available",
        )
        st.button(
            "Refresh Models",
            key="refresh_chat_models",
            on_click=ollama.get_models,
        )
        if st.session_state["advanced"] == True:
            st.select_slider(
                "Top K",
                options=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                help="The number of most similar documents to retrieve in response to a query.",
                value=st.session_state["top_k"],
                key="top_k",
            )
            # st.text_area(
            #     "System Prompt",
            #     value=st.session_state["system_prompt"],
            #     key="system_prompt",
            # )
            st.selectbox(
                "Chat Mode",
                (
                    "compact",
                    "refine",
                    "tree_summarize",
                    "simple_summarize",
                    "accumulate",
                    "compact_accumulate",
                ),
                help="Sets the [Llama Index Query Engine chat mode](https://github.com/run-llama/llama_index/blob/main/docs/module_guides/deploying/query_engine/response_modes.md) used when creating the Query Engine. Default: `compact`.",
                key="chat_mode",
                disabled=True,
            )
            st.write("")

    st.subheader(
        "Embeddings",
        help="Embeddings are numerical representations of data, useful for tasks like document clustering and similarity detection when processing files, as they encode semantic meaning for efficient manipulation and retrieval.",
    )
    embedding_settings = st.container(border=True)
    with embedding_settings:
        embedding_backend = st.selectbox(
            "Backend",
            ["Ollama", "Local Hugging Face"],
            key="embedding_backend",
        )
        if embedding_backend == "Ollama":
            st.selectbox(
                "Embedding Model",
                st.session_state["ollama_embedding_models"],
                key="ollama_embedding_model",
                disabled=len(st.session_state["ollama_embedding_models"]) == 0,
                placeholder=(
                    "Select Model"
                    if len(st.session_state["ollama_embedding_models"]) > 0
                    else "No Embedding Models Available"
                ),
            )
            st.button(
                "Refresh Models",
                key="refresh_embedding_models",
                on_click=_refresh_embedding_models,
            )
            st.caption("Need one? Pull an Ollama embedding model first, e.g. `ollama pull embeddinggemma`.")
        else:
            embedding_model = st.selectbox(
                "Model",
                [
                    "Default (gte-modernbert-base)",
                    "Higher Quality (Qwen3-Embedding-0.6B)",
                    "Other",
                ],
                key="embedding_model",
            )
            if embedding_model == "Other":
                st.text_input(
                    "HuggingFace Model",
                    key="other_embedding_model",
                    placeholder="Qwen/Qwen3-Embedding-0.6B",
                )
        if st.session_state["advanced"] == True:
            st.caption(
                "View the [MTEB Embeddings Leaderboard](https://huggingface.co/spaces/mteb/leaderboard)"
            )
            st.text_input(
                "Chunk Size",
                help="Reducing `chunk_size` improves embedding precision by focusing on smaller text portions. This enhances information retrieval accuracy but escalates computational demands due to processing more chunks.",
                key="chunk_size",
                placeholder="1024",
                value=st.session_state["chunk_size"],
            )
            st.text_input(
                "Chunk Overlap",
                help="The amount of overlap between two consecutive chunks. A higher overlap value helps maintain continuity and context across chunks.",
                key="chunk_overlap",
                placeholder="200",
                value=st.session_state["chunk_overlap"],
            )

    st.subheader("Export Data")
    export_data_settings = st.container(border=True)
    with export_data_settings:
        st.write("Chat History")
        st.download_button(
            label="Download",
            data=json.dumps(st.session_state["messages"]),
            file_name=f"local-rag-chat-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.json",
            mime="application/json",
        )

    st.toggle("Advanced Settings", key="advanced")

    if st.session_state["advanced"] == True:
        with st.expander("Current Application State"):
            state = dict(sorted(st.session_state.items()))
            st.write(state)
