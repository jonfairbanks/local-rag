import streamlit as st

import utils.helpers as func


def github_repo():
    st.header("Import files from a GitHub repo")
    st.caption("Convert a GitHub repo to embeddings for utilization during chat")

    github_container = st.container(border=True)
    with github_container:
        st.text_input(
            "GitHub repo",
            placeholder="jonfairbanks/local-rag",
            key="github_repo",
            value=st.session_state.github_repo,
            on_change=func.process_github_repo,
            args=(st.session_state.github_repo,),
        )
        st.button(
            "Process Repo",
            on_click=func.process_github_repo,
            args=(st.session_state.github_repo,),
            disabled=True,
        )
