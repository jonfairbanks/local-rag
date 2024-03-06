import os
import shutil

import streamlit as st

import utils.helpers as func
import utils.ollama as ollama
import utils.llama_index as llama_index
import utils.logs as logs
import utils.rag_pipeline as rag

supported_files = (
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
)


def local_files():
    # Force users to confirm Settings before uploading files
    if st.session_state["selected_model"] is not None:
        uploaded_files = st.file_uploader(
            "Select Files",
            accept_multiple_files=True,
            type=supported_files,
        )
    else:
        st.warning("Please configure Ollama settings before proceeding!", icon="⚠️")
        file_upload_container = st.container(border=True)
        with file_upload_container:
            uploaded_files = st.file_uploader(
                "Select Files",
                accept_multiple_files=True,
                type=supported_files,
                disabled=True,
            )

    if len(uploaded_files) > 0:
        st.session_state["file_list"] = uploaded_files

        with st.spinner("Processing..."):
            # Initiate the RAG pipeline, providing documents to be saved on disk if necessary
            error = rag.rag_pipeline(uploaded_files)

            # Display errors (if any) or proceed
            if error is not None:
                st.exception(error)
            else:
                st.write("Your files are ready. Let's chat! 😎")
