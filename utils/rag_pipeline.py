import os
import shutil

import streamlit as st

import utils.helpers as func
import utils.ollama as ollama
import utils.llama_index as llama_index
import utils.logs as logs

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
            If none are provided, the function will load files from the current working directory.

    Yields:
        - str: Successive chunks of conversation from the Ollama model with context.

    Raises:
        - Exception: If there is an error retrieving answers from the Ollama model or creating the service context.

    Notes:
        This function initiates a chat with context using the Llama-Index library and the Ollama language model. It takes one optional parameter, `uploaded_files`, which should be a list of files to be processed. If no files are provided, the function will load files from the current working directory. The function returns an iterable yielding successive chunks of conversation from the Ollama model with context. If there is an error retrieving answers from the Ollama model or creating the service context, the function raises an exception.

    Context:
        - logs.log: A logger for logging events related to this function.

    Side Effects:
        - Creates a service context using the provided Ollama model and embedding file.
        - Loads documents from the current working directory or the provided list of files.
        - Removes the loaded documents and any temporary files created during processing.
    """
    error = None
    completed_stages = list(initial_stages or [])
    render_pipeline_status(status_container, completed_stages)

    save_dir = os.path.join(os.getcwd(), "data")
    ingest_dir = data_dir or save_dir

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
    elif embedding_model is None or embedding_model == "Default (gte-modernbert-base)":
        selected_embedding_model = "Alibaba-NLP/gte-modernbert-base"
    elif embedding_model == "Higher Quality (Qwen3-Embedding-0.6B)":
        selected_embedding_model = "Qwen/Qwen3-Embedding-0.6B"
    elif embedding_model == "Other":
        selected_embedding_model = st.session_state["other_embedding_model"]
    else:
        raise ValueError(f"Unsupported embedding model selection: {embedding_model}")

    try:
        chunk_size = int(st.session_state["chunk_size"])
        chunk_overlap = int(st.session_state["chunk_overlap"])
        if chunk_size <= 0:
            raise ValueError("Chunk Size must be > 0")
        if chunk_overlap < 0:
            raise ValueError("Chunk Overlap must be >= 0")
        if chunk_overlap >= chunk_size:
            raise ValueError("Chunk Overlap must be less than Chunk Size")

        llama_index.setup_embedding_model(
            selected_embedding_model,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            backend=embedding_backend,
            ollama_endpoint=st.session_state["ollama_endpoint"],
        )
        completed_stages.append("Embedding Model Ready")
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
            render_pipeline_status(status_container, completed_stages)
        else:
            if uploaded_files is not None:
                for uploaded_file in uploaded_files:
                    with st.spinner(f"Processing {uploaded_file.name}..."):
                        func.save_uploaded_file(uploaded_file, save_dir)
                completed_stages.append("Files Uploaded")
                render_pipeline_status(status_container, completed_stages)

            ingested_documents = llama_index.load_documents(ingest_dir)
            if len(ingested_documents) == 0:
                raise ValueError("No files were found to process.")
            validate_ingested_documents(ingested_documents)
            st.session_state["documents"] = ingested_documents
            completed_stages.append(documents_loaded_stage)
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
            progress_callback=update_embedding_progress,
        )
        completed_stages.append("Embeddings Generated")
        completed_stages.append("Index Ready")
        st.session_state[status_state_key] = list(completed_stages)
        render_completed_ingestion_status(status_container, completed_stages)
    except Exception as err:
        logs.log.error(f"Index Creation Error: {str(err)}")
        error = err
        st.exception(error)
        st.stop()

    # Remove transient on-disk ingestion files (uploads/clones) after indexing.
    if os.path.isdir(save_dir):
        try:
            shutil.rmtree(save_dir)
        except Exception as err:
            logs.log.warning(
                f"Unable to delete data files, you may want to clean-up manually: {str(err)}"
            )

    return error  # If no errors occurred, None is returned
