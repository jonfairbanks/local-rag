import streamlit as st

def set_initial_state():
    if 'ollama_endpoint' not in st.session_state:
        st.session_state['ollama_endpoint'] = None

    if 'embedding_model' not in st.session_state:
        st.session_state['embedding_model'] = None

    if 'ollama_models' not in st.session_state:
        st.session_state['ollama_models'] = []

    if 'selected_model' not in st.session_state:
        st.session_state['selected_model'] = None

    if 'github_repo' not in st.session_state:
        st.session_state['github_repo'] = None

    if 'file_list' not in st.session_state:
        st.session_state['file_list'] = []

    if "messages" not in st.session_state:
        st.session_state["messages"] = [{
            "role": "assistant", 
            "content": "Hello! Import some files or ingest a GitHub repo and we can get started."
        }]