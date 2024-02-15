import ollama
import streamlit as st

def create_ollama_client(host: str):
    client = ollama.Client(host=host)
    return client

def ollama_chat(prompt: str):
    stream = ollama.chat(
        model = st.session_state.selected_model,
        messages = [
            {
                'role': 'user', 
                'content': prompt
            }
        ],
        stream=True,
    )
    return stream

def process_local_file(file: str):
    print(file)
    return

def process_github_repo(repo: str):
    print(repo) # Doesn't work?
    github_endpoint = "https://github.com/" + st.session_state.github_repo
    print(github_endpoint)
    return