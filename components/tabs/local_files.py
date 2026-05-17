import hashlib

import streamlit as st

import utils.rag_pipeline as rag
import utils.helpers as func
from components.ingestion_prerequisites import (
    ingestion_is_configured,
)

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


def _bytes_to_mb(size_in_bytes):
    return size_in_bytes // (1024 * 1024)


def upload_limit_help_text():
    return (
        f"Up to {func.MAX_UPLOAD_FILES} files. "
        f"{_bytes_to_mb(func.MAX_UPLOAD_FILE_BYTES)}MB per file, "
        f"{_bytes_to_mb(func.MAX_TOTAL_UPLOAD_BYTES)}MB total."
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
    if ingestion_is_configured():
        uploaded_files = st.file_uploader(
            "Select Files",
            accept_multiple_files=True,
            type=supported_files,
            help=upload_limit_help_text(),
        )
    else:
        file_upload_container = st.container(border=True)
        with file_upload_container:
            uploaded_files = st.file_uploader(
                "Select Files",
                accept_multiple_files=True,
                type=supported_files,
                disabled=True,
                help=upload_limit_help_text(),
            )

    if len(uploaded_files) > 0:
        try:
            func.validate_uploaded_files(uploaded_files)
        except ValueError as err:
            st.error(str(err))
            st.stop()

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
                error = rag.rag_pipeline(
                    uploaded_files, status_container=status_container
                )

                # Display errors (if any) or proceed
                if error is not None:
                    st.exception(error)
                else:
                    st.session_state["processed_file_signature"] = (
                        current_upload_signature
                    )
        else:
            rag.render_pipeline_status(
                status_container,
                st.session_state["file_ingestion_stages"],
            )

        if st.session_state["query_engine"] is not None:
            st.write(
                "Your files are ready. Let's chat! 😎"
            )  # TODO: This should be a button.
