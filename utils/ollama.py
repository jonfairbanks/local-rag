import ollama
import os

import streamlit as st

import utils.logs as logs

# This is not used but required by llama-index and must be imported FIRST
os.environ["OPENAI_API_KEY"] = "sk-abc123"

from llama_index.llms.ollama import Ollama
from llama_index.core import Settings
from llama_index.core.query_engine.retriever_query_engine import RetrieverQueryEngine

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
        - An instance of the Ollama client.

    Raises:
        - Exception: If there is an error creating the client.

    Notes:
        This function creates a client for interacting with the Ollama API using the `ollama` library. It takes a single parameter, `host`, which should be the hostname or IP address of the Ollama server. The function returns an instance of the Ollama client, or raises an exception if there is an error creating the client.
    """
    try:
        client = ollama.Client(host=host)
        logs.log.info("Ollama chat client created successfully")
        return client
    except Exception as err:
        logs.log.error(f"Failed to create Ollama client: {err}")
        return False


###################################
#
# Get Models
#
###################################


def _get_installed_model_names(chat_client):
    data = chat_client.list()
    models = []
    for model in data["models"]:
        try:
            model_name = model.get("model") or model.get("name")
        except AttributeError:
            model_name = getattr(model, "model", None) or getattr(model, "name", None)

        if model_name:
            models.append(model_name)
    return models


def default_embedding_model(models):
    """Return the preferred default embedding model from discovered Ollama models."""
    preferred_models = ("embeddinggemma:latest",)

    for model in preferred_models:
        if model in models:
            return model

    if models:
        return models[0]

    return None


def get_models():
    """Return installed Ollama models that declare completion capability."""
    try:
        chat_client = create_client(st.session_state["ollama_endpoint"])
        models = []
        for model_name in _get_installed_model_names(chat_client):
            details = chat_client.show(model_name)
            capabilities = getattr(details, "capabilities", None) or details.get("capabilities", [])
            if "completion" in capabilities:
                models.append(model_name)

        st.session_state["ollama_models"] = models

        if len(models) > 0:
            logs.log.info("Ollama chat models loaded successfully")
        else:
            logs.log.warning("Ollama did not return any chat-capable models")

        return models
    except Exception as err:
        logs.log.error(f"Failed to retrieve Ollama model list: {err}")
        st.session_state["ollama_models"] = []
        return []


def get_embedding_models():
    """Return installed Ollama models that declare embedding capability."""
    try:
        chat_client = create_client(st.session_state["ollama_endpoint"])
        embedding_models = []

        for model_name in _get_installed_model_names(chat_client):
            details = chat_client.show(model_name)
            capabilities = getattr(details, "capabilities", None) or details.get("capabilities", [])
            if "embedding" in capabilities:
                embedding_models.append(model_name)

        st.session_state["ollama_embedding_models"] = embedding_models

        if embedding_models:
            if st.session_state.get("ollama_embedding_model") not in embedding_models:
                st.session_state["ollama_embedding_model"] = default_embedding_model(
                    embedding_models
                )
            logs.log.info("Ollama embedding models loaded successfully")
        else:
            logs.log.warning("Ollama did not return any embedding-capable models")

        return embedding_models
    except Exception as err:
        logs.log.error(f"Failed to retrieve Ollama embedding model list: {err}")
        st.session_state["ollama_embedding_models"] = []
        return []


###################################
#
# Create Ollama LLM instance
#
###################################


@st.cache_data(show_spinner=False)
def create_ollama_llm(model: str, base_url: str, system_prompt: str = None, request_timeout: int = 60) -> Ollama:
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
        # Settings.llm = Ollama(model=model, base_url=base_url, system_prompt=system_prompt, request_timeout=request_timeout)
        Settings.llm = Ollama(model=model, base_url=base_url, request_timeout=request_timeout)
        logs.log.info("Ollama LLM instance created successfully")
        return Settings.llm
    except Exception as e:
        logs.log.error(f"Error creating Ollama language model: {e}")
        raise


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
        llm = create_ollama_llm(
            st.session_state["selected_model"],
            st.session_state["ollama_endpoint"],
        )
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


def context_chat(prompt: str, query_engine: RetrieverQueryEngine):
    """
    Initiates a chat with context using the Llama-Index query_engine.

    Parameters:
        - prompt (str): The starting prompt for the conversation.
        - query_engine (RetrieverQueryEngine): The Llama-Index query engine to use for retrieving answers.

    Yields:
        - str: Successive chunks of conversation from the Llama-Index model with context.

    Raises:
        - Exception: If there is an error retrieving answers from the Llama-Index model.

    Notes:
        This function initiates a chat with context using the Llama-Index language model and index.

        It takes two parameters, `prompt` and `query_engine`, which should be the starting prompt for the conversation and the Llama-Index query engine to use for retrieving answers, respectively.

        The function returns an iterable yielding successive chunks of conversation from the Llama-Index index with context.

        If there is an error retrieving answers from the Llama-Index instance, the function raises an exception.

    Side Effects:
        - The chat conversation is generated and returned as successive chunks of text.
    """

    try:
        stream = query_engine.query(prompt)
        for text in stream.response_gen:
            # print(str(text), end="", flush=True)
            yield str(text)
    except Exception as err:
        logs.log.error(f"Ollama chat stream error: {err}")
        return
