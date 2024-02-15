import ollama
import streamlit as st

from typing import Dict, Generator

def ollama_generator(model_name: str, messages: Dict) -> Generator:
    stream = ollama.chat(
        model=model_name, 
        messages=messages, 
        stream=True
    )
    for chunk in stream:
        yield chunk['message']['content']

def chatbox():
    if prompt := st.chat_input("How can I help?"):
        # Prevent submission if Ollama endpoint is not set
        if not st.session_state.ollama_endpoint:
            st.warning("Please set an Ollama Endpoint under Settings before continuing.")
            st.stop()

        # Add the user input to messages state
        st.session_state['messages'].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate Ollama stream with user input 
        with st.chat_message("assistant"):
            response = st.write_stream(
                ollama_generator(
                    st.session_state.selected_model, 
                    st.session_state.messages
                )
            )
        
        # Add the final response to messages state
        st.session_state.messages.append(
            {"role": "assistant", "content": response})