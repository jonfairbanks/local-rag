import streamlit as st

from components.chatbox import chatbox
from components.header import set_page_header
from components.sidebar import sidebar

from components.page_config import set_page_config
from components.page_state import setup_initial_state

### Page Setup
set_page_config()
set_page_header()

### Setup Initial State
setup_initial_state()

for msg in st.session_state['messages']:
    st.chat_message(msg["role"]).write(msg["content"])

### Sidebar
sidebar()

### Chat Box
chatbox()