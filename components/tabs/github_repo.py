import streamlit as st

import utils.helpers as func
import utils.rag_pipeline as rag


def github_repo():
    # st.header("Import files from a GitHub repo")
    # st.caption("Convert a GitHub repo to embeddings for utilization during chat")
    if st.session_state["selected_model"] is not None:
        st.text_input(
            "Select a GitHub.com repo",
            placeholder="jonfairbanks/local-rag",
            key="github_repo",
        )

        repo_processed = st.button("Process", key="process_github")

        if repo_processed:
            with st.spinner("Processing..."):
                repo = st.session_state["github_repo"]
                if not func.validate_github_repo(repo):
                    st.error(
                        "That GitHub repository could not be validated. Use the format `owner/repo` and ensure it exists."
                    )
                    st.stop()

                clone_ok = func.clone_github_repo(repo)
                if not clone_ok:
                    st.error("Failed to clone repository. Check the repo value and logs.")
                    st.stop()

                error = rag.rag_pipeline()
                if error is not None:
                    st.exception(error)
                else:
                    st.write("Your files are ready. Let's chat! 😎") # TODO: This should be a button.

    else:
        st.text_input(
            "Select a GitHub.com repo",
            placeholder="jonfairbanks/local-rag",
            disabled=True,
        )
        st.button(
            "Process Repo",
            disabled=True,
        )
