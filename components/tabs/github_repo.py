import os
import shutil

import streamlit as st

import utils.helpers as func
import utils.ollama as ollama
import utils.llama_index as llama_index
import utils.logs as logs


def github_repo():
    # st.header("Import files from a GitHub repo")
    # st.caption("Convert a GitHub repo to embeddings for utilization during chat")
    if st.session_state["selected_model"] is not None:
        st.text_input(
            "Select a GitHub.com repo",
            placeholder="jonfairbanks/local-rag",
            key="github_repo",
        )

        repo_processed = None
        repo_processed = st.button(
            "Process Repo",
            on_click=func.clone_github_repo,
            args=(st.session_state["github_repo"],),
        )  # TODO: Should this be with st.button?

        with st.spinner("Processing..."):
            if repo_processed is True:
                error = None

                ######################################
                # Create Llama-Index service-context #
                # to use local LLMs and embeddings   #
                ######################################

                try:
                    llm = ollama.create_ollama_llm(
                        st.session_state["selected_model"],
                        st.session_state["ollama_endpoint"],
                    )
                    st.session_state["llm"] = llm
                    st.caption("✔️ LLM Initialized")

                    # resp = llm.complete("Hello!")
                    # print(resp)
                except Exception as err:
                    logs.log.error(f"Failed to setup LLM: {err}")
                    error = err
                    st.exception(error)
                    st.stop()

                ####################################
                # Determine embedding model to use #
                ####################################

                embedding_model = st.session_state["embedding_model"]
                hf_embedding_model = None

                if embedding_model == None:
                    hf_embedding_model = "BAAI/bge-large-en-v1.5"

                if embedding_model == "Default (bge-large-en-v1.5)":
                    hf_embedding_model = "BAAI/bge-large-en-v1.5"

                if embedding_model == "Large (Salesforce/SFR-Embedding-Mistral)":
                    hf_embedding_model = "Salesforce/SFR-Embedding-Mistral"

                if embedding_model == "Other":
                    hf_embedding_model = st.session_state["other_embedding_model"]

                try:
                    llama_index.create_service_context(
                        st.session_state["llm"],
                        st.session_state["system_prompt"],
                        hf_embedding_model,
                        st.session_state["chunk_size"],
                        # st.session_state["chunk_overlap"],
                    )
                    st.caption("✔️ Context Created")
                except Exception as err:
                    logs.log.error(f"Setting up Service Context failed: {err}")
                    error = err
                    st.exception(error)
                    st.stop()

                #######################################
                # Load files from the data/ directory #
                #######################################

                try:
                    save_dir = os.getcwd() + "/data"
                    documents = llama_index.load_documents(save_dir)
                    st.session_state["documents"] = documents
                    st.caption("✔️ Processed File Data")
                except Exception as err:
                    logs.log.error(f"Document Load Error: {err}")
                    error = err
                    st.exception(error)
                    st.stop()

                ###########################################
                # Create an index from ingested documents #
                ###########################################

                try:
                    llama_index.create_query_engine(
                        st.session_state["documents"],
                        st.session_state["service_context"],
                    )
                    st.caption("✔️ Created File Index")
                except Exception as err:
                    logs.log.error(f"Index Creation Error: {err}")
                    error = err
                    st.exception(error)
                    st.stop()

                #####################
                # Remove data files #
                #####################

                try:
                    save_dir = os.getcwd() + "/data"
                    shutil.rmtree(save_dir)
                    st.caption("✔️ Removed Temp Files")
                except Exception as err:
                    logs.log.error(f"Failed to delete data files: {err}")
                    error = err
                    st.exception(error)
                    st.stop()

                #####################
                # Show Final Status #
                #####################

                if error is not None:
                    st.exception(error)
                else:
                    st.write("Your files are ready. Let's chat! 😎")

    else:
        st.text_input(
            "Select a GitHub.com repo",
            placeholder="jonfairbanks/local-rag",
            disabled=True,
        )
        st.button(
            "Process Repo",
            disabled=True,
        )
