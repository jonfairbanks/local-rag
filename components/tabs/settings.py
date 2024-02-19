import streamlit as st

import utils.ollama as ollama
#import utils.llama_index as llama_index

def settings(): 
    st.header("Settings")
    st.caption("Configure Local RAG settings and integrations")
    st.write("")

    st.subheader("Chat")
    st.text_input(
        "Ollama Endpoint",
        key="ollama_endpoint",
        placeholder="http://localhost:11434",
        value=st.session_state["ollama_endpoint"],
        on_change=ollama.get_models,
    )
    st.selectbox("Model", st.session_state.ollama_models, key="selected_model")
    if st.session_state["ollama_endpoint"] is not None:
        st.button(
            "Refresh Models",
            on_click=ollama.get_models,
        )
    st.select_slider(
        'Top K',
        options=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        help="A higher Top K will return more results at the expense of accuracy.",
        value=st.session_state["top_k"],
        disabled=True
    )
    st.write("")

    st.subheader("Embeddings")
    st.selectbox("Model", ["Default (bge-large-en-v1.5)", "Best (Salesforce/SFR-Embedding-Mistral)"], disabled=True)
    st.text_input(
        "Chunk Size",
        help="This should not exceed the value provided by your embedding model.",
        key="chunk_size",
        placeholder="1024",
        value=st.session_state["chunk_size"],
        disabled=True
    )
    
    st.divider()
    st.write("")

    with st.expander("Current State"):
        state = dict(sorted(st.session_state.items()))
        st.write(state)