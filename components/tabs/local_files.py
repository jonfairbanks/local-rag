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

    st.text_input(
        "Persisted Index ID",
        key="persisted_index_id",
        placeholder="local-rag-index",
        help="The unique identifier for the persisted index.",
    )
    st.caption(
        "Persisted indices are stored on disk and can be reloaded for future use. This is useful for retaining the index state across sessions."
    )

    if len(uploaded_files) > 0 or st.session_state["persisted_index_id"]:
        st.session_state["file_list"] = uploaded_files

        if len(uploaded_files) == 0:
            uploaded_files = None

        with st.spinner("Processing..."):
            # Initiate the RAG pipeline, providing documents to be saved on disk if necessary
            error = rag.rag_pipeline(uploaded_files)

            # Display errors (if any) or proceed
            if error is not None:
                st.exception(error)
            else:
                st.write("Your files are ready. Let's chat! 😎") # TODO: This should be a button.
