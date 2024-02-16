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
# Chat (no context)
#
###################################

def chat(prompt: str, model: str, base_url: str, request_timeout: int = 60):
    """
    Initiates a chat with the Ollama language model using the provided parameters.

    Parameters:
        prompt (str): The starting prompt for the conversation.
        model (str): The name of the language model to use for the chat.
        base_url (str): The base URL of the Ollama API.
        request_timeout (int, optional): Timeout for API requests in seconds. Defaults to 60.

    Yields:
        str: Successive chunks of conversation from the Ollama model.

    Returns:
        None: If an exception occurs during the chat stream, prints the error and returns None.
    """
    llm = Ollama(
        model=model,
        base_url=base_url,
        request_timeout=request_timeout
    )

    try:
        stream = llm.stream_complete(prompt)
        for chunk in stream:
            yield chunk.delta
    except Exception as err:
        print(f"Ollama chat stream error: {err}")
        return None

###################################
#
# Document Chat (with context)
#
###################################

def context_chat(
    prompt: str, 
    model: str,
    base_url: str,
    index: str,
    request_timeout: int = 60
):
    llm = Ollama(
        model=model,
        base_url=base_url,
        request_timeout=request_timeout
    )

    chat_engine = index.as_chat_engine(
        llm=llm,
        memory=memory,
        chat_mode="context", # Might need changed
        system_prompt=(
            "You are a chatbot, able to have normal interactions, as well as talk"
            " about an essay discussing Paul Grahams life."
        )
    )

    try:
        stream = chat_engine.stream_chat(prompt)
        for chunk in stream:
            yield chunk.delta
    except Exception as err:
        print(f"Ollama chat stream error: {err}")
        return None