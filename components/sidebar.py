import streamlit as st

from components.tabs.about import about
from components.tabs.sources import sources
from components.tabs.settings import settings


def sidebar():
    with st.sidebar:
        tab1, tab2, tab3 = st.sidebar.tabs(["My Files", "Settings", "About"])

        with tab1:
            sources()

        with tab2:
            settings()

        with tab3:
            about()
