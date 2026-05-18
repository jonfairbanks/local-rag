import streamlit as st

import utils.helpers as func
import utils.rag_pipeline as rag
from components.ingestion_prerequisites import (
    ingestion_is_configured,
)

GITHUB_DOCUMENTS_LOADED_STAGE = "Repository Files Loaded"


def should_show_github_ingestion_status(
    current_repo, processed_repo, ingestion_stages, query_engine
):
    """Return whether saved GitHub ingestion status should be shown on rerun."""
    try:
        normalized_current_repo = func.normalize_github_repo(current_repo)
    except ValueError:
        return False

    return (
        normalized_current_repo == processed_repo
        and len(ingestion_stages) > 0
        and query_engine is not None
    )


def github_repo():
    # st.header("Import files from a GitHub repo")
    # st.caption("Convert a GitHub repo to embeddings for utilization during chat")
    if ingestion_is_configured():
        with st.form("github_repo_form"):
            st.text_input(
                "Select a GitHub.com repo",
                placeholder="jonfairbanks/local-rag",
                key="github_repo",
            )
            repo_processed = st.form_submit_button("Process")

        if repo_processed:
            status_container = st.empty()
            completed_stages = []

            with st.spinner("Processing..."):
                try:
                    repo = func.normalize_github_repo(st.session_state["github_repo"])
                except ValueError as err:
                    st.error(str(err))
                    st.stop()

                rag.render_pipeline_status(
                    status_container, completed_stages, "Validating Repository"
                )
                if not func.validate_github_repo(repo):
                    st.error(
                        "That GitHub repository could not be validated. Use `owner/repo` or a GitHub URL and ensure it exists."
                    )
                    st.stop()
                completed_stages.append("Repository Validated")
                rag.render_pipeline_status(status_container, completed_stages)

                rag.render_pipeline_status(
                    status_container, completed_stages, "Cloning Repository"
                )
                cloned_repo_dir = func.clone_github_repo(repo)
                if not cloned_repo_dir:
                    st.error("Failed to clone repository. Check the repo value and logs.")
                    st.stop()
                completed_stages.append("Repository Cloned")
                rag.render_pipeline_status(status_container, completed_stages)

                error = rag.rag_pipeline(
                    data_dir=cloned_repo_dir,
                    status_container=status_container,
                    initial_stages=completed_stages,
                    status_state_key="github_ingestion_stages",
                    documents_loaded_stage=GITHUB_DOCUMENTS_LOADED_STAGE,
                )
                if error is not None:
                    st.exception(error)
                else:
                    st.session_state["processed_github_repo"] = repo
                    st.write("Your files are ready. Let's chat! 😎") # TODO: This should be a button.
        elif should_show_github_ingestion_status(
            st.session_state["github_repo"],
            st.session_state["processed_github_repo"],
            st.session_state["github_ingestion_stages"],
            st.session_state["query_engine"],
        ):
            status_container = st.empty()
            rag.render_pipeline_status(
                status_container,
                st.session_state["github_ingestion_stages"],
            )
            st.write("Your files are ready. Let's chat! 😎") # TODO: This should be a button.

    else:
        st.text_input(
            "Select a GitHub.com repo",
            placeholder="jonfairbanks/local-rag",
            key="github_repo_disabled",
            disabled=True,
        )
        st.button(
            "Process Repo",
            disabled=True,
        )
