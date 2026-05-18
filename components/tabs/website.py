import streamlit as st

import utils.rag_pipeline as rag
import utils.helpers as func
from components.ingestion_prerequisites import (
    ingestion_is_configured,
)

from urllib.parse import urlparse


def ensure_https(url):
    parsed = urlparse(url)

    if not bool(parsed.scheme):
        return f"https://{url}"

    return url


def add_website_from_input():
    new_website = st.session_state.get("new_website", "").strip()
    if new_website == "":
        return

    try:
        validated_website = func.validate_website_urls([ensure_https(new_website)])[0]
    except ValueError as err:
        st.session_state["website_input_error"] = str(err)
        return

    st.session_state["websites"].append(validated_website)
    st.session_state["websites"] = sorted(set(st.session_state["websites"]))
    st.session_state["new_website"] = ""
    st.session_state["website_input_error"] = None


def website():
    if not ingestion_is_configured():
        st.text_input(
            "Enter a Website",
            label_visibility="visible",
            disabled=True,
            key="new_website_disabled",
        )
        st.button("➕", disabled=True)
        return

    st.write("Enter a Website")
    col1, col2 = st.columns([1, 0.2])
    with col1:
        st.text_input(
            "Enter a Website",
            label_visibility="collapsed",
            key="new_website",
            on_change=add_website_from_input,
        )
    with col2:
        add_button = st.button("➕")

    if add_button:
        add_website_from_input()

    if st.session_state.get("website_input_error"):
        st.error(st.session_state["website_input_error"])

    if st.session_state["websites"] != []:
        st.markdown(f"<p>Website(s)</p>", unsafe_allow_html=True)
        for site in st.session_state["websites"]:
            st.caption(f"- {site}")
        st.write("")

        process_button = st.button("Process", key="process_website")

        if process_button:
            status_container = st.empty()
            completed_stages = []

            with st.spinner("Processing..."):
                try:
                    rag.render_pipeline_status(
                        status_container, completed_stages, "Fetching Websites"
                    )
                    documents = func.load_website_documents(st.session_state["websites"])
                    completed_stages.append("Websites Fetched")
                    rag.render_pipeline_status(status_container, completed_stages)
                except Exception as err:
                    st.exception(err)
                    st.stop()

                if len(documents) > 0:
                    # Initiate the RAG pipeline, providing documents to be saved on disk if necessary
                    error = rag.rag_pipeline(
                        documents=documents,
                        status_container=status_container,
                        initial_stages=completed_stages,
                        status_state_key="website_ingestion_stages",
                        documents_loaded_stage="Website Content Loaded",
                    )

                    # Display errors (if any) or proceed
                    if error is not None:
                        st.exception(error)
                    else:
                        st.write(
                            "Site processing completed. Let's chat! 😎"
                        )  # TODO: This should be a button.
