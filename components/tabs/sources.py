import streamlit as st

from components.tabs.local_files import local_files
from components.tabs.github_repo import github_repo
from components.tabs.website import website
from components.ingestion_prerequisites import (
    ingestion_is_configured,
    render_ingestion_settings_warning,
)


def sources():
    st.title("Directly import your data")
    st.caption("Convert your data into embeddings for utilization during chat")
    st.write("")

    if not ingestion_is_configured():
        render_ingestion_settings_warning()
        st.write("")

    with st.expander("💻 &nbsp; **Local Files**", expanded=False):
        local_files()

    with st.expander("🗂️ &nbsp;**GitHub Repo**", expanded=False):
        github_repo()

    with st.expander("🌐 &nbsp; **Website**", expanded=False):
        website()
