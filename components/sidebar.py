import datetime
import time

import utils.helpers as func
import utils.ollama as ollama

import streamlit as st

def sidebar():
    with st.sidebar:
        tab1, tab2, tab3, tab4 = st.sidebar.tabs(["File Upload", "GitHub Repo", "Settings", "About"])

        with tab1:
            st.header("Directly import local files")
            st.caption("Convert your local files to embeddings for utilization during chat")
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
                st.session_state['file_list'] = uploaded_files
                for uploaded_file in uploaded_files:
                    with st.spinner('Processing...'):
                        time.sleep(5)
                        func.process_local_file(uploaded_file)
                    st.write("Filename:", uploaded_file.name)

        with tab2:
            st.header("Import files from a GitHub repo")
            st.caption("Convert a GitHub repo to embeddings for utilization during chat")
            st.text_input(
                'GitHub repo', 
                placeholder="jonfairbanks/local-rag",
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
                placeholder="http://localhost:11434",
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
        
        with tab4:
            st.title("📚 Local RAG")
            st.caption(f"Developed by Jon Fairbanks &copy; {datetime.datetime.now().year}")
            st.write("")
            
            st.subheader("Links")
            st.markdown("""
                * [GitHub](https://github.com/jonfairbanks/local-rag)
                * [Docker Hub](#)
            """)

            st.subheader("Resources")
            st.markdown("""
                * [What is RAG?](https://blogs.nvidia.com/blog/what-is-retrieval-augmented-generation/)
                * [Ollama](https://ollama.com/)
                * [Llama-Index](https://docs.llamaindex.ai/en/stable/index.html)
                * [Streamlit](https://docs.streamlit.io/library/api-reference)
            """)

            st.subheader("Help")
            st.markdown("""
                * [Bug Reports](https://github.com/jonfairbanks/local-rag/issues)
                * [Feature Requests](https://github.com/jonfairbanks/local-rag/discussions/new?category=ideas)
            """)