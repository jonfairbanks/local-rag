import streamlit as st

from utils.ollama import chat, context_chat


def chatbox():
    if prompt := st.chat_input("How can I help?"):
        # Prevent submission if Ollama endpoint is not set
        if not st.session_state.ollama_endpoint:
            st.warning(
                "Please set an Ollama Endpoint under Settings before continuing."
            )
            st.stop()

        # Add the user input to messages state
        st.session_state["messages"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate llama-index stream with user input
        with st.chat_message("assistant"):
            with st.spinner("Processing..."):
                response = st.write_stream(
                    chat(
                        prompt=prompt,
                        model=st.session_state.selected_model,
                        base_url=st.session_state.ollama_endpoint,
                    )
                )

        # Add the final response to messages state
        st.session_state.messages.append({"role": "assistant", "content": response})
