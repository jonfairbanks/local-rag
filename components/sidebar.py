import streamlit as st

import tabs.about as about
import tabs.file_upload as file_upload
import tabs.github_repo as github_repo
import tabs.settings as settings

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