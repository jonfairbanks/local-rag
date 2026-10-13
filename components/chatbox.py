import streamlit as st

from utils.ollama import context_chat


def _request_retry():
    st.session_state["chat_retry_requested"] = True


def _show_failure(failure, show_partial=True):
    if failure["partial"]:
        if show_partial:
            st.markdown(failure["partial"])
        st.caption("Incomplete Response")
    st.error("Response failed. Check Ollama and retry.")
    st.button("Retry", key="retry_chat", on_click=_request_retry)


def chatbox():
    prompt = st.chat_input("How can I help?")
    failure = st.session_state.get("chat_failure")
    retry = st.session_state.pop("chat_retry_requested", False) and failure is not None
    if not prompt and not retry:
        if failure:
            with st.chat_message("assistant"):
                _show_failure(failure)
        return

    if not st.session_state["query_engine"]:
        st.warning("Please confirm settings and upload files before proceeding.")
        return

    if prompt:
        st.session_state["messages"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
    else:
        prompt = failure["prompt"]
    st.session_state.pop("chat_failure", None)

    chunks = []

    def tracked_stream():
        for chunk in context_chat(prompt=prompt, query_engine=st.session_state["query_engine"]):
            chunks.append(chunk)
            yield chunk

    with st.chat_message("assistant"):
        try:
            with st.spinner("Processing..."):
                st.write_stream(tracked_stream())
            response = "".join(chunks)
            if not response.strip():
                raise ValueError("Ollama returned an empty response")
        except Exception:
            failure = {"prompt": prompt, "partial": "".join(chunks)}
            st.session_state["chat_failure"] = failure
            _show_failure(failure, show_partial=False)
            return

    st.session_state["messages"].append({"role": "assistant", "content": response})
