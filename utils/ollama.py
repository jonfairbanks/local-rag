import ollama
import os

import streamlit as st

from utils.llama_index import create_chat_memory

# This is not used but required by llama-index and must be imported FIRST
os.environ["OPENAI_API_KEY"] = "sk-abc123"

from llama_index.llms.ollama import Ollama

###################################
#
# Create Client
#
###################################

def create_client(host: str):
    """
    Creates a client for interacting with the Ollama API.

    Parameters:
        host (str): The hostname or IP address of the Ollama server.

    Returns:
        ollama.Client: An instance of the Ollama client.
    """
    client = ollama.Client(host=host)
    return client

###################################
#
# Get Models
#
###################################

def get_models():
    """
    Retrieves a list of available language models from the Ollama server.

    Returns:
        list: A list of available language model names.
    """
    chat_client = create_client(st.session_state.ollama_endpoint)
    data = chat_client.list()
    models = []
    for model in data['models']:
        models.append(model['name'])
    st.session_state.ollama_models = models
    return models

###################################
#
# Create Ollama LLM instance
#
###################################

def create_ollama_llm(model: str, base_url: str, request_timeout: int = 60) -> Ollama:
    """
    Create an instance of the Ollama language model.

    Parameters:
        model (str): The name of the model to use for language processing.
        base_url (str): The base URL for making API requests.
        request_timeout (int, optional): The timeout for API requests in seconds. Defaults to 60.

    Returns:
        Ollama: An instance of the Ollama language model with the specified configuration.
    """
    try:
        llm = Ollama(
            model=model,
            base_url=base_url,
            request_timeout=request_timeout
        )
    except Exception as e:
        print(f"Error creating Ollama language model: {e}")
        return None
    else:
        return llm

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

    try:
        llm = create_ollama_llm()
        stream = llm.stream_complete(prompt)
        for chunk in stream:
            yield chunk.delta
    except Exception as err:
        print(f"Ollama chat stream error: {err}")
        return

###################################
#
# Document Chat (with context)
#
###################################

def context_chat(
    prompt: str,
    index: str
):
    """
    Initiates a chat with context using the Ollama language model and index.

    Parameters:
        prompt (str): The starting prompt for the conversation.
        model (str): The name of the language model to use for the chat.
        base_url (str): The base URL of the Ollama API.
        index (str): The index used for context in the conversation.
        request_timeout (int, optional): Timeout for API requests in seconds. Defaults to 60.

    Yields:
        str: Successive chunks of conversation from the Ollama model with context.

    Returns:
        None: If an exception occurs during the chat stream, prints the error and returns None.
    """

    chat_engine = index.as_chat_engine(
        llm=create_ollama_llm(),
        memory=create_chat_memory(),
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
        return

