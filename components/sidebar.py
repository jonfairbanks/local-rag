import datetime
import os

import utils.helpers as func
import utils.ollama as ollama
import utils.llama_index as llama_index

import streamlit as st


def sidebar():
    with st.sidebar:
        tab1, tab2, tab3, tab4 = st.sidebar.tabs(
            ["File Upload", "GitHub Repo", "Settings", "About"]
        )

        ###################################
        #
        # File Upload
        #
        ###################################

        with tab1:
            st.header("Directly import local files")
            st.caption(
                "Convert your local files to embeddings for utilization during chat"
            )
            st.write("")

            uploaded_files = st.file_uploader(
                "Select Files",
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
                st.session_state["file_list"] = uploaded_files

                with st.status("Preparing data...", expanded=True) as status:
                    st.caption("Uploading Files Locally...")
                    # Save the files to disk
                    for uploaded_file in uploaded_files:
                        with st.spinner(f"Processing {uploaded_file.name}..."):
                            save_dir = os.getcwd() + "/data"
                            func.save_uploaded_file(uploaded_file, save_dir)

                    st.caption("Loading Embedding Model...")
                    # Create llama-index service-context to use local LLMs and embeddings
                    # with st.spinner('One moment, preparing embedding model...'):
                    try:
                        llm = ollama.create_ollama_llm(
                            st.session_state.selected_model,
                            st.session_state.ollama_endpoint,
                        )
                        service_context = llama_index.create_service_context(llm)
                    except Exception as err:
                        print(f"Setting up Service Context failed: {err}")
                        # st.error("Error setting up the embedding model", icon="😔")

                    st.caption("Processing File Data...")
                    # with st.spinner('Processing your documents...'):
                    try:
                        documents = llama_index.load_documents(
                            save_dir, service_context
                        )
                        st.session_state["documents"] = documents
                    except Exception as err:
                        print(f"Document Load Error: {err}")
                        # st.error("Error processing your documents", icon="😔")

                    st.caption("Creating File Index...")
                    with st.spinner("Processing your documents..."):
                        try:
                            index = llama_index.create_query_engine(
                                documents, service_context
                            )
                            query_engine = index.as_query_engine(
                                similarity_top_k=5,  # Return additional results
                                service_context=service_context,
                            )
                            st.session_state["query_engine"] = query_engine
                        except Exception as err:
                            print(f"Index Creation Error: {err}")

                    status.update(
                        label="Your files are ready. Let's chat!",
                        state="complete",
                        expanded=False,
                    )

        ###################################
        #
        # GitHub Repo
        #
        ###################################

        with tab2:
            st.header("Import files from a GitHub repo")
            st.caption(
                "Convert a GitHub repo to embeddings for utilization during chat"
            )
            st.write("")

            st.text_input(
                "GitHub repo",
                placeholder="jonfairbanks/local-rag",
                key="github_repo",
                value=st.session_state.github_repo,
                on_change=func.process_github_repo,
                args=(st.session_state.github_repo,),
            )
            st.button(
                "Process Repo",
                on_click=func.process_github_repo,
                args=(st.session_state.github_repo,),
                disabled=True,
            )

        ###################################
        #
        # Settings
        #
        ###################################

        with tab3:
            st.header("Settings")
            st.caption("Configure Local RAG settings and integrations")
            st.write("")

            st.subheader("Chat")
            st.text_input(
                "Ollama Endpoint",
                key="ollama_endpoint",
                placeholder="http://localhost:11434",
                value=st.session_state.ollama_endpoint,
                on_change=ollama.get_models,
                # args=(st.session_state.ollama_endpoint, )
            )
            st.selectbox("Model", st.session_state.ollama_models, key="selected_model")
            if st.session_state.ollama_endpoint is not None:
                st.button(
                    "Refresh Models",
                    on_click=ollama.get_models,
                    # args=(st.session_state.ollama_endpoint, )
                )
            st.write("")

            st.subheader("Embeddings")
            st.selectbox("Model", ["Default (bge-large-en)"], disabled=True)
            st.write("")

            st.subheader("Current State")
            st.write(st.session_state)

        ###################################
        #
        # About
        #
        ###################################

        with tab4:
            st.title("📚 Local RAG")
            st.caption(
                f"Developed by Jon Fairbanks &copy; {datetime.datetime.now().year}"
            )
            st.write("")

            st.subheader("Links")
            st.markdown(
                """
                * [GitHub](https://github.com/jonfairbanks/local-rag)
                * [Docker Hub](#)
            """
            )

            st.subheader("Resources")
            st.markdown(
                """
                * [What is RAG?](https://blogs.nvidia.com/blog/what-is-retrieval-augmented-generation/)
                * [What are embeddings?](https://aws.amazon.com/what-is/embeddings-in-machine-learning/)
            """
            )

            st.subheader("Help")
            st.markdown(
                """
                * [Bug Reports](https://github.com/jonfairbanks/local-rag/issues)
                * [Feature Requests](https://github.com/jonfairbanks/local-rag/discussions/new?category=ideas)
            """
            )
