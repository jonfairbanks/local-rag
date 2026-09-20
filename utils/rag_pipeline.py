from tempfile import TemporaryDirectory

import streamlit as st

import utils.helpers as func
import utils.ollama as ollama
import utils.llama_index as llama_index
import utils.logs as logs
from utils.settings_validation import HF_MODELS, validate_chunk_settings

MAX_INGESTED_DOCUMENTS = 1000
MAX_INGESTED_TEXT_CHARS = 10 * 1024 * 1024


def _document_text(document):
    if hasattr(document, "get_content"):
        return document.get_content() or ""
    if hasattr(document, "text"):
        return document.text or ""
    return str(document)


def validate_ingested_documents(documents):
    if len(documents) > MAX_INGESTED_DOCUMENTS:
        raise ValueError(
            f"Too many documents were loaded. Limit: {MAX_INGESTED_DOCUMENTS}."
        )

    total_chars = sum(len(_document_text(document)) for document in documents)
    if total_chars > MAX_INGESTED_TEXT_CHARS:
        raise ValueError("Loaded documents exceed the ingestion text limit.")


def render_pipeline_status(status_container, completed_stages, active_stage=None):
    """Render truthful ingestion progress for the currently running pipeline."""
    if status_container is None:
        return

    status_container.empty()
    with status_container.container():
        for stage in completed_stages:
            st.caption(f"✔️ {stage}")
        if active_stage is not None:
            st.caption(f"⏳ {active_stage}")


def render_embedding_progress(status_container, completed_stages, completed, total):
    """Render exact embedding progress for the active indexing stage."""
    if status_container is None:
        return

    progress = 0 if total == 0 else min(completed / total, 1)
    progress_label = f"Generating Embeddings — {progress:.0%}"

    status_container.empty()
    with status_container.container():
        for stage in completed_stages:
            st.caption(f"✔️ {stage}")
        st.caption("⏳ Generating Embeddings")
        st.progress(progress, text=progress_label)
        st.caption(f"{completed:,} / {total:,} chunks embedded")


def render_completed_ingestion_status(status_container, completed_stages):
    """Render final ingestion status without leaving stale progress widgets behind."""
    if status_container is None:
        return

    status_container.empty()
    with status_container.container():
        for stage in completed_stages:
            st.caption(f"✔️ {stage}")
        # Replace the old progress-bar slots from the active embedding render.
        # Streamlit can otherwise leave stale child elements visible for this
        # run when the final render has fewer elements than the progress render.
        st.empty()
        st.empty()


def rag_pipeline(
    uploaded_files=None, documents=None, data_dir=None, **kwargs
):
    """Keep ingestion state and temporary uploads private to this operation."""
    st.session_state["query_engine"] = None
    st.session_state["documents"] = None
    st.session_state["llm"] = None
    completed = False
    try:
        if uploaded_files is not None:
            func.validate_uploaded_files(uploaded_files)
            if documents is not None or data_dir is not None:
                raise ValueError("Select one ingestion source at a time.")
            with TemporaryDirectory(prefix="local-rag-upload-") as upload_dir:
                result = _rag_pipeline(uploaded_files=uploaded_files, data_dir=upload_dir, **kwargs)
        else:
            if documents is None and data_dir is None:
                raise ValueError("An ingestion source is required.")
            result = _rag_pipeline(documents=documents, data_dir=data_dir, **kwargs)
        completed = True
        return result
    finally:
        if not completed:
            st.session_state["query_engine"] = None
            st.session_state["documents"] = None
            st.session_state["llm"] = None


def _rag_pipeline(
    uploaded_files: list = None,
    documents: list = None,
    data_dir: str | None = None,
    status_container=None,
    initial_stages: list[str] | None = None,
    status_state_key: str = "file_ingestion_stages",
    documents_loaded_stage: str = "Documents Loaded",
):
    """
    RAG pipeline for Llama-based chatbots.

    Parameters:
        - uploaded_files (list, optional): List of files to be processed.
            Files are staged in a private temporary directory by the caller.

    Yields:
        - str: Successive chunks of conversation from the Ollama model with context.

    Raises:
        - Exception: If there is an error retrieving answers from the Ollama model or creating the service context.

    Notes:
        Loads the explicitly supplied directory or documents and builds a session-local query engine.

    Context:
        - logs.log: A logger for logging events related to this function.

    Side Effects:
        - Creates a service context using the provided Ollama model and embedding file.
        - Loads documents from the supplied source.
        - The caller owns cleanup of temporary upload or clone directories.
    """
    error = None
    completed_stages = list(initial_stages or [])

    def record_completed_stages():
        st.session_state[status_state_key] = list(completed_stages)

    render_pipeline_status(status_container, completed_stages)

    ingest_dir = data_dir

    ######################################
    # Create Llama-Index service-context #
    # to use local LLMs and embeddings   #
    ######################################

    try:
        llm = ollama.create_ollama_llm(
            st.session_state["selected_model"],
            st.session_state["ollama_endpoint"],
            st.session_state["system_prompt"],
        )
        st.session_state["llm"] = llm
        completed_stages.append("LLM Initialized")
        record_completed_stages()
        render_pipeline_status(status_container, completed_stages)

        # resp = llm.complete("Hello!")
        # print(resp)
    except Exception as err:
        logs.log.error(f"Failed to setup LLM: {str(err)}")
        error = err
        st.exception(error)
        st.stop()

    ####################################
    # Determine embedding model to use #
    ####################################

    embedding_backend = st.session_state["embedding_backend"]
    embedding_model = st.session_state["embedding_model"]

    if embedding_backend == "Ollama":
        selected_embedding_model = st.session_state["ollama_embedding_model"]
    elif embedding_model in HF_MODELS:
        selected_embedding_model = HF_MODELS[embedding_model]
    else:
        raise ValueError(f"Unsupported embedding model selection: {embedding_model}")

    try:
        chunk_size, chunk_overlap = validate_chunk_settings(
            st.session_state["chunk_size"], st.session_state["chunk_overlap"]
        )
        embed_model = llama_index.setup_embedding_model(
            selected_embedding_model,
            backend=embedding_backend,
            ollama_endpoint=st.session_state["ollama_endpoint"],
        )
        completed_stages.append("Embedding Model Ready")
        record_completed_stages()
        render_pipeline_status(status_container, completed_stages)
    except Exception as err:
        logs.log.error(f"Setting up Embedding Model failed: {str(err)}")
        error = err
        st.exception(error)
        st.stop()

    try:
        # Always reset the query engine before ingesting fresh source content.
        st.session_state["query_engine"] = None

        if documents is not None:
            if len(documents) == 0:
                raise ValueError("No documents were loaded from the selected source.")
            validate_ingested_documents(documents)
            st.session_state["documents"] = documents
            completed_stages.append(documents_loaded_stage)
            record_completed_stages()
            render_pipeline_status(status_container, completed_stages)
        else:
            if uploaded_files is not None:
                for uploaded_file in uploaded_files:
                    with st.spinner(f"Processing {uploaded_file.name}..."):
                        func.save_uploaded_file(uploaded_file, ingest_dir)
                completed_stages.append("Files Uploaded")
                record_completed_stages()
                render_pipeline_status(status_container, completed_stages)

            ingested_documents = llama_index.load_documents(ingest_dir)
            if len(ingested_documents) == 0:
                raise ValueError("No files were found to process.")
            validate_ingested_documents(ingested_documents)
            st.session_state["documents"] = ingested_documents
            completed_stages.append(documents_loaded_stage)
            record_completed_stages()
            render_pipeline_status(status_container, completed_stages)
    except Exception as err:
        logs.log.error(f"Document Load Error: {str(err)}")
        error = err
        st.exception(error)
        st.stop()

    ###########################################
    # Create an index from ingested documents #
    ###########################################

    try:

        def update_embedding_progress(completed, total):
            if total is None or total == 0:
                render_pipeline_status(
                    status_container, completed_stages, "Generating Embeddings"
                )
                return
            render_embedding_progress(
                status_container, completed_stages, completed, total
            )

        render_pipeline_status(
            status_container, completed_stages, "Generating Embeddings"
        )
        llama_index.create_query_engine(
            st.session_state["documents"],
            llm=llm,
            embed_model=embed_model,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            progress_callback=update_embedding_progress,
        )
        completed_stages.append("Embeddings Generated")
        completed_stages.append("Index Ready")
        record_completed_stages()
        render_completed_ingestion_status(status_container, completed_stages)
    except Exception as err:
        logs.log.error(f"Index Creation Error: {str(err)}")
        error = err
        st.exception(error)
        st.stop()

    return error  # If no errors occurred, None is returned
