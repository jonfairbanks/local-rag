import streamlit as st

import utils.rag_pipeline as rag

from llama_index.readers.web import SimpleWebPageReader
from urllib.parse import urlparse


def ensure_https(url):
    parsed = urlparse(url)

    if not bool(parsed.scheme):
        return f"https://{url}"

    return url


def website():
    st.write("Enter a Website")
    col1, col2 = st.columns([1, 0.2])
    with col1:
        new_website = st.text_input("Enter a Website", label_visibility="collapsed")
    with col2:
        add_button = st.button("➕")

    # If the add button is clicked, append the new website to our list
    if add_button and new_website != "":
        st.session_state["websites"].append(ensure_https(new_website))
        st.session_state["websites"] = sorted(set(st.session_state["websites"]))

    if st.session_state["websites"] != []:
        st.markdown(f"<p>Website(s)</p>", unsafe_allow_html=True)
        for site in st.session_state["websites"]:
            st.caption(f"- {site}")
        st.write("")

        process_button = st.button("Process", key="process_website")

        if process_button:
            try:
                documents = SimpleWebPageReader(html_to_text=True).load_data(
                    st.session_state["websites"]
                )
            except Exception as err:
                st.exception(err)
                st.stop()

            if len(documents) > 0:
                with st.spinner("Processing..."):
                    # Initiate the RAG pipeline, providing documents to be saved on disk if necessary
                    error = rag.rag_pipeline(documents=documents)

                    # Display errors (if any) or proceed
                    if error is not None:
                        st.exception(error)
                    else:
                        st.write("Site processing completed. Let's chat! 😎") # TODO: This should be a button.
