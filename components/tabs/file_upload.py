import os

import streamlit as st

import utils.helpers as func
import utils.ollama as ollama
import utils.llama_index as llama_index

def file_upload():
    st.title("Directly import local files")
    st.caption(
        "Convert your local files to embeddings for utilization during chat"
    )
    st.write("")

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
        )
    )
    if len(uploaded_files) > 0:
        st.session_state["file_list"] = uploaded_files

        with st.status("Preparing your data...", expanded=True) as status:
            error = None
            st.caption("Uploading Files Locally")
            # Save the files to disk
            for uploaded_file in uploaded_files:
                with st.spinner(f"Processing {uploaded_file.name}..."):
                    save_dir = os.getcwd() + "/data"
                    func.save_uploaded_file(uploaded_file, save_dir)

            st.caption("Loading Embedding Model")
            # Create llama-index service-context to use local LLMs and embeddings
            try:
                llm = ollama.create_ollama_llm(
                    st.session_state.selected_model,
                    st.session_state.ollama_endpoint,
                )
                service_context = llama_index.create_service_context(llm)
            except Exception as err:
                print(f"Setting up Service Context failed: {err}")
                error = err

            st.caption("Processing File Data")
            try:
                documents = llama_index.load_documents(
                    save_dir
                )
                st.session_state.documents = documents
            except Exception as err:
                print(f"Document Load Error: {err}")
                error = err

            st.caption("Creating File Index")
            try:
                index = llama_index.create_query_engine(
                    documents, service_context
                )
                print(f"Index: {index}")
                query_engine = index.as_query_engine(
                    similarity_top_k = 5,  # Returns additional results; TODO: Set via UI?
                    service_context=service_context,
                )
                print(query_engine)
                st.session_state["query_engine"] = query_engine
            except Exception as err:
                print(f"Index Creation Error: {err}")
                error = err

            if error is not None:
                status.update(
                    label="File processing failed.",
                    state="error",
                    expanded=True,
                )
                st.error(error)
            else:
                status.update(
                    label="Your files are ready. Let's chat!",
                    state="complete",
                    expanded=False,
                )

    # st.caption(
    #     "Although any uploads are supported, you will get the best results with: _csv, docx, epub, ipynb, md, pdf, ppt, pptx_"
    # )