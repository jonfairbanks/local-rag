import streamlit as st

from components.tabs.local_files import local_files
from components.tabs.github_repo import github_repo


def file_upload():
    st.title("Directly import your files")
    st.caption("Convert your files to embeddings for utilization during chat")
    st.write("")

    with st.expander("💻 &nbsp; **Local Files**", expanded=False):
        local_files()

    with st.expander("🗂️ &nbsp;**GitHub Repo**", expanded=False):
        github_repo()
