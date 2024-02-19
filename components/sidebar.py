import streamlit as st

from components.tabs.about import about
from components.tabs.file_upload import file_upload
from components.tabs.github_repo import github_repo
from components.tabs.settings import settings

def sidebar():
    with st.sidebar:
        tab1, tab2, tab3, tab4 = st.sidebar.tabs(
            [
                "File Upload", 
                "GitHub Repo", 
                "Settings", 
                "About"
            ]
        )

        with tab1:
            file_upload()

        with tab2:
            github_repo()

        with tab3:
            settings()

        with tab4:
            about()