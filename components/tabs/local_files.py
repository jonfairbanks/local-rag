import hashlib

import streamlit as st

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


def uploaded_files_signature(uploaded_files):
    """Return a stable signature for the current uploader contents."""
    return tuple(
        (
            uploaded_file.name,
            uploaded_file.size,
            uploaded_file.type,
            hashlib.sha256(uploaded_file.getvalue()).hexdigest(),
        )
        for uploaded_file in uploaded_files
    )


def should_process_uploads(current_signature, processed_signature, query_engine):
    """Return whether uploaded files need ingestion for the current app state."""
    return current_signature != processed_signature or query_engine is None


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
        current_upload_signature = uploaded_files_signature(uploaded_files)
        needs_processing = should_process_uploads(
            current_upload_signature,
            st.session_state["processed_file_signature"],
            st.session_state["query_engine"],
        )

        status_container = st.empty()

        if needs_processing:
            with st.spinner("Processing..."):
                # Initiate the RAG pipeline only for new file contents or missing index state.
                error = rag.rag_pipeline(uploaded_files, status_container=status_container)

                # Display errors (if any) or proceed
                if error is not None:
                    st.exception(error)
                else:
                    st.session_state["processed_file_signature"] = current_upload_signature
        else:
            rag.render_pipeline_status(
                status_container,
                st.session_state["file_ingestion_stages"],
            )

        if st.session_state["query_engine"] is not None:
            st.write("Your files are ready. Let's chat! 😎") # TODO: This should be a button.
