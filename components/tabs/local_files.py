import os
import shutil

import streamlit as st

import utils.helpers as func
import utils.ollama as ollama
import utils.llama_index as llama_index
import utils.logs as logs


def local_files():
    # Force users to confirm Settings before uploading files
    if st.session_state["selected_model"] is not None:
        uploaded_files = st.file_uploader(
            "Select Files",
            accept_multiple_files=True,
            type=(
                "csv",
                "docx",
                "epub",
                "ipynb",
                "json",
                "md",
                "pdf",
                "ppt",
                "pptx",
                "txt",
            ),
        )
    else:
        st.warning("Please configure Ollama settings before proceeding!", icon="⚠️")
        file_upload_container = st.container(border=True)
        with file_upload_container:
            uploaded_files = st.file_uploader(
                "Select Files",
                accept_multiple_files=True,
                type=(
                    "csv",
                    "docx",
                    "epub",
                    "ipynb",
                    "json",
                    "md",
                    "pdf",
                    "ppt",
                    "pptx",
                    "txt"
                ),
                disabled=True,
            )

    if len(uploaded_files) > 0:
        st.session_state["file_list"] = uploaded_files

        with st.spinner("Processing..."):
            error = None

            ######################
            # Save Files to Disk #
            ######################

            for uploaded_file in uploaded_files:
                with st.spinner(f"Processing {uploaded_file.name}..."):
                    save_dir = os.getcwd() + "/data"
                    func.save_uploaded_file(uploaded_file, save_dir)

            st.caption("✔️ Files Uploaded")

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

                # Determine embedding model to use

                embedding_model = st.session_state["embedding_model"]
                hf_embedding_model = None

                if embedding_model == None:
                    # logs.log.info("No embedding model set; using defaults...")
                    hf_embedding_model = "BAAI/bge-large-en-v1.5"

                if embedding_model == "Default (bge-large-en-v1.5)":
                    # logs.log.info("Using default embedding model...")
                    hf_embedding_model = "BAAI/bge-large-en-v1.5"

                if embedding_model == "Large (Salesforce/SFR-Embedding-Mistral)":
                    # logs.log.info("Using the Salesforce embedding model; RIP yer VRAM...")
                    hf_embedding_model = "Salesforce/SFR-Embedding-Mistral"

                if embedding_model == "Other":
                    # logs.log.info("Using a user-provided embedding model...")
                    hf_embedding_model = st.session_state["other_embedding_model"]

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

            #######################################
            # Load files from the data/ directory #
            #######################################

            try:
                documents = llama_index.load_documents(save_dir)
                st.session_state["documents"] = documents
                st.caption("✔️ Processed File Data")
            except Exception as err:
                logs.log.error(f"Document Load Error: {err}")
                error = err

            ###########################################
            # Create an index from ingested documents #
            ###########################################

            try:
                llama_index.create_query_engine(
                    st.session_state["documents"], st.session_state["service_context"]
                )
                st.caption("✔️ Created File Index")
            except Exception as err:
                logs.log.error(f"Index Creation Error: {err}")
                error = err

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

            #####################
            # Show Final Status #
            #####################

            if error is not None:
                st.exception(error)
            else:
                st.write("Your files are ready. Let's chat! 😎")
