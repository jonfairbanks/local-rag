import streamlit as st

def set_page_config():
    st.set_page_config(
        page_title='Local RAG',
        page_icon='📚',
        layout='wide',
        initial_sidebar_state='expanded'
    )