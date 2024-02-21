import os

import streamlit as st

import utils.helpers as func
import utils.ollama as ollama
import utils.llama_index as llama_index


def file_upload():
    st.title("Directly import your files")
    st.caption("Convert your files to embeddings for utilization during chat")
    st.write("")

    if st.session_state["selected_model"] is not None:
        uploaded_files = st.file_uploader(
            "Select Files",
            accept_multiple_files=True,
            type=("csv", "docx", "epub", "ipynb", "json", "md", "pdf", "ppt", "pptx",),
        )
    else:
        st.warning("Please configure Ollama settings before proceeding!", icon="⚠️")
        uploaded_files = st.file_uploader(
            "Select Files",
            accept_multiple_files=True,
            type=("csv", "docx", "epub", "ipynb", "json", "md", "pdf", "ppt", "pptx",),
            disabled=True,
        )

    if len(uploaded_files) > 0:
        st.session_state["file_list"] = uploaded_files

        with st.status("Preparing your data...", expanded=True) as status:
            error = None

            ######################
            # Save Files to Disk #
            ######################

            st.caption("Uploading Files Locally")
            for uploaded_file in uploaded_files:
                with st.spinner(f"Processing {uploaded_file.name}..."):
                    save_dir = os.getcwd() + "/data"
                    func.save_uploaded_file(uploaded_file, save_dir)

            st.caption("Loading Embedding Model")

            ######################################
            # Create Llama-Index service-context #
            # to use local LLMs and embeddings   #
            ######################################

            try:
                llm = ollama.create_ollama_llm(
                    st.session_state["selected_model"],
                    st.session_state["ollama_endpoint"],
                )
                # resp = llm.complete("Hello!")
                # print(resp)
                service_context = llama_index.create_service_context(llm)
            except Exception as err:
                print(f"Setting up Service Context failed: {err}")
                error = err

            #######################################
            # Load files from the data/ directory #
            #######################################

            st.caption("Processing File Data")
            try:
                documents = llama_index.load_documents(save_dir)
                st.session_state["documents"] = documents
            except Exception as err:
                print(f"Document Load Error: {err}")
                error = err

            ###########################################
            # Create an index from ingested documents #
            ###########################################

            st.caption("Creating File Index")
            try:
                llama_index.create_query_engine(documents, service_context)
            except Exception as err:
                print(f"Index Creation Error: {err}")
                error = err

            #####################
            # Show Final Status #
            #####################

            if error is not None:
                status.update(
                    label="File processing failed.", state="error", expanded=True,
                )
                st.error(error)
            else:
                status.update(
                    label="Your files are ready. Let's chat!",
                    state="complete",
                    expanded=False,
                )

    with st.expander("GitHub Repo", expanded=False):
        st.write(":grey[Coming Soon&trade;]")