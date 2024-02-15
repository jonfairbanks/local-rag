import ollama
import os

import streamlit as st

# This is not used but required by llama-index and must be imported FIRST
os.environ["OPENAI_API_KEY"] = "sk-abc123"

from llama_index.llms.ollama import Ollama

###################################
#
# Create Client
#
###################################

def create_client(host: str):
    client = ollama.Client(host=host)
    return client

###################################
#
# Get Models
#
###################################

def get_models():
    chat_client = create_client(st.session_state.ollama_endpoint)
    data = chat_client.list()
    models = []
    for model in data['models']:
        models.append(model['name'])
    st.session_state.ollama_models = models
    return models

###################################
#
# Chat Stream 
#
###################################

def stream_chat(prompt: str):
    llm = Ollama(
        model=st.session_state.selected_model,
        base_url=st.session_state.ollama_endpoint,
        request_timeout=60.0
    )

    stream = llm.stream_complete(prompt)

    for r in stream:
        print(r.delta, end="")

    return stream