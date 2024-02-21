import json

import streamlit as st

import utils.ollama as ollama

from datetime import datetime


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
            on_change=ollama.get_models,
        )
        st.selectbox(
            "Model", st.session_state["ollama_models"], key="selected_model",
        )
        st.button(
            "Refresh", on_click=ollama.get_models,
        )
        if st.session_state["advanced"] == True:
            st.select_slider(
                "Top K",
                options=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                help="A higher Top K will return more results at the expense of accuracy.",
                value=5,
                key="top_k",
            )
            st.text_input(
                "System Prompt",
                value="You are a sophisticated virtual assistant designed to assist users in comprehensively understanding and extracting insights from a wide range of documents at their disposal. Your expertise lies in tackling complex inquiries and providing insightful analyses based on the information contained within these documents.",
                key="system_prompt",
                disabled=True,
            )
            st.selectbox(
                "Chat Mode",
                ("Best", "Condense Question", "Context", "Condense + Context"),
                help="Sets the [Llama-Index Chat Mode](https://docs.llamaindex.ai/en/stable/module_guides/deploying/chat_engines/usage_pattern.html#available-chat-modes) used when creating the Query Engine.",
                disabled=True,
            )
            st.write("")

    st.subheader(
        "Embeddings",
        help="Embeddings help convert your files to a format LLMs can understand.",
    )
    embedding_settings = st.container(border=True)
    with embedding_settings:
        st.selectbox(
            "Model",
            ["Default (bge-large-en-v1.5)", "Best (Salesforce/SFR-Embedding-Mistral)"],
            disabled=True,
        )
        if st.session_state["advanced"] == True:
            st.caption(
                "View the [Embeddings Leaderboard](https://huggingface.co/spaces/mteb/leaderboard)"
            )
            st.text_input(
                "Chunk Size",
                help="This should not exceed the value provided by your embedding model.",
                key="chunk_size",
                placeholder="512",
                value=st.session_state["chunk_size"],
                disabled=True,
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
