import streamlit as st

from components.tabs.about import about
from components.tabs.file_upload import file_upload
from components.tabs.github_repo import github_repo
from components.tabs.settings import settings


def sidebar():
    with st.sidebar:
        tab1, tab2, tab3 = st.sidebar.tabs(["My Files", "Settings", "About"])

        with tab1:
            file_upload()

        with tab2:
            settings()

        with tab3:
            about()
