import utils.helpers as func
import utils.ollama as ollama

import streamlit as st

def sidebar():
    with st.sidebar:
        tab1, tab2, tab3 = st.sidebar.tabs(["File Upload", "GitHub Repo", "Settings"])

        with tab1:
            st.header("Directly import local files")
            st.caption("Convert local files to embeddings for utilization during chat")
            uploaded_files = st.file_uploader(
                'Select Files', 
                accept_multiple_files=True,
                # type=(
                #     "css",
                #     "csv", 
                #     "docx", 
                #     "epub",
                #     "html",
                #     "ipynb", 
                #     "jpeg", 
                #     "jpg",
                #     "js",
                #     "md", 
                #     "mp3", 
                #     "mp4", 
                #     "pdf", 
                #     "png", 
                #     "ppt", 
                #     "pptx",
                #     "py"
                # )
            )
            if len(uploaded_files) > 0:
                #print(f"File List: {uploaded_files}")
                st.session_state['file_list'] = uploaded_files
                for uploaded_file in uploaded_files:
                    st.write("Filename:", uploaded_file.name)

        with tab2:
            st.header("Import files from a GitHub repo")
            st.caption("Convert a GitHub repo to embeddings for utilization during chat")
            st.text_input(
                'GitHub repo', 
                placeholder="jonfairbanks/notebooks",
                key="github_repo",
                value=st.session_state.github_repo,
                on_change=func.process_github_repo,
                args=(st.session_state.github_repo, )
            )
            st.button(
                "Process Repo",
                on_click=func.process_github_repo,
                args=(st.session_state.github_repo, )          
            )

        with tab3:
            st.header("Settings")
            st.caption("Configure Local RAG settings and integrations")
            st.text_input(
                'Ollama Endpoint',
                key="ollama_endpoint",
                placeholder="http://localhost:11434/api",
                value=st.session_state.ollama_endpoint,
                on_change=ollama.get_models,
                #args=(st.session_state.ollama_endpoint, )
            )
            st.selectbox('Embedding Model', ["Default"])
            st.selectbox(
                'Chat Model', 
                st.session_state.ollama_models,
                key="selected_model"
            )
            if (st.session_state.ollama_endpoint is not None):
                st.button(
                    "Refresh Models",
                    on_click=ollama.get_models,
                    #args=(st.session_state.ollama_endpoint, )
                )
            st.subheader("Current State")
            st.write(st.session_state)