import ollama
import os

import streamlit as st

import utils.logs as logs

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
        - host (str): The hostname or IP address of the Ollama server.

    Returns:
        - ollama.Client: An instance of the Ollama client.
    """
    client = ollama.Client(host=host)
    return client


###################################
#
# Get Models
#
###################################


@st.cache_data(show_spinner=False)
def get_models():
    """
    Retrieves a list of available language models from the Ollama server.

    Returns:
        - models: A list of available language model names.
    """
    chat_client = create_client(st.session_state["ollama_endpoint"])
    data = chat_client.list()
    models = []
    for model in data["models"]:
        models.append(model["name"])
    st.session_state["ollama_models"] = models
    return models


###################################
#
# Create Ollama LLM instance
#
###################################


@st.cache_data(show_spinner=False)
def create_ollama_llm(model: str, base_url: str, request_timeout: int = 60) -> Ollama:
    """
    Create an instance of the Ollama language model.

    Parameters:
        - model (str): The name of the model to use for language processing.
        - base_url (str): The base URL for making API requests.
        - request_timeout (int, optional): The timeout for API requests in seconds. Defaults to 60.

    Returns:
        - llm: An instance of the Ollama language model with the specified configuration.
    """
    try:
        llm = Ollama(model=model, base_url=base_url, request_timeout=request_timeout)
        return llm
    except Exception as e:
        logs.log.error(f"Error creating Ollama language model: {e}")
        return None


###################################
#
# Chat (no context)
#
###################################


def chat(prompt: str):
    """
    Initiates a chat with the Ollama language model using the provided parameters.

    Parameters:
        - prompt (str): The starting prompt for the conversation.

    Yields:
        - str: Successive chunks of conversation from the Ollama model.
    """

    try:
        llm = create_ollama_llm()
        stream = llm.stream_complete(prompt)
        for chunk in stream:
            yield chunk.delta
    except Exception as err:
        logs.log.error(f"Ollama chat stream error: {err}")
        return


###################################
#
# Document Chat (with context)
#
###################################


def context_chat(prompt: str, query_engine):
    """
    Initiates a chat with context using the Ollama language model and index.

    Parameters:
        - prompt (str): The starting prompt for the conversation.
        - query_engine (str): TODO: Write this section

    Yields:
        - str: Successive chunks of conversation from the Ollama model with context.
    """

    # print(type(query_engine)) # <class 'llama_index.core.query_engine.retriever_query_engine.RetrieverQueryEngine'>

    try:
        stream = query_engine.query(prompt)
        for text in stream.response_gen:
            yield text
    except Exception as err:
        logs.log.error(f"Ollama chat stream error: {err}")
        return
